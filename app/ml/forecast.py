"""Demand forecasting (doc 3.6, M3).

Primary: weekly seasonal-naive with trend (no heavy deps, <10ms).
Prophet adapter used automatically when `prophet` is installed AND history
is >= 60 days; moving-average fallback for sparse histories (<14 days).
Reorder: forecast over supplier lead time + safety stock - current stock.
"""
from datetime import date, timedelta

MODEL_SEASONAL = "seasonal-naive-trend"
MODEL_MA = "moving-average"
MODEL_PROPHET = "prophet"


def _weekday_avgs(history: list[tuple[date, int]]) -> list[float]:
    buckets: list[list[int]] = [[] for _ in range(7)]
    for d, q in history:
        buckets[d.weekday()].append(q)
    overall = sum(q for _, q in history) / max(len(history), 1)
    return [sum(b) / len(b) if b else overall for b in buckets]


def seasonal_forecast(history: list[tuple[date, int]], horizon: int = 14) -> list[float]:
    avgs = _weekday_avgs(history)
    last14 = [q for _, q in history[-14:]]
    prior14 = [q for _, q in history[-28:-14]] or last14
    trend = (sum(last14) / len(last14) - sum(prior14) / len(prior14)) / 14
    last_day = history[-1][0]
    return [round(max(avgs[(last_day + timedelta(days=i + 1)).weekday()] + trend * (i + 1), 0), 2)
            for i in range(horizon)]


def moving_average_forecast(history: list[tuple[date, int]], horizon: int = 14) -> list[float]:
    avg = round(sum(q for _, q in history) / max(len(history), 1), 2)
    return [avg] * horizon


def prophet_forecast(history: list[tuple[date, int]], horizon: int = 14) -> list[float] | None:
    """Prophet when installed; None -> caller falls back (M3 adapter)."""
    if len(history) < 60:
        return None
    try:
        import pandas as pd
        from prophet import Prophet
    except Exception:
        return None
    df = pd.DataFrame({"ds": [d for d, _ in history], "y": [q for _, q in history]})
    m = Prophet(weekly_seasonality=True, daily_seasonality=False,
                yearly_seasonality=False)
    m.fit(df)
    future = m.make_future_dataframe(periods=horizon)
    fc = m.predict(future).tail(horizon)["yhat"].clip(lower=0).round(2)
    return [float(v) for v in fc]


def forecast(history: list[tuple[date, int]], horizon: int = 14) -> tuple[list[float], str]:
    history = sorted(history)
    if len(history) >= 14:
        if (p := prophet_forecast(history, horizon)) is not None:
            return p, MODEL_PROPHET
        return seasonal_forecast(history, horizon), MODEL_SEASONAL
    if history:
        return moving_average_forecast(history, horizon), MODEL_MA
    return [0.0] * horizon, MODEL_MA


def mape(actual: list[float], predicted: list[float]) -> float:
    pairs = [(a, p) for a, p in zip(actual, predicted) if a > 0]
    if not pairs:
        return 0.0
    return round(sum(abs(a - p) / a for a, p in pairs) / len(pairs) * 100, 2)


def wape(actual: list[float], predicted: list[float]) -> float:
    denom = sum(actual)
    if not denom:
        return 0.0
    return round(sum(abs(a - p) for a, p in zip(actual, predicted)) / denom * 100, 2)


def holdout_mape(history: list[tuple[date, int]], horizon: int = 14) -> tuple[float, str]:
    """Rolling 14-day hold-out MAPE (M3 criterion #2)."""
    if len(history) < horizon + 7:
        return 0.0, MODEL_MA
    train, actual = history[:-horizon], [q for _, q in history[-horizon:]]
    pred, model = forecast(train, horizon)
    return mape(actual, pred), model


def days_until_stockout(available: int, forecast_14: list[float]) -> float | None:
    cum = 0.0
    for i, q in enumerate(forecast_14):
        cum += q
        if cum >= available:
            return round(i + (cum - available) / q if q else i, 1)
    return None


def reorder_qty(forecast_14: list[float], *, lead_days: int = 7,
                safety_days: int = 3, on_hand: int) -> int:
    need = sum(forecast_14[:lead_days])
    avg_daily = sum(forecast_14) / len(forecast_14)
    return max(int(round(need + avg_daily * safety_days - on_hand)), 0)
