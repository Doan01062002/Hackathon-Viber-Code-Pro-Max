"use client";

import { useMemo, useState, useEffect } from "react";
import { MetricGrid, SectionCard } from "@/features/rail-ui/components/Primitives";
import { buildCurveChart, useForecast } from "@/features/forecast";
import { buildSegmentHeatmap, useSegmentsLoad } from "@/features/segments";
import {
  gapSuggestions,
  odMatrix,
  rightRailCards,
} from "@/features/rail-ui/mockData";
import { seatApi } from "@/features/rail-ui/api/seatApi";
import type { GapSuggestionDto } from "@/features/rail-ui/api/seatApi";

const DEFAULT_TRIP_ID = 1;

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

// Fallback Mock Heatmap Rows (khi không có API)
const mockHeatmapRows = [
  { segment: "Hà Nội → Vinh", slots: [62, 68, 71, 76, 81, 79] },
  { segment: "Vinh → Đồng Hới", slots: [58, 64, 66, 72, 75, 74] },
  { segment: "Đồng Hới → Huế", slots: [73, 79, 82, 84, 88, 86] },
  { segment: "Huế → Đà Nẵng", slots: [88, 92, 95, 97, 99, 96] },
  { segment: "Đà Nẵng → Nha Trang", slots: [67, 71, 76, 79, 82, 80] },
  { segment: "Nha Trang → Sài Gòn", slots: [59, 63, 68, 70, 74, 72] },
];

const defaultCurvePoints = [
  { day: "D-30", actual: 14, forecast: 18 },
  { day: "D-20", actual: 28, forecast: 31 },
  { day: "D-10", actual: 48, forecast: 52 },
  { day: "D-7", actual: 58, forecast: 61 },
  { day: "D-3", actual: 74, forecast: 76 },
  { day: "D-1", actual: 88, forecast: 91 },
];

function buildMockPolyline(values: number[], max: number) {
  const width = 360;
  const height = 180;
  return values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - (value / max) * 140 - 12;
      return `${x},${y}`;
    })
    .join(" ");
}

export function DashboardScreen() {
  const forecast = useForecast(DEFAULT_TRIP_ID);
  const segments = useSegmentsLoad(DEFAULT_TRIP_ID);
  const [suggestions, setSuggestions] = useState<GapSuggestionDto[]>(gapSuggestions);

  useEffect(() => {
    async function loadGaps() {
      try {
        const data = await seatApi.getGapSuggestions(DEFAULT_TRIP_ID);
        if (data && data.length > 0) {
          setSuggestions(data);
        }
      } catch (err) {
        console.warn("Không tải được gợi ý khoảng trống, dùng mock:", err);
      }
    }
    loadGaps();
  }, []);

  const legs = useMemo(() => segments.data?.legs ?? [], [segments.data?.legs]);
  const heatmap = useMemo(
    () => buildSegmentHeatmap(legs),
    [legs],
  );

  const curveChart = useMemo(
    () => buildCurveChart(forecast.data?.booking_curve ?? []),
    [forecast.data],
  );

  // Tính toán Top Metrics động dựa trên dữ liệu chặng thực tế từ backend (nếu có)
  let avgLoad = 78;
  let bottleneckCount = 1;
  if (legs.length > 0) {
    const totalCapacity = legs.reduce((acc, leg) => acc + leg.capacity, 0);
    const totalRemaining = legs.reduce((acc, leg) => acc + leg.remaining, 0);
    avgLoad = Math.round(((totalCapacity - totalRemaining) / totalCapacity) * 100);
    bottleneckCount = legs.filter((leg) => leg.is_bottleneck).length;
  }

  const topMetrics = [
    {
      label: legs.length > 0 ? "Tải TB Thực tế" : "Tải trung bình",
      value: `${avgLoad}%`,
      detail: legs.length > 0 ? "Tính trên tất cả chặng" : "Tăng 4 điểm so với hôm qua",
      tone: "good",
    },
    { label: "Doanh thu dự kiến", value: "2,84 tỷ", detail: "Đạt 103% kế hoạch ngày", tone: "neutral" },
    {
      label: legs.length > 0 ? "Chặng Bottleneck" : "Chặng rủi ro",
      value: bottleneckCount.toString().padStart(2, "0"),
      detail: legs.length > 0 ? "Cần điều phối bid price" : "Huế → Đà Nẵng đang gần đầy",
      tone: bottleneckCount > 0 ? "danger" : "good",
    },
    { label: "Cảnh báo mở", value: "12", detail: "03 cảnh báo cần xử lý ngay", tone: "danger" },
  ];

  // Gom lỗi (nếu có) hiển thị dưới dạng banner thông báo
  const apiError = segments.error || forecast.error;

  return (
    <div className="page-stack">
      {apiError && (
        <div
          className="banner banner-warning"
          style={{
            backgroundColor: "#3a2a18",
            borderLeft: "4px solid #d97706",
            padding: "12px",
            borderRadius: "6px",
            color: "#f59e0b",
            fontSize: "14px",
            marginBottom: "8px",
          }}
        >
          ⚠️ <strong>Cập nhật thất bại:</strong> Không kết nối được API backend. Hệ thống đang chuyển sang chế độ hiển thị dữ liệu mô phỏng Demo.
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
                <strong>{legs.length > 0 ? `${avgLoad}%` : "97%"}</strong>
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
          subtitle="Tỉ lệ lấp đầy từng chặng theo loại chỗ; chặng nút cổ chai được đánh dấu để ưu tiên xử lý."
          actions={
            segments.status === "error" ? (
              <button className="btn btn-ghost" type="button" onClick={segments.refetch}>
                Thử lại
              </button>
            ) : (
              <button className="btn btn-ghost">Bộ lọc tàu và ngày</button>
            )
          }
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

          {segments.isLoading && <p className="curve-state">Đang tải dữ liệu tải chặng…</p>}

          {heatmap ? (
            <div className="table-wrap">
              <table className="data-table heatmap-table">
                <thead>
                  <tr>
                    <th>Chặng</th>
                    {heatmap.columns.map((col) => (
                      <th key={col.key}>{col.label}</th>
                    ))}
                    <th>Nút cổ chai</th>
                  </tr>
                </thead>
                <tbody>
                  {heatmap.rows.map((row) => (
                    <tr key={row.seq}>
                      <th scope="row">{row.label}</th>
                      {heatmap.columns.map((col) => {
                        const load = row.loads[col.key];
                        return (
                          <td
                            key={`${row.seq}-${col.key}`}
                            className={load === null ? undefined : heatClass(load)}
                          >
                            {load === null ? "—" : `${Math.round(load)}%`}
                          </td>
                        );
                      })}
                      <td>
                        {row.isBottleneck ? (
                          <span className="priority-badge severity-cao">Nút cổ chai</span>
                        ) : (
                          "—"
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            !segments.isLoading && (
              <div className="table-wrap">
                <table className="data-table heatmap-table">
                  <thead>
                    <tr>
                      <th>Chặng</th>
                      <th>06h</th>
                      <th>09h</th>
                      <th>12h</th>
                      <th>15h</th>
                      <th>18h</th>
                      <th>21h</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mockHeatmapRows.map((row) => (
                      <tr key={row.segment}>
                        <th scope="row">{row.segment}</th>
                        {row.slots.map((slot, index) => (
                          <td key={`${row.segment}-${index}`} className={heatClass(slot)}>
                            {slot}%
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          )}
        </SectionCard>

        <SectionCard
          title="Đường cong đặt vé"
          subtitle="Theo dõi thực tế so với dự báo trên cùng một biểu đồ để nhìn ra điểm lệch sớm."
          actions={
            forecast.status === "error" ? (
              <button className="btn btn-ghost" type="button" onClick={forecast.refetch}>
                Thử lại
              </button>
            ) : undefined
          }
        >
          {forecast.isLoading && <p className="curve-state">Đang tải dữ liệu dự báo…</p>}

          {curveChart ? (
            <>
              <div className="curve-chart">
                <div className="curve-axis-labels">
                  <span>100%</span>
                  <span>50%</span>
                  <span>0%</span>
                </div>

                <div className="curve-svg-wrap">
                  <svg aria-hidden="true" className="curve-svg" viewBox="0 0 360 180">
                    <path className="curve-grid-line" d="M0 28 H360" />
                    <path className="curve-grid-line" d="M0 88 H360" />
                    <path className="curve-grid-line" d="M0 148 H360" />
                    <polyline
                      className="curve-line curve-line-forecast"
                      fill="none"
                      points={curveChart.forecastPoints}
                    />
                    <polyline
                      className="curve-line curve-line-actual"
                      fill="none"
                      points={curveChart.actualPoints}
                    />
                  </svg>

                  <div className="curve-x-axis">
                    {curveChart.labels.map((label) => (
                      <span key={label}>{label}</span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="curve-summary">
                <span>
                  <i className="curve-dot curve-dot-actual" />
                  Thực tế bán vé (Chuẩn hóa)
                </span>
                <span>
                  <i className="curve-dot curve-dot-forecast" />
                  Dự báo nhu cầu (Chuẩn hóa)
                </span>
              </div>
            </>
          ) : (
            !forecast.isLoading && (
              <>
                <div className="curve-chart">
                  <div className="curve-axis-labels">
                    <span>100%</span>
                    <span>50%</span>
                    <span>0%</span>
                  </div>

                  <div className="curve-svg-wrap">
                    <svg aria-hidden="true" className="curve-svg" viewBox="0 0 360 180">
                      <path className="curve-grid-line" d="M0 28 H360" />
                      <path className="curve-grid-line" d="M0 88 H360" />
                      <path className="curve-grid-line" d="M0 148 H360" />
                      <polyline
                        className="curve-line curve-line-forecast"
                        fill="none"
                        points={buildMockPolyline(defaultCurvePoints.map(p => p.forecast), 100)}
                      />
                      <polyline
                        className="curve-line curve-line-actual"
                        fill="none"
                        points={buildMockPolyline(defaultCurvePoints.map(p => p.actual), 100)}
                      />
                    </svg>

                    <div className="curve-x-axis">
                      {defaultCurvePoints.map((point) => (
                        <span key={point.day}>{point.day}</span>
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
              </>
            )
          )}
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
            {suggestions.map((item) => (
              <article className="action-item" key={`${item.route}-${item.seatType}`}>
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
