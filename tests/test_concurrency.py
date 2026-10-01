"""M2 criterion #2: 50 parallel buyers, 10 units -> exactly 10 successes.

Exercises the REAL atomic reservation (app.services.inventory.reserve_stock)
against a file-backed SQLite DB in WAL mode with one session per thread —
the same code path checkout uses on Postgres (plus FOR UPDATE there).
"""
import os
import threading
import time

from sqlalchemy import create_engine, event
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.db.base import Base
from app.models.catalog import Inventory, Product
from app.services.inventory import InsufficientStock, reserve_stock


def _engine(path: str):
    eng = create_engine(f"sqlite:///{path}",
                        connect_args={"timeout": 30, "check_same_thread": False})

    @event.listens_for(eng, "connect")
    def _pragmas(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA journal_mode=WAL;")
        dbapi_conn.execute("PRAGMA busy_timeout=30000;")

    return eng


def test_50_buyers_10_units_no_oversell(tmp_path):
    path = str(tmp_path / "conc.db")
    eng = _engine(path)
    Base.metadata.create_all(bind=eng)
    s = sessionmaker(bind=eng)()
    p = Product(sku="CONC-10", name="Hot Item", price=9.99, search_text="hot")
    s.add(p)
    s.flush()
    s.add(Inventory(product_id=p.id, on_hand=10, reserved=0))
    s.commit()
    pid = p.id
    s.close()

    results = []

    def buyer(_):
        sess = sessionmaker(bind=eng)()
        ok = False
        for _ in range(100):  # retry on transient write locks, then give up
            try:
                reserve_stock(sess, product_id=pid, variant_id=None, qty=1)
                sess.commit()
                ok = True
                break
            except InsufficientStock:
                sess.rollback()
                break
            except OperationalError:
                sess.rollback()
                time.sleep(0.01)
        sess.close()
        results.append(ok)

    threads = [threading.Thread(target=buyer, args=(i,)) for i in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sum(results) == 10, f"expected exactly 10 successes, got {sum(results)}"
    check = sessionmaker(bind=eng)()
    inv = check.query(Inventory).filter(Inventory.product_id == pid).first()
    assert (inv.on_hand - inv.reserved) == 0 and inv.reserved == 10
    check.close()
    eng.dispose()
    for suffix in ("", "-wal", "-shm"):
        if os.path.exists(path + suffix):
            os.remove(path + suffix)
