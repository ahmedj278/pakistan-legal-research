import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi, test, expect } from "vitest";
import SearchPage from "./pages/SearchPage";
import * as apiClient from "./api/client";

const fakeResult = {
  chunk_id: "c.a._106_k_2024.pdf::chunk_3",
  text: "This is a long passage of judgment text that should be truncated in the excerpt preview because it exceeds the maximum display length configured in the ResultCard component for readability in the results list view. " + "Repeating filler text to definitely exceed two hundred eighty characters total length for this specific truncation test case. ".repeat(2),
  rerank_score: 4.2371,
  metadata: {
    case_title: "Petitioners vs Azhar Ali (C.A. 106-K/24)",
    court_name: "Supreme Court of Pakistan",
    court: "supreme_court",
    year: 2024,
    case_number: null,
    source_filename: "c.a._106_k_2024.pdf",
  },
};

function renderPage() {
  return render(
    <MemoryRouter>
      <SearchPage />
    </MemoryRouter>
  );
}

test("submits query and renders result card with correct fields", async () => {
  vi.spyOn(apiClient, "search").mockResolvedValue({ results: [fakeResult] });
  const user = userEvent.setup();
  renderPage();

  await user.type(screen.getByLabelText("Search query"), "PLD 2024 SC 1276");
  await user.click(screen.getByRole("button", { name: /search/i }));

  await waitFor(() => {
    expect(screen.getByText("Petitioners vs Azhar Ali (C.A. 106-K/24)")).toBeTruthy();
  });
  const card = document.querySelector(".result-card");
  expect(within(card).getByText("Supreme Court of Pakistan")).toBeTruthy();
  expect(screen.getByText("2024")).toBeTruthy();
  expect(screen.getByText("Case number not available")).toBeTruthy();
  expect(screen.getByText("Score: 4.24")).toBeTruthy();
  expect(screen.getByText(/View full judgment/)).toBeTruthy();
  console.log("Test 1 PASSED: search submits, result card shows correct fields incl. null-case_number fallback");
});

test("excerpt is truncated with ellipsis", async () => {
  vi.spyOn(apiClient, "search").mockResolvedValue({ results: [fakeResult] });
  const user = userEvent.setup();
  renderPage();
  await user.type(screen.getByLabelText("Search query"), "test");
  await user.click(screen.getByRole("button", { name: /search/i }));

  await waitFor(() => {
    const excerptEl = document.querySelector(".result-excerpt");
    expect(excerptEl.textContent.endsWith("…")).toBe(true);
    expect(excerptEl.textContent.length).toBeLessThan(fakeResult.text.length);
  });
  console.log("Test 2 PASSED: long excerpt truncated with ellipsis");
});

test("shows 'no results' message when search returns empty", async () => {
  vi.spyOn(apiClient, "search").mockResolvedValue({ results: [] });
  const user = userEvent.setup();
  renderPage();
  await user.type(screen.getByLabelText("Search query"), "nonexistent query xyz");
  await user.click(screen.getByRole("button", { name: /search/i }));

  await waitFor(() => {
    expect(screen.getByText(/No results found/)).toBeTruthy();
  });
  console.log("Test 3 PASSED: empty results shows correct message");
});

test("shows error message when search fails", async () => {
  vi.spyOn(apiClient, "search").mockRejectedValue(new Error("AI service unreachable"));
  const user = userEvent.setup();
  renderPage();
  await user.type(screen.getByLabelText("Search query"), "test");
  await user.click(screen.getByRole("button", { name: /search/i }));

  await waitFor(() => {
    expect(screen.getByText("AI service unreachable")).toBeTruthy();
  });
  console.log("Test 4 PASSED: error from API surfaces to user");
});

test("submit button disabled when query is empty", () => {
  renderPage();
  expect(screen.getByRole("button", { name: /search/i })).toHaveProperty("disabled", true);
  console.log("Test 5 PASSED: empty query disables submit");
});

test("filters are passed through to search() call", async () => {
  const searchSpy = vi.spyOn(apiClient, "search").mockResolvedValue({ results: [] });
  const user = userEvent.setup();
  renderPage();

  await user.type(screen.getByLabelText("Search query"), "khula");
  await user.selectOptions(screen.getByLabelText("Court filter"), "supreme_court");
  await user.type(screen.getByLabelText("Year filter"), "2024");
  await user.selectOptions(screen.getByLabelText("Document type filter"), "JUDGMENT");
  await user.click(screen.getByRole("button", { name: /search/i }));

  await waitFor(() => {
    expect(searchSpy).toHaveBeenCalledWith({
      query: "khula",
      court: "supreme_court",
      year: 2024,
      documentType: "JUDGMENT",
    });
  });
  console.log("Test 6 PASSED: filters correctly passed through to search() call");
});
