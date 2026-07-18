import { describe, expect, it } from "vitest";

// Translate seat type helper logic
function translateSeatType(type: string) {
  if (type === "ngoi_mem") return "Toa Ngồi mềm điều hòa";
  if (type === "giuong_nam_k6") return "Toa Giường nằm K6";
  return type;
}

// Business rule helper logic: check if Gộp chặng is available (at least 2 empty segments)
function checkCombineOpportunity(legs: { leg: string; status: "empty" | "sold" | "blocked" }[]) {
  const emptyCount = legs.filter(l => l.status === "empty").length;
  return emptyCount >= 2;
}

// Business rule helper logic: check if Tách chặng is available (at least 1 sold segment to split)
function checkSplitOpportunity(legs: { leg: string; status: "empty" | "sold" | "blocked" }[]) {
  return legs.some(l => l.status === "sold");
}

describe("Train Layout Screen Logic", () => {
  describe("translateSeatType", () => {
    it("should translate seat type correctly", () => {
      expect(translateSeatType("ngoi_mem")).toBe("Toa Ngồi mềm điều hòa");
      expect(translateSeatType("giuong_nam_k6")).toBe("Toa Giường nằm K6");
      expect(translateSeatType("other")).toBe("other");
    });
  });

  describe("checkCombineOpportunity", () => {
    it("should allow combining if there are at least two empty segments", () => {
      const legs: { leg: string; status: "empty" | "sold" | "blocked" }[] = [
        { leg: "HN → Vinh", status: "empty" },
        { leg: "Vinh → Huế", status: "empty" },
        { leg: "Huế → Đà Nẵng", status: "sold" }
      ];
      expect(checkCombineOpportunity(legs)).toBe(true);
    });

    it("should not allow combining if there is less than two empty segments", () => {
      const legs: { leg: string; status: "empty" | "sold" | "blocked" }[] = [
        { leg: "HN → Vinh", status: "sold" },
        { leg: "Vinh → Huế", status: "empty" },
        { leg: "Huế → Đà Nẵng", status: "sold" }
      ];
      expect(checkCombineOpportunity(legs)).toBe(false);
    });
  });

  describe("checkSplitOpportunity", () => {
    it("should allow splitting if at least one segment is sold", () => {
      const legs: { leg: string; status: "empty" | "sold" | "blocked" }[] = [
        { leg: "HN → Vinh", status: "sold" },
        { leg: "Vinh → Huế", status: "empty" },
        { leg: "Huế → Đà Nẵng", status: "empty" }
      ];
      expect(checkSplitOpportunity(legs)).toBe(true);
    });

    it("should not allow splitting if no segment is sold", () => {
      const legs: { leg: string; status: "empty" | "sold" | "blocked" }[] = [
        { leg: "HN → Vinh", status: "empty" },
        { leg: "Vinh → Huế", status: "empty" },
        { leg: "Huế → Đà Nẵng", status: "empty" }
      ];
      expect(checkSplitOpportunity(legs)).toBe(false);
    });
  });
});
