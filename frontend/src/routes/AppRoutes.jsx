import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import AppShell, { PageContainer } from "../components/layout/AppShell.jsx";
import { RequireAuth, RequireRole } from "../components/auth/guards.jsx";
import { Skeleton } from "../components/ui/feedback.jsx";
import { homeFor } from "../constants/roles.js";
import { useAuth } from "../contexts/AuthContext.jsx";

const L = (p) => lazy(p);
const Landing = L(() => import("../pages/public/Landing.jsx"));
const Login = L(() => import("../pages/public/Login.jsx"));
const Register = L(() => import("../pages/public/Register.jsx"));
const PasswordFlows = L(() => import("../pages/public/PasswordFlows.jsx"));
const Shop = L(() => import("../pages/customer/Shop.jsx"));
const Products = L(() => import("../pages/customer/Products.jsx"));
const ProductDetail = L(() => import("../pages/customer/ProductDetail.jsx"));
const Categories = L(() => import("../pages/customer/Categories.jsx"));
const Cart = L(() => import("../pages/customer/Cart.jsx"));
const Checkout = L(() => import("../pages/customer/Checkout.jsx"));
const Orders = L(() => import("../pages/customer/Orders.jsx"));
const OrderDetail = L(() => import("../pages/customer/OrderDetail.jsx"));
const Recommendations = L(() => import("../pages/customer/Recommendations.jsx"));
const Profile = L(() => import("../pages/customer/Profile.jsx"));
const Notifications = L(() => import("../pages/customer/Notifications.jsx"));
const ManageProducts = L(() => import("../pages/shared/ManageProducts.jsx"));
const InventoryPage = L(() => import("../pages/shared/InventoryPage.jsx"));
const OrdersConsole = L(() => import("../pages/shared/OrdersConsole.jsx"));
const AnalyticsPage = L(() => import("../pages/shared/AnalyticsPage.jsx"));
const ForecastPage = L(() => import("../pages/shared/ForecastPage.jsx"));
const SellerDashboard = L(() => import("../pages/seller/Dashboard.jsx"));
const SupportDashboard = L(() => import("../pages/support/Dashboard.jsx"));
const FraudReview = L(() => import("../pages/support/FraudReview.jsx"));
const Refunds = L(() => import("../pages/support/Refunds.jsx"));
const Customers = L(() => import("../pages/support/Customers.jsx"));
const AdminDashboard = L(() => import("../pages/admin/Dashboard.jsx"));
const Users = L(() => import("../pages/admin/Users.jsx"));
const Fraud = L(() => import("../pages/admin/Fraud.jsx"));
const FraudDetail = L(() => import("../pages/admin/FraudDetail.jsx"));
const AuditLogs = L(() => import("../pages/admin/AuditLogs.jsx"));
const System = L(() => import("../pages/admin/System.jsx"));
const Reports = L(() => import("../pages/admin/Reports.jsx"));
const Settings = L(() => import("../pages/admin/Settings.jsx"));

function Shell({ children }) {
  return (
    <AppShell>
      <PageContainer>{children}</PageContainer>
    </AppShell>
  );
}

function RoleHome() {
  const { role, isAuthed, loading } = useAuth();
  if (loading) return <Shell><Skeleton className="h-64" /></Shell>;
  return <Navigate to={isAuthed ? homeFor(role) : "/"} replace />;
}

const page = (el) => (
  <Suspense fallback={<PageContainer><Skeleton className="h-64" /></PageContainer>}>
    <Shell>{el}</Shell>
  </Suspense>
);

export default function AppRoutes() {
  return (
    <Suspense fallback={<div className="p-6">Loading…</div>}>
      <Routes>
        {/* public */}
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<PasswordFlows.ForgotPassword />} />
        <Route path="/reset-password" element={<PasswordFlows.ResetPassword />} />
        <Route path="/verify-email" element={<PasswordFlows.VerifyEmail />} />

        {/* post-login landing */}
        <Route element={<RequireAuth />}>
          <Route path="/home" element={<RoleHome />} />
        </Route>

        {/* customer + guest-browse storefront */}
        <Route path="/shop" element={page(<Shop />)} />
        <Route path="/products" element={page(<Products />)} />
        <Route path="/products/:id" element={page(<ProductDetail />)} />
        <Route path="/categories" element={page(<Categories />)} />

        <Route element={<RequireRole roles={["CUSTOMER"]} />}>
          <Route path="/cart" element={page(<Cart />)} />
          <Route path="/checkout" element={page(<Checkout />)} />
          <Route path="/orders" element={page(<Orders />)} />
          <Route path="/recommendations" element={page(<Recommendations />)} />
        </Route>

        <Route element={<RequireRole roles={["CUSTOMER", "SELLER", "SUPPORT", "ADMIN"]} />}>
          <Route path="/orders/:id" element={page(<OrderDetail />)} />
          <Route path="/profile" element={page(<Profile />)} />
          <Route path="/notifications" element={page(<Notifications />)} />
          <Route path="/settings" element={page(<Settings />)} />
        </Route>

        {/* seller */}
        <Route element={<RequireRole roles={["SELLER", "ADMIN"]} />}>
          <Route path="/seller/dashboard" element={page(<SellerDashboard />)} />
          <Route path="/seller/products" element={page(<ManageProducts scope="seller" />)} />
          <Route path="/seller/inventory" element={page(<InventoryPage scope="seller" />)} />
          <Route path="/seller/orders" element={page(
            <OrdersConsole variant="seller" title="Fulfilment" subtitle="Orders containing your products." />)} />
          <Route path="/seller/forecast" element={page(<ForecastPage />)} />
          <Route path="/seller/analytics" element={page(
            <AnalyticsPage title="Sales analytics" subtitle="Your products, your revenue." />)} />
        </Route>

        {/* support */}
        <Route element={<RequireRole roles={["SUPPORT", "ADMIN"]} />}>
          <Route path="/support/dashboard" element={page(<SupportDashboard />)} />
          <Route path="/support/orders" element={page(
            <OrdersConsole variant="support" title="All orders" subtitle="Search, fulfil and resolve." />)} />
          <Route path="/support/fraud-review" element={page(<FraudReview />)} />
          <Route path="/support/refunds" element={page(<Refunds />)} />
          <Route path="/support/customers" element={page(<Customers />)} />
        </Route>

        {/* admin */}
        <Route element={<RequireRole roles={["ADMIN"]} />}>
          <Route path="/admin/dashboard" element={page(<AdminDashboard />)} />
          <Route path="/admin/users" element={page(<Users />)} />
          <Route path="/admin/products" element={page(<ManageProducts scope="admin" />)} />
          <Route path="/admin/categories" element={page(<Categories />)} />
          <Route path="/admin/orders" element={page(
            <OrdersConsole variant="admin" title="All orders" subtitle="Platform-wide order operations." />)} />
          <Route path="/admin/inventory" element={page(<InventoryPage scope="admin" />)} />
          <Route path="/admin/payments" element={page(
            <OrdersConsole variant="admin" title="Payments" subtitle="Payments follow their orders — open one to refund." />)} />
          <Route path="/admin/refunds" element={page(<Refunds />)} />
          <Route path="/admin/fraud" element={page(<Fraud />)} />
          <Route path="/admin/fraud/:id" element={page(<FraudDetail />)} />
          <Route path="/admin/analytics" element={page(
            <AnalyticsPage title="Platform analytics" subtitle="Every seller, every category." />)} />
          <Route path="/admin/forecast" element={page(<ForecastPage admin title="Demand intelligence" />)} />
          <Route path="/admin/recommendations" element={page(<Recommendations />)} />
          <Route path="/admin/notifications" element={page(<Notifications />)} />
          <Route path="/admin/audit-logs" element={page(<AuditLogs />)} />
          <Route path="/admin/system" element={page(<System />)} />
          <Route path="/admin/reports" element={page(<Reports />)} />
          <Route path="/admin/settings" element={page(<Settings />)} />
        </Route>

        <Route path="*" element={page(
          <div className="glass mx-auto max-w-md p-10 text-center">
            <h1 className="font-display text-2xl font-bold">Page not found</h1>
            <p className="text-muted2 mt-2 text-sm">The link may be wrong or the page moved.</p>
          </div>
        )} />
      </Routes>
    </Suspense>
  );
}
