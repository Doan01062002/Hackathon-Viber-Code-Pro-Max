import { describe, expect, it } from "vitest";

import { buildCurveChart, buildPolyline } from "./transform";
import type { BookingCurvePointDto } from "./types";

function point(
  lead_days: number,
  cumulative_bookings: number,
  forecast_demand_point: number,
): BookingCurvePointDto {
  return { lead_days, cumulative_bookings, forecast_demand_point };
}

describe("buildPolyline", () => {
  it("map giá trị 0–100 thành toạ độ trên khung 360×180", () => {
    // value 100 → đỉnh (y=28); value 0 → gần đáy (y=168).
    expect(buildPolyline([0, 100])).toBe("0,168 360,28");
  });

  it("số điểm bằng số giá trị đầu vào", () => {
    const out = buildPolyline([10, 20, 30, 40]);
    expect(out.split(" ")).toHaveLength(4);
  });
});

describe("buildCurveChart", () => {
  it("trả null khi có ít hơn 2 điểm", () => {
    expect(buildCurveChart([])).toBeNull();
    expect(buildCurveChart([point(5, 10, 1)])).toBeNull();
  });

  it("sắp xếp theo lead_days giảm dần (xa ngày chạy ở trái)", () => {
    const chart = buildCurveChart([point(1, 80, 2), point(30, 10, 0.5), point(10, 40, 1)]);
    expect(chart?.labels[0]).toBe("D-30");
    expect(chart?.labels.at(-1)).toBe("D-1");
  });

  it("chuẩn hoá mỗi chuỗi theo max riêng → điểm cuối actual chạm đỉnh (100%→y=28)", () => {
    // actual tăng dần: max ở lead_days nhỏ nhất (điểm cuối bên phải).
    const chart = buildCurveChart([point(20, 0, 0.2), point(10, 50, 1), point(0, 100, 2.5)]);
    // Điểm cuối cùng của actualPoints phải ở y=28 (100% sau chuẩn hoá).
    const lastActual = chart!.actualPoints.split(" ").at(-1);
    expect(lastActual?.endsWith(",28")).toBe(true);
  });

  it("không chia cho 0 khi tất cả cumulative_bookings = 0", () => {
    const chart = buildCurveChart([point(20, 0, 0.2), point(10, 0, 0.5)]);
    expect(chart).not.toBeNull();
    // maxActual bị chặn ở 1 → mọi actual = 0% → y = 168.
    expect(chart!.actualPoints.split(" ").every((p) => p.endsWith(",168"))).toBe(true);
  });
});
