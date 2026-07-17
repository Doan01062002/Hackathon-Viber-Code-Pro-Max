"use client";

import { useState, useEffect } from "react";
import { MetricGrid, SectionCard } from "@/features/rail-ui/components/Primitives";
import { apiClient } from "@/lib/api/client";
import {
  bookingCurve as mockBookingCurve,
  gapSuggestions,
  heatmapRows as mockHeatmapRows,
  odMatrix,
  rightRailCards,
} from "@/features/rail-ui/mockData";

// Giao diện dữ liệu Heatmap từ API
interface LegHeatmapItem {
  segment_id: number;
  sequence_no: number;
  origin_station_code: string;
  destination_station_code: string;
  capacity: number;
  remaining: number;
  seat_type: string;
  bid_price: number;
  is_bottleneck: boolean;
}

interface LegHeatmapResponse {
  trip_id: number;
  legs: LegHeatmapItem[];
}

// Giao diện dữ liệu Booking Curve từ API
interface BookingCurvePoint {
  lead_days: number;
  cumulative_bookings: number;
  forecast_demand_point: number;
}

interface ForecastResponse {
  trip_id: number;
  service_date: string;
  forecasts: any[];
  booking_curve: BookingCurvePoint[];
}

function heatClass(value: number) {
  if (value >= 95) return "heat-critical";
  if (value >= 80) return "heat-hot";
  if (value >= 60) return "heat-warm";
  return "heat-cool";
}

function severityClass(value: string) {
  if (value === "Cao") return "severity-cao";
  if (value === "Trung bình") return "severity-trung-binh";
  return "severity-thap";
}

export function DashboardScreen() {
  const [legs, setLegs] = useState<LegHeatmapItem[]>([]);
  const [curve, setCurve] = useState<BookingCurvePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        // Lấy đồng thời heatmap chặng và booking curve dự báo
        const [heatmapRes, forecastRes] = await Promise.all([
          apiClient.get<LegHeatmapResponse>("/api/v1/analytics/legs-heatmap?trip_id=1"),
          apiClient.get<ForecastResponse>("/api/v1/forecast?trip_id=1")
        ]);
        
        setLegs(heatmapRes.legs);
        setCurve(forecastRes.booking_curve);
      } catch (err: any) {
        console.warn("Lỗi khi kết nối API backend, fallback sang dữ liệu mô phỏng:", err);
        setError("Không thể đồng bộ dữ liệu thời gian thực từ Backend server.");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const legsToRender = legs.length > 0 ? legs : null;
  const curveToRender = curve.length > 0 ? curve : mockBookingCurve;

  // Tính toán Top Metrics động dựa trên dữ liệu DB thực tế
  let avgLoad = 78;
  let bottleneckCount = 1;
  if (legs.length > 0) {
    const totalCapacity = legs.reduce((acc, leg) => acc + leg.capacity, 0);
    const totalRemaining = legs.reduce((acc, leg) => acc + leg.remaining, 0);
    avgLoad = Math.round(((totalCapacity - totalRemaining) / totalCapacity) * 100);
    bottleneckCount = legs.filter((leg) => leg.is_bottleneck).length;
  }

  const topMetrics = [
    { label: legsToRender ? "Tải TB Thực tế" : "Tải trung bình", value: `${avgLoad}%`, detail: legsToRender ? "Tính trên tất cả chặng" : "Tăng 4 điểm so với hôm qua", tone: "good" },
    { label: "Doanh thu dự kiến", value: "2,84 tỷ", detail: "Đạt 103% kế hoạch ngày", tone: "neutral" },
    { label: legsToRender ? "Chặng Bottleneck" : "Chặng rủi ro", value: bottleneckCount.toString().padStart(2, "0"), detail: legsToRender ? "Cần điều phối bid price" : "Huế → Đà Nẵng đang gần đầy", tone: bottleneckCount > 0 ? "danger" : "good" },
    { label: "Cảnh báo mở", value: "12", detail: "03 cảnh báo cần xử lý ngay", tone: "danger" },
  ];

  // Tìm điểm cực đại để vẽ trục y biểu đồ tự động
  const maxVal = Math.max(
    ...curveToRender.map((point) => ("cumulative_bookings" in point ? (point as any).cumulative_bookings : (point as any).actual)),
    ...curveToRender.map((point) => ("forecast_demand_point" in point ? (point as any).forecast_demand_point : (point as any).forecast)),
    100
  );

  function buildPolyline(values: number[]) {
    const width = 360;
    const height = 180;
    if (values.length === 0) return "";
    return values
      .map((value, index) => {
        const x = (index / (values.length - 1)) * width;
        const y = height - (value / maxVal) * 140 - 12;
        return `${x},${y}`;
      })
      .join(" ");
  }

  const actualPoints = buildPolyline(
    curveToRender.map((point) => ("cumulative_bookings" in point ? (point as any).cumulative_bookings : (point as any).actual))
  );
  const forecastPoints = buildPolyline(
    curveToRender.map((point) => ("forecast_demand_point" in point ? (point as any).forecast_demand_point : (point as any).forecast))
  );

  return (
    <div className="page-stack">
      {error && (
        <div className="banner banner-warning" style={{ backgroundColor: "#3a2a18", borderLeft: "4px solid #d97706", padding: "12px", borderRadius: "6px", color: "#f59e0b", fontSize: "14px", marginBottom: "8px" }}>
          ⚠️ <strong>Cảnh báo:</strong> {error} Hệ thống tự động chuyển sang chế độ mô phỏng dữ liệu Demo.
        </div>
      )}

      <section className="dashboard-toolbar">
        <div className="command-bar">
          <span className="command-icon" aria-hidden="true">
            ⌕
          </span>
          <input
            aria-label="Tìm tàu, ga hoặc chính sách"
            className="input command-input"
            defaultValue="Tìm tàu, ga, chính sách hoặc mã chạy cần theo dõi..."
          />
        </div>

        <div className="filters-row">
          <button className="filter-chip filter-chip-active" type="button">
            Toàn tuyến SE3
          </button>
          <button className="filter-chip" type="button">
            Khởi hành hôm nay
          </button>
          <button className="filter-chip" type="button">
            Chỉ xem chặng rủi ro cao
          </button>
        </div>
      </section>

      <section className="dashboard-lead">
        <article className="decision-card">
          <div className="decision-main">
            <div className="decision-heading">
              <span className="priority-badge">Ưu tiên xử lý ngay</span>
              <h2>Huế → Đà Nẵng đang là chặng cần can thiệp trước khi mở thêm quota ngắn.</h2>
              <p>
                Năng lực còn rất thấp trong 18 giờ tới, trong khi nhu cầu ngắn hạn tăng nhanh hơn
                dự báo. Nếu không điều chỉnh sớm, hệ thống có nguy cơ sold-out giả và bỏ lỡ doanh
                thu cho ga trung gian.
              </p>
            </div>

            <div className="decision-stat-grid">
              <article className="decision-stat">
                <span>Mức tải hiện tại</span>
                <strong>{legsToRender ? `${avgLoad}%` : "97%"}</strong>
                <small>Tăng 6% trong 2 giờ gần nhất</small>
              </article>
              <article className="decision-stat">
                <span>Dự báo tăng thêm</span>
                <strong>+8,2%</strong>
                <small>So với kịch bản giữ quota hiện tại</small>
              </article>
              <article className="decision-stat">
                <span>Tác động doanh thu</span>
                <strong>+190 triệu</strong>
                <small>Nếu mở bán lại đúng nhóm ghế</small>
              </article>
            </div>

            <ul className="recommendation-list">
              <li>Mở lại quota ngắn cho Vinh → Huế ở toa B2 và B3 trong 90 phút tới.</li>
              <li>Giữ bid price cao cho luồng dài đi Đà Nẵng để tránh mất doanh thu cơ hội.</li>
              <li>Chạy mô phỏng nhanh trước khi duyệt để kiểm tra ảnh hưởng lên ga trung gian.</li>
            </ul>

            <div className="hero-actions">
              <button className="btn btn-primary" type="button">
                Chạy mô phỏng khuyến nghị
              </button>
              <button className="btn btn-ghost" type="button">
                Mở màn hình báo giá
              </button>
            </div>
          </div>
        </article>

        <aside className="side-stack">
          <section className="side-mini-card">
            <div className="side-mini-head">
              <h3>Cảnh báo cần xử lý</h3>
              <span className="status-chip">03 nóng</span>
            </div>
            <div className="stack-list">
              {rightRailCards.quickAlerts.map((item) => (
                <article className="mini-alert" key={item.title}>
                  <span className={`severity-dot ${severityClass(item.severity)}`} aria-hidden="true" />
                  <div>
                    <strong>{item.title}</strong>
                    <p>{item.body}</p>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="side-mini-card">
            <div className="side-mini-head">
              <h3>Chế độ xem đã lưu</h3>
            </div>
            <div className="stack-list">
              {rightRailCards.savedViews.map((item) => (
                <article className="saved-view" key={item.title}>
                  <strong>{item.title}</strong>
                  <p>{item.meta}</p>
                </article>
              ))}
            </div>
          </section>

          <section className="side-mini-card">
            <div className="side-mini-head">
              <h3>Trạng thái mô phỏng</h3>
            </div>
            <div className="status-row">
              <strong>{rightRailCards.simulationStatus.value}</strong>
              <span>{rightRailCards.simulationStatus.body}</span>
            </div>
            <div className="progress-track">
              <span className="progress-fill" style={{ width: "68%" }} />
            </div>
          </section>
        </aside>
      </section>

      <MetricGrid items={topMetrics} />

      <div className="dashboard-grid">
        <SectionCard
          title="Heatmap tải chặng"
          subtitle="Nhìn nhanh chặng nào đang nóng lên theo từng khung giờ để quyết định mở hoặc giữ quota."
          actions={<button className="btn btn-ghost">Bộ lọc tàu và ngày</button>}
        >
          <div className="heatmap-legend">
            <span>
              <i className="legend-box heat-cool" />
              Dưới 60%
            </span>
            <span>
              <i className="legend-box heat-warm" />
              60 - 80%
            </span>
            <span>
              <i className="legend-box heat-hot" />
              80 - 95%
            </span>
            <span>
              <i className="legend-box heat-critical" />
              Trên 95%
            </span>
          </div>

          <div className="table-wrap">
            <table className="data-table heatmap-table">
              <thead>
                {legsToRender ? (
                  <tr>
                    <th>Chặng hành trình</th>
                    <th>Loại chỗ</th>
                    <th>Tồn kho ghế</th>
                    <th>Hệ số lấp đầy</th>
                    <th>Giá cơ hội (Bid)</th>
                    <th>Trạng thái</th>
                  </tr>
                ) : (
                  <tr>
                    <th>Chặng</th>
                    <th>06h</th>
                    <th>09h</th>
                    <th>12h</th>
                    <th>15h</th>
                    <th>18h</th>
                    <th>21h</th>
                  </tr>
                )}
              </thead>
              <tbody>
                {legsToRender ? (
                  legsToRender.map((leg) => {
                    const load = Math.round(((leg.capacity - leg.remaining) / leg.capacity) * 100);
                    return (
                      <tr key={leg.segment_id}>
                        <th scope="row" style={{ color: "#fff" }}>
                          {leg.origin_station_code} → {leg.destination_station_code}
                        </th>
                        <td>{leg.seat_type === "soft_seat" ? "Ngồi mềm" : "Giường nằm"}</td>
                        <td>{leg.remaining} / {leg.capacity}</td>
                        <td className={heatClass(load)} style={{ fontWeight: "bold" }}>
                          {load}%
                        </td>
                        <td style={{ color: "#10b981", fontWeight: "bold" }}>
                          {leg.bid_price.toLocaleString()} VND
                        </td>
                        <td>
                          {leg.is_bottleneck ? (
                            <span className="priority-badge severity-cao">Nút cổ chai</span>
                          ) : (
                            <span className="priority-badge severity-thap">Thường</span>
                          )}
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  mockHeatmapRows.map((row) => (
                    <tr key={row.segment}>
                      <th scope="row">{row.segment}</th>
                      {row.slots.map((slot, index) => (
                        <td key={`${row.segment}-${index}`} className={heatClass(slot)}>
                          {slot}%
                        </td>
                      ))}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </SectionCard>

        <SectionCard
          title="Đường cong đặt vé"
          subtitle="Theo dõi thực tế so với dự báo trên cùng một biểu đồ để nhìn ra điểm lệch sớm."
        >
          <div className="curve-chart">
            <div className="curve-axis-labels">
              <span>{Math.round(maxVal)}</span>
              <span>{Math.round(maxVal / 2)}</span>
              <span>0</span>
            </div>

            <div className="curve-svg-wrap">
              <svg aria-hidden="true" className="curve-svg" viewBox="0 0 360 180">
                <path className="curve-grid-line" d="M0 28 H360" />
                <path className="curve-grid-line" d="M0 88 H360" />
                <path className="curve-grid-line" d="M0 148 H360" />
                <polyline className="curve-line curve-line-forecast" fill="none" points={forecastPoints} />
                <polyline className="curve-line curve-line-actual" fill="none" points={actualPoints} />
              </svg>

              <div className="curve-x-axis">
                {curveToRender.map((point) => (
                  <span key={"lead_days" in point ? (point as any).lead_days : (point as any).day}>
                    {"lead_days" in point ? `D-${(point as any).lead_days}` : (point as any).day}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="curve-summary">
            <span>
              <i className="curve-dot curve-dot-actual" />
              Thực tế bán vé
            </span>
            <span>
              <i className="curve-dot curve-dot-forecast" />
              Dự báo nhu cầu
            </span>
          </div>
        </SectionCard>

        <SectionCard
          title="Ma trận OD"
          subtitle="Theo dõi số vé theo cặp ga để điều chỉnh bán vé, quota và giá theo đúng luồng nhu cầu."
        >
          <div className="table-wrap">
            <table className="data-table matrix-table">
              <thead>
                <tr>
                  {odMatrix[0].map((cell, index) => (
                    <th key={`od-head-${index}`}>{cell || "Ga đi / Ga đến"}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {odMatrix.slice(1).map((row) => (
                  <tr key={row[0]}>
                    <th scope="row">{row[0]}</th>
                    {row.slice(1).map((cell, index) => (
                      <td key={`${row[0]}-${index}`}>{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>

        <SectionCard
          title="Gợi ý lấp khoảng trống"
          subtitle="Các hành động có thể triển khai ngay để tận dụng tồn kho đang bị bỏ phí."
        >
          <div className="action-list">
            {gapSuggestions.map((item) => (
              <article className="action-item" key={item.route}>
                <div>
                  <strong>{item.route}</strong>
                  <p>{item.reason}</p>
                </div>
                <div className="action-meta">
                  <span>{item.seatType}</span>
                  <span>{item.benefit}</span>
                  <span className={`priority-text ${severityClass(item.priority)}`}>{item.priority}</span>
                </div>
                <button className="btn btn-ghost" type="button">
                  Xem chi tiết
                </button>
              </article>
            ))}
          </div>
        </SectionCard>
      </div>

      <SectionCard
        title="Trạng thái dữ liệu và điều phối"
        subtitle="Giữ phần cuối trang có điểm kết thúc rõ ràng thay vì dừng đột ngột giữa viewport."
      >
        <div className="summary-footer-grid">
          <article className="summary-footer-card">
            <span className="mini-label">Đồng bộ dữ liệu</span>
            <strong>{rightRailCards.updateStatus.title}</strong>
            <p>{rightRailCards.updateStatus.body}</p>
          </article>
          <article className="summary-footer-card">
            <span className="mini-label">Tín hiệu cuối ngày</span>
            <strong>Ưu tiên theo dõi sold-out giả và ga trung gian</strong>
            <p>Từ 18h đến 21h là khung thời gian cần nhìn lại quota ngắn và giá vé luồng dài.</p>
          </article>
        </div>
      </SectionCard>
    </div>
  );
}
