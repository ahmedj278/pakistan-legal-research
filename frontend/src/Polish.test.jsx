import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { vi, test, expect } from "vitest";
import SearchPage from "./pages/SearchPage";
import Layout from "./components/Layout";
import NotFoundPage from "./pages/NotFoundPage";
import * as apiClient from "./api/client";

test("shows pre-search empty-state hint before any search is made", () => {
  render(<MemoryRouter><SearchPage /></MemoryRouter>);
  expect(screen.getByText(/Enter a query above to search/)).toBeTruthy();
  console.log("Test 1 PASSED: pre-search empty state shown");
});

test("empty-state hint disappears once a search has been made", async () => {
  vi.spyOn(apiClient, "search").mockResolvedValue({ results: [] });
  const user = userEvent.setup();
  render(<MemoryRouter><SearchPage /></MemoryRouter>);

  await user.type(screen.getByLabelText("Search query"), "test");
  await user.click(screen.getByRole("button", { name: /search/i }));

  await waitFor(() => {
    expect(screen.getByText(/No results found/)).toBeTruthy();
  });
  expect(screen.queryByText(/Enter a query above to search/)).toBeNull();
  console.log("Test 2 PASSED: empty-state hint replaced by real no-results message after search");
});

test("stale results are cleared immediately when a new search starts (regression test for the real bug found)", async () => {
  let resolveSecondCall;
  const searchSpy = vi.spyOn(apiClient, "search");
  searchSpy.mockResolvedValueOnce({
    results: [{ chunk_id: "old1", text: "old result", rerank_score: 1, metadata: { case_title: "OLD CASE", source_filename: "old.pdf" } }],
  });

  const user = userEvent.setup();
  render(<MemoryRouter><SearchPage /></MemoryRouter>);

  await user.type(screen.getByLabelText("Search query"), "first query");
  await user.click(screen.getByRole("button", { name: /search/i }));

  await waitFor(() => {
    expect(screen.getByText("OLD CASE")).toBeTruthy();
  });

  // Second search — deliberately never resolves, so we can inspect
  // the DOM WHILE it's loading, before any new data arrives.
  searchSpy.mockReturnValueOnce(new Promise(() => {}));
  await user.clear(screen.getByLabelText("Search query"));
  await user.type(screen.getByLabelText("Search query"), "second query");
  await user.click(screen.getByRole("button", { name: /search/i }));

  // The OLD result must be gone already, even though the new search
  // hasn't resolved yet — this is exactly the bug that was fixed.
  expect(screen.queryByText("OLD CASE")).toBeNull();
  expect(screen.getByText(/Searching/)).toBeTruthy();
  console.log("Test 3 PASSED: stale results cleared immediately on new search (bug fix confirmed)");
});

test("spinner shows during search loading", async () => {
  vi.spyOn(apiClient, "search").mockReturnValue(new Promise(() => {})); // never resolves
  const user = userEvent.setup();
  render(<MemoryRouter><SearchPage /></MemoryRouter>);

  await user.type(screen.getByLabelText("Search query"), "test");
  await user.click(screen.getByRole("button", { name: /search/i }));

  expect(screen.getByText(/Searching/)).toBeTruthy();
  expect(document.querySelector(".spinner")).toBeTruthy();
  console.log("Test 4 PASSED: spinner visible during loading");
});

test("unmatched route renders NotFoundPage instead of blank screen", async () => {
  vi.spyOn(apiClient, "checkHealth").mockResolvedValue({ status: "ok" });
  render(
    <MemoryRouter initialEntries={["/this-route-does-not-exist"]}>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<SearchPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </MemoryRouter>
  );
  await waitFor(() => {
    expect(screen.getByText("Page not found")).toBeTruthy();
  });
  console.log("Test 5 PASSED: unmatched route renders NotFoundPage, not a blank screen");
});
