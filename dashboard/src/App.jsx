import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Overview from "./pages/Overview";
import Products from "./pages/Products";
import ProductDetail from "./pages/ProductDetail";
import Alerts from "./pages/Alerts";
import Pipeline from "./pages/Pipeline";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route path="/*" element={
            <ProtectedRoute>
              <Layout>
                <Routes>
                  <Route path="/"             element={<Overview />} />
                  <Route path="/products"     element={<Products />} />
                  <Route path="/products/:id" element={<ProductDetail />} />
                  <Route path="/alerts"       element={<Alerts />} />
                  <Route path="/pipeline"     element={<Pipeline />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          } />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}