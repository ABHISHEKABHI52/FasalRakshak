import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import HomePage from "./page";

describe("FasalRakshak landing shell", () => {
  it("renders the product name, tagline and core principle", () => {
    render(<HomePage />);
    expect(screen.getAllByText("FasalRakshak").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Scan. Predict. Protect.").length).toBeGreaterThan(0);
    expect(screen.getByText("Evidence > Guess")).toBeTruthy();
  });

  it("states the SIH problem statement context", () => {
    render(<HomePage />);
    expect(screen.getByText(/SIH26131/)).toBeTruthy();
  });

  it("does not claim unimplemented AI features are available", () => {
    render(<HomePage />);
    expect(screen.getByText(/not implemented yet/i)).toBeTruthy();
  });
});