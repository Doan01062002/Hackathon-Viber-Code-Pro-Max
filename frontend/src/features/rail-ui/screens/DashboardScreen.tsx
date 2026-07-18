"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api/client";
import { useQuery } from "@/lib/api/useQuery";
import { SegmentHeatmap } from "@/features/rail-ui/components/SegmentHeatmap";
import {
  bookingCurve as mockBookingCurve,
  gapSuggestions,
  heatmapRows as mockHeatmapRows,
  odMatrix,
  rightRailCards,
  alerts as mockAlerts,
} from "@/features/rail-ui/mockData";

// interfaces
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
  if (value >= 90) return "text-red-600 font-bold";
  if (value >= 75) return "text-orange-600 font-bold";
  return "text-primary font-bold";
}

// Reusable Interactive Sparkline Component
interface SparklineProps {
  data: number[];
  labels: string[];
  prefix?: string;
  suffix?: string;
  strokeColor: string;
}

function InteractiveSparkline({ data, labels, prefix = "", suffix = "", strokeColor }: SparklineProps) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const width = 240;
  const height = 40;
  const padding = 6;

  // Calculate points
  const points = data.map((val, idx) => {
    const x = padding + (idx / (data.length - 1)) * (width - padding * 2);
    const y = height - padding - ((val - min) / range) * (height - padding * 2);
    return { x, y, value: val, label: labels[idx] };
  });

  const pathD = points.map((p, idx) => `${idx === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

  return (
    <div className="relative w-full mt-2">
      {/* Min / Max indicators */}
      <div className="flex justify-between text-[9px] text-on-surface-variant/60 font-bold mb-1 font-mono">
        <span>Min: {prefix}{min.toLocaleString()}{suffix}</span>
        <span>Max: {prefix}{max.toLocaleString()}{suffix}</span>
      </div>

      <div className="h-10 relative">
        <svg
          className="w-full h-full overflow-visible"
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="none"
        >
          {/* Background gridlines */}
          <line x1="0" y1={padding} x2={width} y2={padding} stroke="#f1f5f9" strokeDasharray="2 2" strokeWidth="1" />
          <line x1="0" y1={height - padding} x2={width} y2={height - padding} stroke="#f1f5f9" strokeDasharray="2 2" strokeWidth="1" />

          {/* Line Path */}
          <path
            d={pathD}
            fill="none"
            stroke={strokeColor}
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2.5"
          />

          {/* Interaction Zones */}
          {points.map((p, idx) => (
            <g key={idx}>
              {hoverIndex === idx && (
                <circle
                  cx={p.x}
                  cy={p.y}
                  r="4"
                  fill={strokeColor}
                  stroke="#fff"
                  strokeWidth="1.5"
                />
              )}
              <rect
                x={idx === 0 ? 0 : points[idx - 1].x + (p.x - points[idx - 1].x) / 2}
                y="0"
                width={
                  idx === 0
                    ? points[1].x / 2
                    : idx === data.length - 1
                    ? width - (points[idx - 1].x + (p.x - points[idx - 1].x) / 2)
                    : (points[idx + 1].x - points[idx - 1].x) / 2
                }
                height={height}
                fill="transparent"
                className="cursor-pointer"
                onMouseEnter={(e) => {
                  setHoverIndex(idx);
                  const svgEl = e.currentTarget.ownerSVGElement;
                  if (svgEl) {
                    const rect = svgEl.getBoundingClientRect();
                    const pctX = p.x / width;
                    setTooltipPos({
                      x: pctX * rect.width,
                      y: (p.y / height) * rect.height - 28,
                    });
                  }
                }}
                onMouseMove={(e) => {
                  const svgEl = e.currentTarget.ownerSVGElement;
                  if (svgEl) {
                    const rect = svgEl.getBoundingClientRect();
                    const pctX = p.x / width;
                    setTooltipPos({
                      x: pctX * rect.width,
                      y: (p.y / height) * rect.height - 28,
                    });
                  }
                }}
                onMouseLeave={() => setHoverIndex(null)}
              />
            </g>
          ))}
        </svg>

        {/* Dynamic Tooltip */}
        {hoverIndex !== null && (
          <div
            style={{
              left: `${tooltipPos.x}px`,
              top: `${tooltipPos.y}px`,
              transform: "translateX(-50%)",
            }}
            className="absolute z-50 pointer-events-none bg-slate-950 text-white text-[9px] font-bold px-2 py-0.5 rounded shadow border border-slate-800 font-mono whitespace-nowrap"
          >
            {points[hoverIndex].label}: {prefix}{points[hoverIndex].value.toLocaleString()}{suffix}
          </div>
        )}
      </div>
    </div>
  );
}

export function DashboardScreen() {
  const router = useRouter();

  // Sử dụng custom hook useQuery theo yêu cầu FE-02.1
  const {
    data: heatmapData,
    loading: loadingHeatmap,
    error: errorHeatmap,
  } = useQuery<LegHeatmapResponse>("/api/v1/analytics/legs-heatmap?trip_id=1");

  const {
    data: forecastData,
    loading: loadingForecast,
    error: errorForecast,
  } = useQuery<ForecastResponse>("/api/v1/forecast?trip_id=1");

  const legs = heatmapData?.legs ?? [];
  const curve = forecastData?.booking_curve ?? [];

  const loading = loadingHeatmap || loadingForecast;
  const error = errorHeatmap || errorForecast;

  const legsToRender = legs.length > 0 ? legs : null;
  const curveToRender = curve.length > 0 ? curve : mockBookingCurve;

  // Tính toán metrics động
  let avgLoad = 84.2;
  let bottleneckCount = 1;
  if (legs.length > 0) {
    const totalCapacity = legs.reduce((acc, leg) => acc + leg.capacity, 0);
    const totalRemaining = legs.reduce((acc, leg) => acc + leg.remaining, 0);
    avgLoad = Math.round(((totalCapacity - totalRemaining) / totalCapacity) * 100);
    bottleneckCount = legs.filter((leg) => leg.is_bottleneck).length;
  }

  // Cấu hình biểu đồ
  const maxVal = Math.max(
    ...curveToRender.map((p) => ("cumulative_bookings" in p ? (p as any).cumulative_bookings : (p as any).actual) || 0),
    ...curveToRender.map((p) => ("forecast_demand_point" in p ? (p as any).forecast_demand_point : (p as any).forecast) || 0),
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
    curveToRender.map((p) => ("cumulative_bookings" in p ? (p as any).cumulative_bookings : (p as any).actual) || 0)
  );
  const forecastPoints = buildPolyline(
    curveToRender.map((p) => ("forecast_demand_point" in p ? (p as any).forecast_demand_point : (p as any).forecast) || 0)
  );

  // Sparkline data
  const sparkLabels = ["D-9", "D-8", "D-7", "D-6", "D-5", "D-4", "D-3", "D-2", "D-1", "Hôm nay"];
  const revenueTrend = [1.10, 1.12, 1.08, 1.15, 1.13, 1.18, 1.16, 1.22, 1.20, 1.24];
  const loadTrend = [86.5, 87.2, 86.0, 85.3, 85.5, 84.8, 85.0, 84.2, 84.5, avgLoad];
  const seatUseTrend = [0.85, 0.88, 0.86, 0.89, 0.87, 0.90, 0.88, 0.91, 0.90, 0.92];

  // Mapping legs to SegmentHeatmap slots format
  const mappedHeatmapRows = legs.length > 0
    ? legs.map(leg => {
        const load = Math.round(((leg.capacity - leg.remaining) / leg.capacity) * 100);
        return {
          segment: `${leg.origin_station_code} → ${leg.destination_station_code} (${leg.seat_type === "soft_seat" ? "Ngồi mềm" : "Giường nằm"})`,
          slots: [
            load,
            Math.max(10, Math.min(100, load - 12)),
            Math.max(10, Math.min(100, load + 8)),
            Math.max(10, Math.min(100, load - 5)),
            Math.max(10, Math.min(100, load + 15)),
            Math.max(10, Math.min(100, load - 8)),
          ]
        };
      })
    : mockHeatmapRows;

  return (
    <div className="space-y-6">
      {/* Header / Controls */}
      <div className="flex justify-end items-center mb-6">
        <div className="flex items-center space-x-3">
          <div className="bg-surface border border-outline-variant rounded-lg px-3 py-1.5 flex items-center space-x-2">
            <span className="material-symbols-outlined text-outline text-sm">calendar_today</span>
            <span className="text-xs font-semibold">Today, 17 July 2026</span>
          </div>
          <select
            className="bg-surface border border-outline-variant rounded-lg px-3 py-1.5 text-xs font-semibold focus:ring-primary focus:border-primary outline-none"
            defaultValue="Train ID: SE1, SE2, SE3"
          >
            <option>Train ID: SE1, SE2, SE3</option>
            <option>Train ID: SE4, SE5, SE6</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-lg text-yellow-700 text-xs font-semibold">
          ⚠️ Cảnh báo: {error} Hệ thống tự động chuyển sang chế độ mô phỏng dữ liệu Demo.
        </div>
      )}

      {/* Decision and Alert Stack Row */}
      <div className="grid grid-cols-12 gap-6">
        {/* Huế -> Đà Nẵng Decision Card (Left 8 cols) */}
        <div className="col-span-12 lg:col-span-8 bg-white border-l-4 border-primary border-y border-r border-outline-variant p-6 rounded-xl shadow-sm relative overflow-hidden flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="px-2 py-0.5 bg-red-100 text-red-700 text-[10px] font-bold rounded uppercase">
                Ưu tiên xử lý ngay
              </span>
              <span className="material-symbols-outlined text-primary scale-75">auto_awesome</span>
            </div>
            <h3 className="font-extrabold text-base text-on-surface mb-2">
              Huế → Đà Nẵng đang là chặng cần can thiệp trước khi mở thêm quota ngắn.
            </h3>
            <p className="text-xs text-on-surface-variant leading-relaxed mb-6 font-semibold">
              Năng lực còn rất thấp trong 18 giờ tới, trong khi nhu cầu ngắn hạn tăng nhanh hơn
              dự báo. Nếu không điều chỉnh sớm, hệ thống có nguy cơ sold-out giả và bỏ lỡ doanh
              thu cho ga trung gian.
            </p>

            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-surface-container-low p-3 rounded-lg border border-outline-variant/35">
                <p className="text-[10px] text-on-surface-variant font-bold uppercase">Mức tải hiện tại</p>
                <p className="text-lg font-black text-on-surface mt-1">{avgLoad}%</p>
                <p className="text-[9px] text-on-surface-variant mt-1 font-semibold">Tăng 6% trong 2h gần nhất</p>
              </div>
              <div className="bg-surface-container-low p-3 rounded-lg border border-outline-variant/35">
                <p className="text-[10px] text-on-surface-variant font-bold uppercase">Dự báo tăng thêm</p>
                <p className="text-lg font-black text-primary mt-1">+8.2%</p>
                <p className="text-[9px] text-on-surface-variant mt-1 font-semibold">So với giữ nguyên quota</p>
              </div>
              <div className="bg-surface-container-low p-3 rounded-lg border border-outline-variant/35">
                <p className="text-[10px] text-on-surface-variant font-bold uppercase">Tác động doanh thu</p>
                <p className="text-lg font-black text-green-600 mt-1">+190M</p>
                <p className="text-[9px] text-on-surface-variant mt-1 font-semibold">Nếu mở bán đúng nhóm ghế</p>
              </div>
            </div>

            <ul className="text-xs text-on-surface-variant space-y-1.5 list-disc list-inside font-semibold mb-6">
              <li>Mở lại quota ngắn cho Vinh → Huế ở toa B2 và B3 trong 90 phút tới.</li>
              <li>Giữ bid price cao cho luồng dài đi Đà Nẵng để tránh mất doanh thu cơ hội.</li>
              <li>Chạy mô phỏng nhanh trước khi duyệt để kiểm tra ảnh hưởng lên ga trung gian.</li>
            </ul>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => router.push("/simulation")}
              className="px-4 py-2 bg-primary text-on-primary font-bold rounded-lg hover:brightness-110 transition-all text-xs cursor-pointer"
            >
              Chạy mô phỏng khuyến nghị
            </button>
            <button
              onClick={() => router.push("/pricing")}
              className="px-4 py-2 border border-outline-variant text-on-surface hover:bg-slate-50 font-bold rounded-lg transition-all text-xs cursor-pointer"
            >
              Mở màn hình báo giá
            </button>
          </div>
        </div>

        {/* Side Stack (Right 4 cols) */}
        <aside className="col-span-12 lg:col-span-4 space-y-6">
          {/* Cảnh báo cần xử lý */}
          <div className="bg-white border border-outline-variant rounded-xl p-5 shadow-sm">
            <div className="flex justify-between items-center mb-4 border-b border-outline-variant/30 pb-2">
              <h4 className="font-bold text-xs text-on-surface uppercase tracking-wider">Cảnh báo cần xử lý</h4>
              <button
                onClick={() => router.push("/alerts")}
                className="px-2 py-0.5 bg-red-100 text-red-700 text-[9px] font-bold rounded hover:bg-red-200 transition-colors cursor-pointer"
              >
                Xem tất cả
              </button>
            </div>
            <div className="space-y-3">
              {rightRailCards.quickAlerts.map((item) => (
                <div
                  onClick={() => router.push("/alerts")}
                  className="flex items-start gap-2 text-xs cursor-pointer hover:bg-slate-50 p-1.5 rounded transition-colors"
                  key={item.title}
                >
                  <span className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${item.severity === "Cao" ? "bg-red-500" : "bg-orange-500"}`} />
                  <div>
                    <p className="font-bold text-on-surface">{item.title}</p>
                    <p className="text-[10px] text-on-surface-variant font-medium mt-0.5 leading-tight">{item.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Chế độ xem đã lưu */}
          <div className="bg-white border border-outline-variant rounded-xl p-5 shadow-sm">
            <h4 className="font-bold text-xs text-on-surface uppercase tracking-wider mb-3 border-b border-outline-variant/30 pb-2">
              Chế độ xem đã lưu
            </h4>
            <div className="space-y-2">
              {rightRailCards.savedViews.map((item) => (
                <div className="text-xs" key={item.title}>
                  <p className="font-bold text-on-surface hover:underline cursor-pointer">{item.title}</p>
                  <p className="text-[10px] text-on-surface-variant font-medium">{item.meta}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Trạng thái mô phỏng */}
          <div
            onClick={() => router.push("/simulation")}
            className="bg-white border border-outline-variant rounded-xl p-5 shadow-sm cursor-pointer hover:bg-slate-50 transition-colors"
          >
            <h4 className="font-bold text-xs text-on-surface uppercase tracking-wider mb-2 border-b border-outline-variant/30 pb-2">
              Trạng thái mô phỏng
            </h4>
            <div className="flex justify-between items-center text-xs mb-2">
              <span className="font-bold text-on-surface">{rightRailCards.simulationStatus.value}</span>
              <span className="text-[10px] text-on-surface-variant font-semibold">{rightRailCards.simulationStatus.body}</span>
            </div>
            <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
              <div className="h-full bg-primary" style={{ width: "68%" }} />
            </div>
          </div>
        </aside>
      </div>

      {/* 4 Key Bento Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
        {/* Metric Card 1 */}
        <div
          onClick={() => router.push("/pricing")}
          className="bg-surface border border-outline-variant p-5 rounded-xl hover:bg-surface-container-low transition-colors duration-200 cursor-pointer"
        >
          <div className="flex justify-between items-start mb-4">
            <span className="text-[10px] tracking-wider uppercase font-bold text-on-surface-variant">
              Tổng doanh thu
            </span>
            <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-[10px] font-bold">
              +12.4%
            </span>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-black text-on-surface">29.8 tỷ</span>
            <span className="text-on-surface-variant text-xs font-semibold">VNĐ</span>
          </div>
          <div className="mt-4">
            <InteractiveSparkline
              data={revenueTrend}
              labels={sparkLabels}
              suffix=" tỷ"
              strokeColor="#3525cd"
            />
          </div>
        </div>

        {/* Metric Card 2 */}
        <div
          onClick={() => router.push("/train")}
          className="bg-surface border border-outline-variant p-5 rounded-xl hover:bg-surface-container-low transition-colors duration-200 cursor-pointer"
        >
          <div className="flex justify-between items-start mb-4">
            <span className="text-[10px] tracking-wider uppercase font-bold text-on-surface-variant">
              Hệ số lấp đầy trung bình
            </span>
            <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded text-[10px] font-bold">
              -2.1%
            </span>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-black text-on-surface">{avgLoad}%</span>
          </div>
          <div className="mt-4">
            <InteractiveSparkline
              data={loadTrend}
              labels={sparkLabels}
              suffix="%"
              strokeColor="#ba1a1a"
            />
          </div>
        </div>

        {/* Metric Card 3 */}
        <div
          onClick={() => router.push("/simulation")}
          className="bg-surface border border-outline-variant p-5 rounded-xl hover:bg-surface-container-low transition-colors duration-200 cursor-pointer"
        >
          <div className="flex justify-between items-start mb-4">
            <span className="text-[10px] tracking-wider uppercase font-bold text-on-surface-variant">
              Hiệu suất Ghế-Km (ASK)
            </span>
            <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-[10px] font-bold">
              +5.8%
            </span>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-black text-on-surface">0.92</span>
            <span className="text-on-surface-variant text-xs font-semibold">Ghế-km</span>
          </div>
          <div className="mt-4">
            <InteractiveSparkline
              data={seatUseTrend}
              labels={sparkLabels}
              suffix=" Ghế-km"
              strokeColor="#3525cd"
            />
          </div>
        </div>

        {/* Metric Card 4 */}
        <div
          onClick={() => router.push("/simulation")}
          className="bg-surface-container border border-primary/20 p-5 rounded-xl ai-accent-border hover:bg-surface-container-high transition-colors duration-200 cursor-pointer"
        >
          <div className="flex justify-between items-start mb-4">
            <span className="text-[10px] tracking-wider uppercase text-primary font-bold">
              Nhu cầu chưa được đáp ứng
            </span>
            <span className="material-symbols-outlined text-primary scale-75">
              auto_awesome
            </span>
          </div>
          <div className="flex items-baseline space-x-2">
            <span className="text-2xl font-black text-primary">4,122</span>
            <span className="text-primary/70 text-xs font-semibold">Ghế</span>
          </div>
          <p className="mt-2 text-[11px] text-on-surface-variant leading-tight font-medium">
            AI đề xuất tăng năng lực chở khách cho tàu SE3 trên chặng HN-Vinh vào cuối tuần.
          </p>
        </div>
      </div>

      {/* Charts & Map Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Dynamic Booking Curve (develop SVG chart) */}
        <div className="lg:col-span-2 bg-white border border-outline-variant rounded-xl p-6">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h3 className="text-base font-bold text-on-surface">
                Đường cong đặt vé
              </h3>
              <p className="text-xs text-on-surface-variant font-medium mt-0.5">
                Theo dõi thực tế so với dự báo trên cùng một biểu đồ để nhìn ra điểm lệch sớm.
              </p>
            </div>
            <div className="flex items-center space-x-4 text-xs font-semibold">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-0.5 bg-primary" />
                <span className="text-on-surface-variant">Thực tế</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-0.5 bg-primary/45 border-t border-dashed" />
                <span className="text-on-surface-variant">Dự báo</span>
              </div>
            </div>
          </div>

          <div className="flex gap-4 items-stretch h-64">
            {/* Y axis labels */}
            <div className="flex flex-col justify-between py-2 text-[9px] text-on-surface-variant font-bold font-mono">
              <span>{Math.round(maxVal)}</span>
              <span>{Math.round(maxVal / 2)}</span>
              <span>0</span>
            </div>

            {/* SVG wrapper */}
            <div className="flex-grow border-l border-b border-outline-variant/60 relative">
              <svg className="w-full h-full overflow-visible" viewBox="0 0 360 180" preserveAspectRatio="none">
                {/* grid lines */}
                <line x1="0" y1="36" x2="360" y2="36" stroke="#e2e8f0" strokeDasharray="4 4" strokeWidth="1" />
                <line x1="0" y1="90" x2="360" y2="90" stroke="#e2e8f0" strokeDasharray="4 4" strokeWidth="1" />
                <line x1="0" y1="144" x2="360" y2="144" stroke="#e2e8f0" strokeDasharray="4 4" strokeWidth="1" />
                
                {/* paths */}
                <polyline fill="none" stroke="#3525cd" strokeWidth="2.5" points={actualPoints} />
                <polyline fill="none" stroke="#3525cd" strokeWidth="1.5" strokeDasharray="3 3" opacity="0.6" points={forecastPoints} />
              </svg>

              {/* X axis labels */}
              <div className="absolute -bottom-6 left-0 right-0 flex justify-between px-2 text-[9px] text-on-surface-variant font-mono font-bold">
                {curveToRender.map((point, idx) => (
                  <span key={idx}>
                    {"lead_days" in point ? `D-${(point as any).lead_days}` : (point as any).day}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Segment Load Factor heat levels */}
        <div className="bg-white border border-outline-variant rounded-xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-on-surface mb-6">
              Tải trọng theo chặng
            </h3>
            <div className="space-y-6">
              {/* Segment */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-on-surface-variant font-medium">HN → Vinh</span>
                  <span className="font-bold text-primary">92% Hệ số tải</span>
                </div>
                <div className="h-3 w-full bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-primary" style={{ width: "92%" }} />
                </div>
              </div>
              {/* Segment */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-on-surface-variant font-medium">Vinh → Hue</span>
                  <span className="font-bold text-primary">78% Hệ số tải</span>
                </div>
                <div className="h-3 w-full bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-primary" style={{ width: "78%" }} />
                </div>
              </div>
              {/* Segment */}
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-on-surface-variant font-medium">Hue → DN</span>
                  <span className="font-bold text-red-600">98% Hệ số tải</span>
                </div>
                <div className="h-3 w-full bg-surface-container rounded-full overflow-hidden">
                  <div className="h-full bg-red-500" style={{ width: "98%" }} />
                </div>
              </div>
            </div>
          </div>

          <div className="mt-8 p-4 bg-surface-container-low rounded-lg border border-dashed border-outline-variant">
            <p className="text-[11px] text-on-surface-variant italic leading-relaxed">
              Phát hiện nút cổ chai nghiêm trọng tại <span className="font-bold">Huế - Đà Nẵng</span>. Doanh thu cao hơn khả dụng thông qua việc phân bổ lại quota chặng.
            </p>
          </div>
        </div>
      </div>

      {/* Heatmap chặng chi tiết (SegmentHeatmap Grid) */}
      <SegmentHeatmap data={mappedHeatmapRows} />
    </div>
  );
}
