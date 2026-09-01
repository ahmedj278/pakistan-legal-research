import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi, test, expect } from "vitest";
import ResearchPage from "./pages/ResearchPage";
import * as apiClient from "./api/client";

const groundedResult = {
  answer: "A wife can claim maintenance after khula in certain circumstances [1].",
  grounded: true,
  citations: [
    {
      number: 1,
      chunk_id: "a.pdf::chunk_1",
      case_title: "Test v Case",
      court_name: "Supreme Court of Pakistan",
      case_number: null,
      year: 2022,
      source_filename: "a.pdf",
      text_snippet: "The relevant excerpt text.",
    },
  ],
};

const ungroundedResult = {
  answer: "The provided passages do not contain enough information to answer this.",
  grounded: false,
  citations: [],
  warning:
    "The model's answer did not cite any of the retrieved passages. This may mean it correctly identified insufficient evidence to answer, or it may have answered without proper grounding — review this answer manually before relying on it.",
};

function renderPage() {
  return render(
    <MemoryRouter>
      <ResearchPage />
    </MemoryRouter>
  );
}

test("submits question and renders grounded answer with citation card", async () => {
  vi.spyOn(apiClient, "ask").mockResolvedValue(groundedResult);
  const user = userEvent.setup();
  renderPage();

  await user.type(screen.getByLabelText("Research question"), "Can a wife get maintenance after khula?");
  await user.click(screen.getByRole("button", { name: /ask/i }));

  await waitFor(() => {
    expect(screen.getByText(groundedResult.answer)).toBeTruthy();
  });
  expect(screen.getByText("Test v Case")).toBeTruthy();
  expect(screen.getByText("The relevant excerpt text.")).toBeTruthy();
  expect(screen.queryByText(/did not cite/)).toBeNull();
  console.log("Test 1 PASSED: grounded answer renders with citation card, no warning shown");
});

test("shows grounding warning and NO citation cards for an ungrounded answer", async () => {
  vi.spyOn(apiClient, "ask").mockResolvedValue(ungroundedResult);
  const user = userEvent.setup();
  renderPage();

  await user.type(screen.getByLabelText("Research question"), "something out of scope");
  await user.click(screen.getByRole("button", { name: /ask/i }));

  await waitFor(() => {
    expect(screen.getByText(ungroundedResult.answer)).toBeTruthy();
  });
  expect(screen.getByText(/did not cite/)).toBeTruthy();
  expect(screen.queryByText("Sources")).toBeNull();
  console.log("Test 2 PASSED: ungrounded answer shows warning, no Sources section rendered");
});

test("shows error message when /ask fails", async () => {
  vi.spyOn(apiClient, "ask").mockRejectedValue(new Error("AI service unreachable"));
  const user = userEvent.setup();
  renderPage();

  await user.type(screen.getByLabelText("Research question"), "test");
  await user.click(screen.getByRole("button", { name: /ask/i }));

  await waitFor(() => {
    expect(screen.getByText("AI service unreachable")).toBeTruthy();
  });
  console.log("Test 3 PASSED: /ask failure surfaces error to user");
});

test("submit disabled when question is empty", () => {
  renderPage();
  expect(screen.getByRole("button", { name: /ask/i })).toHaveProperty("disabled", true);
  console.log("Test 4 PASSED: empty question disables submit");
});
