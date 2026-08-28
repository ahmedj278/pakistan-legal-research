import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import SearchPage from "./pages/SearchPage";
import ResearchPage from "./pages/ResearchPage";
import JudgmentPage from "./pages/JudgmentPage";

// App structure and routing (Session 7.1). Layout wraps every page
// with the shared nav bar + backend status badge (see
// components/Layout.jsx) via a nested route + <Outlet />, so each
// page component only needs to render its own content.
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<SearchPage />} />
          <Route path="/research" element={<ResearchPage />} />
          <Route path="/judgment/:filename" element={<JudgmentPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
