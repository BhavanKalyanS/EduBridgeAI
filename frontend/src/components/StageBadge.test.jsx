import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import StageBadge from "./StageBadge";

describe("StageBadge", () => {
  it("shows the language-support stage and its label", () => {
    render(<StageBadge stage={2} />);

    expect(screen.getByText("Stage 2")).toBeInTheDocument();
    expect(screen.getByText("Bilingual")).toBeInTheDocument();
  });

  it("clamps invalid stages to the supported range", () => {
    render(<StageBadge stage={9} />);

    expect(screen.getByText("Stage 4")).toBeInTheDocument();
    expect(screen.getByText("English", { selector: ".stage-name" })).toBeInTheDocument();
  });
});