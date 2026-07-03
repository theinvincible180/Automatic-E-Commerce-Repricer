
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Overview from "./pages/Overview";
import Products from "./pages/Products";
import ProductDetail from "./pages/ProductDetail";
import Alerts from "./pages/Alerts";
import Pipeline from "./pages/Pipeline";

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/"            element={<Overview />} />
          <Route path="/products"    element={<Products />} />
          <Route path="/products/:id" element={<ProductDetail />} />
          <Route path="/alerts"      element={<Alerts />} />
          <Route path="/pipeline"    element={<Pipeline />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}