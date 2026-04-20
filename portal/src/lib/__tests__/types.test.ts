import { describe, it, expect } from "vitest";
import { FRAMEWORKS } from "@/lib/types";

describe("FRAMEWORKS catalog", () => {
  it("exposes a CIS M365 entry", () => {
    expect(FRAMEWORKS.find((f) => f.id === "cis-m365")).toBeDefined();
  });

  it("exposes a SOC 2 entry", () => {
    expect(FRAMEWORKS.find((f) => f.id === "soc2")).toBeDefined();
  });

  it("labels coming-soon frameworks", () => {
    const iso = FRAMEWORKS.find((f) => f.id === "iso27001");
    expect(iso?.label.toLowerCase()).toContain("coming soon");
  });
});
