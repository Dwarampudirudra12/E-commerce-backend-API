# ER Diagram — M1 (22 tables, criterion: ≥12 via migrations)

```mermaid
erDiagram
  roles ||--o{ users : has
  users ||--o{ addresses : has
  users ||--o{ email_verification_tokens : has
  users ||--o{ password_reset_tokens : has
  users ||--o{ revoked_tokens : has
  users ||--o{ products : sells
  categories ||--o{ products : contains
  categories ||--o{ categories : parent
  products ||--o{ product_variants : has
  products ||--o{ product_images : has
  products ||--o{ inventory : stocks
  product_variants ||--o{ inventory : stocks
  users ||--o{ carts : owns
  carts ||--o{ cart_items : has
  products ||--o{ cart_items : in
  users ||--o{ orders : places
  orders ||--o{ order_items : has
  orders ||--o{ order_status_history : tracks
  orders ||--o{ payments : paid_by
  payments ||--o{ refunds : has
  users ||--o{ notifications : receives
  users ||--o{ audit_logs : acts
```

Tables: `roles, users, addresses, email_verification_tokens, password_reset_tokens,
revoked_tokens, categories, products, product_variants, product_images, inventory,
carts, cart_items, orders, order_items, order_status_history, payments, refunds,
discount_codes, notifications, audit_logs, ml_predictions` (22).

Key constraints: `users.email UNIQUE`, `products.sku UNIQUE`, `orders.order_number UNIQUE`,
`orders.idempotency_key UNIQUE`, `payments.gateway_ref UNIQUE`, `payments.webhook_event_id UNIQUE`.
Prod adds Postgres `tsvector + GIN` on products (M2 search).
