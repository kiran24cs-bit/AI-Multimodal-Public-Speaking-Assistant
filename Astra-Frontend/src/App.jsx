
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import UploadVideo from "./pages/UploadVideo.jsx";
import Analyzing from "./pages/Analyzing.jsx";
import AnalysisReport from "./pages/AnalysisReport.jsx";
import DetailedFinal from "./pages/DetailedFinal.jsx";
import Practice from "./pages/Practice.jsx";
import GenerateScript from "./pages/GenerateScript.jsx";
import SlidePrep from "./pages/SlidePrep";
import AppLayout from "./components/AppLayout.jsx";
import { DataProvider } from "./context/DataContext";
export default function App() {
  return (
    <DataProvider>
    <BrowserRouter>
      <Routes>
        {/* Login stays separate */}
        <Route path="/" element={<Login />} />

        {/* All other pages share the top nav and chatbot */}
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/upload" element={<UploadVideo />} />
          <Route path="/analyzing" element={<Analyzing />} />
          <Route path="/report" element={<AnalysisReport />} />
          <Route path="/detailed-final" element={<Analyzing />} />
          <Route path="/practice" element={<Practice />} />
          <Route path="/GenerateScript" element={<GenerateScript />} />
          <Route path="/slide-prep" element={<SlidePrep />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
    </DataProvider>
  );
}
