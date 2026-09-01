import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { vi, test, expect } from "vitest";
import Layout from "./components/Layout";
import SearchPage from "./pages/SearchPage";
import ResearchPage from "./pages/ResearchPage";
import JudgmentPage from "./pages/JudgmentPage";

vi.mock("./api/client", () => ({
  checkHealth: vi.fn(() => Promise.resolve({ status: "ok" })),
  search: vi.fn(() => Promise.resolve({ results: [] })),
  getDocument: vi.fn(() => Promise.resolve({
    filename: "c.a._106_k_2024.pdf",
    court: "supreme_court",
    metadata: { case_title: "Test Case" },
    text: "Test text",
  })),
}));

function renderAt(initialPath) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<SearchPage />} />
          <Route path="/research" element={<ResearchPage />} />
          <Route path="/judgment/:filename" element={<JudgmentPage />} />
        </Route>
      </Routes>
    </MemoryRouter>
  );
}

test("renders SearchPage at / (with real search form now)", () => {
  renderAt("/");
  expect(screen.getByText("Search Judgments")).toBeTruthy();
  expect(screen.getByLabelText("Search query")).toBeTruthy();
});

test("renders ResearchPage at /research", () => {
  renderAt("/research");
  expect(screen.getByText("Research Mode")).toBeTruthy();
});

test("renders JudgmentPage at /judgment/:filename with correct param", async () => {
  renderAt("/judgment/c.a._106_k_2024.pdf");
  await waitFor(() => {
    expect(screen.getByText("Test Case")).toBeTruthy();
  });
});
