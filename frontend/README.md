# E-Commerce AI — Frontend

Premium dark-glassmorphism React storefront + intelligence platform for the
E-Commerce Backend API.

## Run
```powershell
Copy-Item .env.example .env   # VITE_API_BASE_URL, default http://localhost:8000
npm install
npm run dev                   # http://localhost:5173 (proxies /api to :8000)
npm run build                 # production bundle in dist/
```

Backend must be up first (`docker compose up -d` in repo root + migrations +
`python scripts/seed.py`). Demo logins: `customer@ / seller@ / support@ /
admin@example.com` / `Password123!`.

## Architecture
- `src/api/` — Axios client (JWT refresh, 401 retry, error normalization) + one
  service module per domain (`authApi`, `ordersApi`, …). No secrets in source;
  base URL comes from `VITE_API_BASE_URL`.
- `src/contexts/` — `AuthContext` (user/tokens/role) + `PermissionContext`
  (backend-mirrored capability matrix). Frontend guards are UX only; the
  backend remains the security authority.
- `src/routes/AppRoutes.jsx` — lazy-loaded routes behind `RequireAuth` /
  `RequireRole` (4 roles + guest browsing). Route table mirrors
  `docs/FRONTEND_ROUTES.md` if present, else section 50 of the frontend spec.
- `src/components/{ui,layout,charts,commerce,analytics,auth}/` — glass design
  system, shell, charts, storefront and analytics widgets, route guards.
- `src/pages/{public,customer,seller,support,admin,shared}/` — role consoles.
- API gaps closed read-only on the backend for integration: `GET /audit-logs`,
  `GET /refunds`, `GET /payments`, `GET /orders/{id}/history`, and a guarded
  test-mode `POST /payments/by-order/{id}/confirm-test` (mock gateway,
  non-prod only).
