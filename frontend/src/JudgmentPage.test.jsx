import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { vi, test, expect } from "vitest";
import JudgmentPage from "./pages/JudgmentPage";
import * as apiClient from "./api/client";

const fakeDoc = {
  filename: "c.a._106_k_2024.pdf",
  court: "supreme_court",
  metadata: {
    case_title: "Petitioners vs Azhar Ali (C.A. 106-K/24)",
    court_name: "Supreme Court of Pakistan",
    case_number: null,
    year: null,
    judges: ["Justice Muhammad Ali Mazhar"],
    document_type: "JUDGMENT",
    citation: null,
    hearing_date: "01.01.2024",
    decision_date: null,
  },
  text: "Short judgment text.",
};

function renderPage({ initialEntries, filename = "c.a._106_k_2024.pdf" }) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path="/judgment/:filename" element={<JudgmentPage />} />
      </Routes>
    </MemoryRouter>
  );
}

test("renders metadata fields with correct null fallbacks", async () => {
  vi.spyOn(apiClient, "getDocument").mockResolvedValue(fakeDoc);
  renderPage({ initialEntries: ["/judgment/c.a._106_k_2024.pdf"] });

  await waitFor(() => {
    expect(screen.getByText("Petitioners vs Azhar Ali (C.A. 106-K/24)")).toBeTruthy();
  });
  expect(screen.getByText("Not available")).toBeTruthy(); // case number null
  expect(screen.getByText("Not yet assigned")).toBeTruthy(); // citation null
  expect(screen.getByText("Justice Muhammad Ali Mazhar")).toBeTruthy();
  expect(screen.getByText("01.01.2024")).toBeTruthy(); // hearing date shown
  expect(screen.queryByText("Decision date")).toBeNull(); // decision date omitted when null
  console.log("Test 1 PASSED: metadata renders correctly with proper null fallbacks");
});

test("shows relevant passage section ONLY when navigated with state", async () => {
  vi.spyOn(apiClient, "getDocument").mockResolvedValue(fakeDoc);
  renderPage({
    initialEntries: [
      { pathname: "/judgment/c.a._106_k_2024.pdf", state: { relevantText: "This exact chunk matched the search." } },
    ],
  });

  await waitFor(() => {
    expect(screen.getByText("Passage matching your search")).toBeTruthy();
  });
  expect(screen.getByText("This exact chunk matched the search.")).toBeTruthy();
  console.log("Test 2 PASSED: relevant passage shown when arriving via search result");
});

test("does NOT show relevant passage section on direct navigation (no state)", async () => {
  vi.spyOn(apiClient, "getDocument").mockResolvedValue(fakeDoc);
  renderPage({ initialEntries: ["/judgment/c.a._106_k_2024.pdf"] });

  await waitFor(() => {
    expect(screen.getByText("Petitioners vs Azhar Ali (C.A. 106-K/24)")).toBeTruthy();
  });
  expect(screen.queryByText("Passage matching your search")).toBeNull();
  console.log("Test 3 PASSED: no relevant-passage section on direct/bookmarked navigation");
});

test("show more/less toggle works for long text", async () => {
  const longText = "word ".repeat(1000); // well over 2000 chars
  vi.spyOn(apiClient, "getDocument").mockResolvedValue({ ...fakeDoc, text: longText });
  const user = userEvent.setup();
  renderPage({ initialEntries: ["/judgment/c.a._106_k_2024.pdf"] });

  await waitFor(() => {
    expect(screen.getByText("Show full text")).toBeTruthy();
  });

  const textEl = document.querySelector(".judgment-text");
  expect(textEl.textContent.length).toBeLessThan(longText.length);

  await user.click(screen.getByText("Show full text"));
  expect(textEl.textContent.length).toBeGreaterThan(2000);
  expect(screen.getByText("Show less")).toBeTruthy();
  console.log("Test 4 PASSED: show more/less toggle correctly expands and collapses long text");
});

test("short text has no show more/less toggle", async () => {
  vi.spyOn(apiClient, "getDocument").mockResolvedValue(fakeDoc); // short text
  renderPage({ initialEntries: ["/judgment/c.a._106_k_2024.pdf"] });

  await waitFor(() => {
    expect(screen.getByText("Short judgment text.")).toBeTruthy();
  });
  expect(screen.queryByText("Show full text")).toBeNull();
  console.log("Test 5 PASSED: no toggle shown for short text");
});

test("shows error state when document fetch fails (e.g. 404)", async () => {
  vi.spyOn(apiClient, "getDocument").mockRejectedValue(new Error("Document 'x.pdf' not found"));
  renderPage({ initialEntries: ["/judgment/x.pdf"] });

  await waitFor(() => {
    expect(screen.getByText("Document 'x.pdf' not found")).toBeTruthy();
  });
  expect(screen.getByText("← Back to search")).toBeTruthy();
  console.log("Test 6 PASSED: fetch error shown with recovery link, no crash");
});

test("court query param is passed through to getDocument()", async () => {
  const spy = vi.spyOn(apiClient, "getDocument").mockResolvedValue(fakeDoc);
  render(
    <MemoryRouter initialEntries={["/judgment/c.a._106_k_2024.pdf?court=supreme_court"]}>
      <Routes>
        <Route path="/judgment/:filename" element={<JudgmentPage />} />
      </Routes>
    </MemoryRouter>
  );

  await waitFor(() => {
    expect(spy).toHaveBeenCalledWith("c.a._106_k_2024.pdf", "supreme_court");
  });
  console.log("Test 7 PASSED: court query param correctly passed to getDocument()");
});
