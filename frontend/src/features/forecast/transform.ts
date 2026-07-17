/** Biến đổi dữ liệu forecast của backend thành dữ liệu vẽ biểu đồ. */

import type { BookingCurvePointDto } from "./types";

export type CurveChart = {
  actualPoints: string;
  forecastPoints: string;
  labels: string[];
};

/** Nối các giá trị 0–100 thành chuỗi points cho <polyline> trên khung 360×180. */
export function buildPolyline(values: number[]): string {
  const width = 360;
  const height = 180;
  return values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - (value / 100) * 140 - 12;
      return `${x},${y}`;
    })
    .join(" ");
}

/**
 * Biến booking_curve của backend thành dữ liệu vẽ trên khung 0–100%.
 *
 * `cumulative_bookings` (số vé) và `forecast_demand_point` đang ở hai thang rất
 * khác nhau, nên mỗi chuỗi được chuẩn hoá theo max riêng để so sánh *nhịp* đặt
 * vé thực tế với dự báo (không phải so trị tuyệt đối).
 */
export function buildCurveChart(points: BookingCurvePointDto[]): CurveChart | null {
  if (points.length < 2) return null;

  // lead_days giảm dần → xa ngày chạy ở trái, gần ngày chạy ở phải.
  const sorted = [...points].sort((a, b) => b.lead_days - a.lead_days);
  const maxActual = Math.max(1, ...sorted.map((p) => p.cumulative_bookings));
  const maxForecast = Math.max(1e-9, ...sorted.map((p) => p.forecast_demand_point));

  const actual = sorted.map((p) => (p.cumulative_bookings / maxActual) * 100);
  const forecast = sorted.map((p) => (p.forecast_demand_point / maxForecast) * 100);

  const labelStep = Math.ceil(sorted.length / 6);
  const labels = sorted
    .filter((_, index) => index % labelStep === 0 || index === sorted.length - 1)
    .map((p) => `D-${p.lead_days}`);

  return {
    actualPoints: buildPolyline(actual),
    forecastPoints: buildPolyline(forecast),
    labels,
  };
}
