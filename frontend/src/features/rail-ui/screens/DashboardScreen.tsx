"use client";

import React, { useMemo, useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { seatApi } from "@/features/rail-ui/api/seatApi";
import type { GapSuggestionDto } from "@/features/rail-ui/api/seatApi";
import { useForecast, buildCurveChart } from "@/features/forecast";
import { useSegmentsLoad, buildSegmentHeatmap } from "@/features/segments";
import {
  gapSuggestions as mockGapSuggestions,
  odMatrix,
  rightRailCards,
} from "@/features/rail-ui/mockData";

const DEFAULT_TRIP_ID = 1;

const DATE_MIN = "2024-01-01";
const DATE_MAX = "2025-12-30";

/** "2024-01-01" → "01/01/2024" */
function toDisplayDate(iso: string) {
  if (!iso) return "Chọn ngày";
  const [year, month, day] = iso.split("-");
  return `${day}/${month}/${year}`;
}

/** "01/01/2024" → "2024-01-01" (trả về null nếu không hợp lệ) */
function fromDisplayDate(display: string): string | null {
  const match = display.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!match) return null;
  const [, d, m, y] = match;
  const iso = `${y}-${m}-${d}`;
  if (iso < DATE_MIN || iso > DATE_MAX) return null;
  return iso;
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
        <span>Thấp nhất: {prefix}{min.toLocaleString()}{suffix}</span>
        <span>Cao nhất: {prefix}{max.toLocaleString()}{suffix}</span>
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
                  stroke="#opacity"
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

// Fallback Mock Heatmap Rows (khi không có API)
const mockHeatmapRows = [
  { segment: "Hà Nội → Vinh", slots: [62, 68, 71, 76, 81, 79] },
  { segment: "Vinh → Đồng Hới", slots: [58, 64, 66, 72, 75, 74] },
  { segment: "Đồng Hới → Huế", slots: [73, 79, 82, 84, 88, 86] },
  { segment: "Huế → Đà Nẵng", slots: [88, 92, 95, 97, 99, 96] },
  { segment: "Đà Nẵng → Nha Trang", slots: [67, 71, 76, 79, 82, 80] },
  { segment: "Nha Trang → Sài Gòn", slots: [59, 63, 68, 70, 74, 72] },
];

export function DashboardScreen() {
  const router = useRouter();

  // Custom Hooks từ develop branch
  const forecast = useForecast(DEFAULT_TRIP_ID);
  const segments = useSegmentsLoad(DEFAULT_TRIP_ID);
  const [suggestions, setSuggestions] = useState<GapSuggestionDto[]>(mockGapSuggestions);

  const [selectedDate, setSelectedDate] = useState(DATE_MIN);
  const [displayDate, setDisplayDate] = useState(toDisplayDate(DATE_MIN));
  const hiddenDateInputRef = useRef<HTMLInputElement>(null);


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
  const heatmap = useMemo(() => buildSegmentHeatmap(legs), [legs]);
  const curveChart = useMemo(() => buildCurveChart(forecast.data?.booking_curve ?? []), [forecast.data]);

  // Tính toán metrics động dựa trên dữ liệu chặng thực tế từ backend
  let avgLoad = 84.2;
  let bottleneckCount = 1;
  if (legs.length > 0) {
    const totalCapacity = legs.reduce((acc, leg) => acc + leg.capacity, 0);
    const totalRemaining = legs.reduce((acc, leg) => acc + leg.remaining, 0);
    avgLoad = Math.round(((totalCapacity - totalRemaining) / totalCapacity) * 100);
    bottleneckCount = legs.filter((leg) => leg.is_bottleneck).length;
  }

  // Gom lỗi hiển thị banner
  const apiError = segments.error || forecast.error;

  // Sparkline data
  // Nhãn cuối bám theo ngày đang chọn để không mâu thuẫn với bộ chọn ngày ở header.
  const lastSparkLabel = selectedDate ? toDisplayDate(selectedDate) : "01/01/2024";
  const sparkLabels = ["D-9", "D-8", "D-7", "D-6", "D-5", "D-4", "D-3", "D-2", "D-1", lastSparkLabel];
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
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-lg font-black text-on-surface">Bảng điều khiển tổng quan</h2>
          <p className="text-xs text-on-surface-variant font-medium mt-0.5">
            Giám sát thời gian thực hệ số tải, xu hướng đặt vé, doanh thu và cảnh báo thắt nút cổ chai.
          </p>
        </div>
        <div className="flex items-center space-x-3 mr-16">
          <div className="relative flex items-center w-36">
            <input
              type="text"
              aria-label="Chọn ngày xem dữ liệu (dd/mm/yyyy)"
              placeholder="dd/mm/yyyy"
              maxLength={10}
              value={displayDate}
              onChange={(event) => {
                const raw = event.target.value;
                setDisplayDate(raw);
                const iso = fromDisplayDate(raw);
                if (iso) setSelectedDate(iso);
              }}
              onBlur={() => {
                // Nếu gõ sai thì reset về giá trị hợp lệ cuối cùng
                const iso = fromDisplayDate(displayDate);
                if (!iso) {
                  setDisplayDate(toDisplayDate(selectedDate || DATE_MIN));
                }
              }}
              className="w-full rounded-lg border border-outline-variant bg-surface-container-low pl-2 pr-8 py-1.5 text-xs font-semibold outline-none focus:ring-1 focus:ring-primary text-on-surface shadow-sm"
            />
            <span 
              onClick={() => {
                if (hiddenDateInputRef.current && typeof hiddenDateInputRef.current.showPicker === "function") {
                  hiddenDateInputRef.current.showPicker();
                }
              }}
              className="absolute right-2 material-symbols-outlined text-outline text-sm cursor-pointer hover:text-primary transition-colors select-none"
            >
              calendar_today
            </span>
            {/* hidden native date input for calendar picker */}
            <input
              ref={hiddenDateInputRef}
              type="date"
              min={DATE_MIN}
              max={DATE_MAX}
              value={selectedDate}
              tabIndex={-1}
              onChange={(event) => {
                const value = event.target.value;
                if (!value) return;
                setSelectedDate(value);
                setDisplayDate(toDisplayDate(value));
              }}
              className="absolute pointer-events-none opacity-0"
              style={{ width: 0, height: 0 }}
            />
          </div>

        </div>
      </div>

      {apiError && (
        <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-lg text-yellow-700 text-xs font-semibold">
          ⚠️ Cảnh báo kết nối: Không thể đồng bộ từ Backend API. Đang hiển thị kịch bản Demo.
        </div>
      )}

      {/* SECTION 1: Priority + Alerts (moved to top) */}
      <div className="grid grid-cols-12 gap-6">
        {/* Left: AI priority recommendation (col-span-8) */}
        <div className="col-span-12 lg:col-span-8 bg-white border-l-4 border-primary border-y border-r border-outline-variant rounded-xl shadow-sm overflow-hidden flex flex-col justify-between">
          <div>
            <div className="bg-slate-50/60 px-6 py-4 flex items-center justify-between border-b border-outline-variant">
              <span className="inline-flex items-center gap-1.5 bg-red-50 text-red-700 text-[10px] font-black tracking-wider px-2.5 py-1 rounded-full">
                ● ƯU TIÊN XỬ LÝ NGAY
              </span>
              <span className="inline-flex items-center gap-1 text-primary text-xs font-black">
                <span className="material-symbols-outlined text-sm">auto_awesome</span> Gợi ý AI
              </span>
            </div>
            <div className="p-6">
              <h4 className="font-black text-lg text-on-surface leading-tight mb-2">
                Huế → Đà Nẵng là chặng cần can thiệp trước khi mở thêm quota ngắn
              </h4>
              <p className="text-xs text-on-surface-variant leading-relaxed mb-6 font-medium">
                Năng lực còn rất thấp trong 18 giờ tới, trong khi nhu cầu ngắn hạn tăng nhanh hơn dự báo. Nếu không điều chỉnh sớm, hệ thống có nguy cơ sold-out giá thấp và bỏ lỡ doanh thu cho ga trung gian.
              </p>

              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-slate-50 p-4 rounded-xl border border-outline-variant/35">
                  <p className="text-[10px] text-on-surface-variant font-bold uppercase tracking-wider">Mức tải hiện tại</p>
                  <p className="text-2xl font-black text-on-surface mt-1.5">{avgLoad}%</p>
                  <p className="text-[9.5px] text-green-600 mt-1 font-bold">▲ Tăng 6% trong 2h gần nhất</p>
                </div>
                <div className="bg-slate-50 p-4 rounded-xl border border-outline-variant/35">
                  <p className="text-[10px] text-on-surface-variant font-bold uppercase tracking-wider">Dự báo tăng thêm</p>
                  <p className="text-2xl font-black text-primary mt-1.5">+8.2%</p>
                  <p className="text-[9.5px] text-on-surface-variant/80 mt-1 font-medium">So với giữ nguyên quota</p>
                </div>
                <div className="bg-slate-50 p-4 rounded-xl border border-outline-variant/35">
                  <p className="text-[10px] text-on-surface-variant font-bold uppercase tracking-wider">Tác động doanh thu</p>
                  <p className="text-2xl font-black text-green-600 mt-1.5">+190 triệu</p>
                  <p className="text-[9.5px] text-on-surface-variant/80 mt-1 font-medium">Nếu mở bán đúng nhóm ghế</p>
                </div>
              </div>

              <ol className="space-y-3 pl-0 list-none">
                <li className="flex gap-3 text-xs text-on-surface-variant font-semibold items-start">
                  <span className="flex-shrink-0 w-[22px] h-[22px] rounded-lg bg-primary/15 text-primary text-xs font-black flex items-center justify-center mt-0.5">1</span>
                  <span>Mở lại quota ngắn cho <strong>Vinh → Huế</strong> ở toa B2 và B3 trong 90 phút tới.</span>
                </li>
                <li className="flex gap-3 text-xs text-on-surface-variant font-semibold items-start">
                  <span className="flex-shrink-0 w-[22px] h-[22px] rounded-lg bg-primary/15 text-primary text-xs font-black flex items-center justify-center mt-0.5">2</span>
                  <span>Giữ <strong>bid price</strong> cao cho luồng dài đi Đà Nẵng để tránh mất doanh thu cơ hội.</span>
                </li>
              </ol>
            </div>
          </div>

          <div className="px-6 py-4 bg-slate-50/30 border-t border-outline-variant flex gap-3">
            <button
              onClick={() => router.push("/quote")}
              className="px-5 py-2.5 bg-primary text-on-primary font-black rounded-lg hover:brightness-110 transition-all text-xs cursor-pointer"
            >
              Mở màn hình báo giá
            </button>
          </div>
        </div>

        {/* Right Rail (col-span-4) */}
        <aside className="col-span-12 lg:col-span-4 space-y-6">
          {/* Cảnh báo cần xử lý */}
          <div className="bg-white border border-outline-variant rounded-xl p-5 shadow-sm">
            <div className="flex justify-between items-center mb-4 border-b border-outline-variant/30 pb-2">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                <h4 className="font-black text-xs text-on-surface uppercase tracking-wider">Cảnh báo cần xử lý</h4>
              </div>
              <button
                onClick={() => router.push("/alerts")}
                className="text-[11px] font-bold text-primary hover:underline cursor-pointer"
              >
                Xem tất cả
              </button>
            </div>
            <div className="space-y-3">
              {rightRailCards.quickAlerts.map((item) => (
                <div
                  onClick={() => router.push("/alerts")}
                  className="flex items-start gap-2.5 text-xs cursor-pointer hover:bg-slate-50 p-2 rounded-lg transition-colors"
                  key={item.title}
                >
                  <span className={`w-2.5 h-2.5 rounded-full mt-1 flex-shrink-0 ${item.severity === "Cao" ? "bg-red-500" : "bg-amber-500"}`} />
                  <div>
                    <p className="font-extrabold text-on-surface leading-snug">{item.title}</p>
                    <p className="text-[10px] text-on-surface-variant font-semibold mt-0.5 leading-snug">{item.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Bộ lọc đã lưu */}
          <div className="bg-white border border-outline-variant rounded-xl p-5 shadow-sm">
            <div className="flex items-center gap-1.5 mb-3 border-b border-outline-variant/30 pb-2">
              <span className="w-2 h-2 rounded-full bg-primary" />
              <h4 className="font-black text-xs text-on-surface uppercase tracking-wider">Bộ lọc đã lưu</h4>
            </div>
            <div className="space-y-3">
              {rightRailCards.savedViews.map((item) => (
                <div className="text-xs p-1 rounded hover:bg-slate-50 transition-colors cursor-pointer" key={item.title}>
                  <p className="font-extrabold text-on-surface">{item.title}</p>
                  <p className="text-[10px] text-on-surface-variant font-semibold leading-tight mt-0.5">{item.meta}</p>
                </div>
              ))}
            </div>
          </div>
        </aside>
      </div>

      {/* SECTION 2: KPI overview (Bento grid) */}
      <div className="space-y-3 mt-6">
        <div className="flex items-center gap-2 mb-3">
          <span className="w-2 h-2 rounded bg-primary" />
          <h3 className="text-xs font-black text-on-surface uppercase tracking-wider">Chỉ số sức khoẻ hôm nay</h3>
          <span className="text-xs text-on-surface-variant/80 font-medium">so với hôm qua</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* KPI Card 1 */}
          <div
            onClick={() => router.push("/quote")}
            className="bg-white border border-outline-variant p-5 rounded-xl hover:bg-slate-50/50 transition-all duration-200 cursor-pointer shadow-sm"
          >
            <div className="flex justify-between items-start mb-4">
              <span className="text-[10.5px] tracking-wider uppercase font-extrabold text-on-surface-variant">
                Tổng doanh thu
              </span>
              <span className="px-2 py-0.5 bg-green-50 text-green-700 rounded-full text-[10px] font-black">
                ▲ 12.4%
              </span>
            </div>
            <div className="flex items-baseline space-x-1.5">
              <span className="text-2xl font-black text-on-surface">4.82 tỷ</span>
              <span className="text-on-surface-variant text-xs font-bold">VNĐ</span>
            </div>
            <div className="mt-4 border-t border-slate-50 pt-3">
              <InteractiveSparkline
                data={revenueTrend}
                labels={sparkLabels}
                suffix=" tỷ"
                strokeColor="#3525cd"
              />
            </div>
          </div>

          {/* KPI Card 2 */}
          <div
            onClick={() => router.push("/train-layout")}
            className="bg-white border border-outline-variant p-5 rounded-xl hover:bg-slate-50/50 transition-all duration-200 cursor-pointer shadow-sm"
          >
            <div className="flex justify-between items-start mb-4">
              <span className="text-[10.5px] tracking-wider uppercase font-extrabold text-on-surface-variant">
                Hệ số lấp đầy TB
              </span>
              <span className="px-2 py-0.5 bg-red-50 text-red-700 rounded-full text-[10px] font-black">
                ▼ 2.1%
              </span>
            </div>
            <div className="flex items-baseline space-x-1.5">
              <span className="text-2xl font-black text-on-surface">{avgLoad}%</span>
            </div>
            <div className="mt-4 border-t border-slate-50 pt-3">
              <InteractiveSparkline
                data={loadTrend}
                labels={sparkLabels}
                suffix="%"
                strokeColor="#ba1a1a"
              />
            </div>
          </div>

          {/* KPI Card 3 */}
          <div
            onClick={() => router.push("/train-layout")}
            className="bg-white border border-outline-variant p-5 rounded-xl hover:bg-slate-50/50 transition-all duration-200 cursor-pointer shadow-sm"
          >
            <div className="flex justify-between items-start mb-4">
              <span className="text-[10.5px] tracking-wider uppercase font-extrabold text-on-surface-variant">
                Hiệu suất ghế-km (ASK)
              </span>
              <span className="px-2 py-0.5 bg-green-50 text-green-700 rounded-full text-[10px] font-black">
                ▲ 5.8%
              </span>
            </div>
            <div className="flex items-baseline space-x-1.5">
              <span className="text-2xl font-black text-on-surface">91.3%</span>
            </div>
            <div className="mt-4 border-t border-slate-50 pt-3">
              <InteractiveSparkline
                data={seatUseTrend}
                labels={sparkLabels}
                suffix="%"
                strokeColor="#3525cd"
              />
            </div>
          </div>

          {/* KPI Card 4 */}
          <div
            onClick={() => router.push("/quote")}
            className="bg-white border border-primary/20 p-5 rounded-xl hover:bg-primary/5 transition-all duration-200 cursor-pointer shadow-sm"
          >
            <div className="flex justify-between items-start mb-4">
              <span className="text-[10.5px] tracking-wider uppercase text-primary font-black">
                Nhu cầu chưa đáp ứng
              </span>
              <span className="px-2 py-0.5 bg-primary/10 text-primary rounded-full text-[10px] font-black">
                ✦ Cần mở bán
              </span>
            </div>
            <div className="flex items-baseline space-x-1.5">
              <span className="text-2xl font-black text-primary">1,240</span>
              <span className="text-primary/70 text-xs font-bold">chỗ</span>
            </div>
            <p className="mt-4 text-[11px] text-on-surface-variant leading-relaxed font-semibold border-t border-primary/5 pt-3">
              Cơ cấu năng lực chưa tối ưu, AI đề xuất tăng quota các chặng ngắn trọng điểm.
            </p>
          </div>
        </div>
      </div>

      {/* SECTION 3: Analysis (booking curve + segment load) */}
      <div className="space-y-3 mt-6">
        <div className="flex items-center gap-2 mb-3">
          <span className="w-2 h-2 rounded bg-primary" />
          <h3 className="text-xs font-black text-on-surface uppercase tracking-wider">Phân tích nhu cầu &amp; tải chặng</h3>
          <span className="text-xs text-on-surface-variant/80 font-medium">vì sao cần can thiệp</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Booking Curve Panel (col-span-2) */}
          <div className="lg:col-span-2 bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h4 className="text-sm font-black text-on-surface">Đường cong đặt vé</h4>
                <p className="text-xs text-on-surface-variant font-semibold mt-0.5">
                  Theo dõi thực tế bán so với dự báo trên cùng một biểu đồ để nhìn ra điểm lệch sớm.
                </p>
              </div>
              <div className="flex items-center space-x-4 text-[11px] font-bold">
                <div className="flex items-center space-x-1.5">
                  <div className="w-3.5 h-0.75 bg-primary rounded" />
                  <span className="text-on-surface-variant">Thực tế bán vé</span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <div className="w-3.5 h-0.75 bg-[#ba1a1a] border-t border-dashed" />
                  <span className="text-on-surface-variant">Dự báo nhu cầu</span>
                </div>
              </div>
            </div>

            {forecast.isLoading ? (
              <p className="text-center text-xs text-on-surface-variant py-12 font-semibold">Đang tải dữ liệu dự báo...</p>
            ) : curveChart ? (
              <div className="flex gap-4 items-stretch h-64">
                {/* Y axis labels */}
                <div className="flex flex-col justify-between py-2 text-[9px] text-on-surface-variant font-bold font-mono">
                  <span>100%</span>
                  <span>50%</span>
                  <span>0%</span>
                </div>

                {/* SVG wrapper */}
                <div className="flex-grow border-l border-b border-outline-variant/60 relative">
                  <svg className="w-full h-full overflow-visible" viewBox="0 0 360 180" preserveAspectRatio="none">
                    <path className="curve-grid-line" d="M0 28 H360" stroke="#f1f5f9" strokeDasharray="4 4" />
                    <path className="curve-grid-line" d="M0 88 H360" stroke="#f1f5f9" strokeDasharray="4 4" />
                    <path className="curve-grid-line" d="M0 148 H360" stroke="#f1f5f9" strokeDasharray="4 4" />
                    <polyline fill="none" stroke="#ba1a1a" strokeWidth="2" strokeDasharray="4 3" opacity="0.75" points={curveChart.forecastPoints} />
                    <polyline fill="none" stroke="#3525cd" strokeWidth="3" points={curveChart.actualPoints} />
                  </svg>

                  {/* X axis labels */}
                  <div className="absolute -bottom-6 left-0 right-0 flex justify-between px-2 text-[9px] text-on-surface-variant font-mono font-bold">
                    {curveChart.labels.map((label) => (
                      <span key={label}>{label}</span>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-center text-xs text-on-surface-variant py-12 font-semibold">Không có dữ liệu biểu đồ.</p>
            )}
          </div>

          {/* Segment Load Factor Panel */}
          <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm flex flex-col justify-between">
            <div>
              <h4 className="text-sm font-black text-on-surface mb-1">
                Hệ số tải chặng Thống Nhất
              </h4>
              <p className="text-xs text-on-surface-variant mb-6 font-semibold">Theo dõi hệ số lấp đầy ba phân đoạn trọng điểm.</p>

              <div className="space-y-4">
                {/* Segment */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-baseline text-xs font-bold">
                    <span className="text-on-surface font-extrabold">HN → Vinh</span>
                    <span className="text-primary font-black text-sm">92%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-primary" style={{ width: "92%" }} />
                  </div>
                </div>
                {/* Segment */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-baseline text-xs font-bold">
                    <span className="text-on-surface font-extrabold">Vinh → Huế</span>
                    <span className="text-[#b06f00] font-black text-sm">{avgLoad}%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-[#fdf1dc]" style={{ width: `${avgLoad}%` }} />
                  </div>
                </div>
                {/* Segment */}
                <div className="space-y-1.5">
                  <div className="flex justify-between items-baseline text-xs font-bold">
                    <span className="text-on-surface font-extrabold">Huế → Đà Nẵng</span>
                    <span className="text-red-600 font-black text-sm">98%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-red-500" style={{ width: "98%" }} />
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 p-4 bg-red-50/50 rounded-xl border border-red-200/50">
              <p className="text-[11px] text-[#b02a41] leading-relaxed font-semibold">
                ⚠ Phát hiện <span className="font-extrabold text-red-600">nút cổ chai nghiêm trọng</span> tại Huế → Đà Nẵng. Cần tối ưu phân bổ quota chặng để mở rộng ghế.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 4: Load heatmap table */}
      <div className="space-y-3 mt-6">
        <div className="flex items-center gap-2 mb-3">
          <span className="w-2 h-2 rounded bg-primary" />
          <h3 className="text-xs font-black text-on-surface uppercase tracking-wider">Chi tiết tải theo từng chặng</h3>
          <span className="text-xs text-on-surface-variant/80 font-medium">bản đồ nhiệt — tỉ lệ lấp đầy theo loại chỗ</span>
          <button
            onClick={() => router.push("/train-layout")}
            className="ml-auto text-xs font-extrabold text-primary hover:underline cursor-pointer"
          >
            Xem đầy đủ
          </button>
        </div>

        <div className="bg-white border border-outline-variant rounded-xl p-5 shadow-sm">
          {segments.isLoading ? (
            <p className="text-center text-xs text-on-surface-variant py-12 font-semibold">Đang tải bản đồ nhiệt...</p>
          ) : heatmap ? (
            <div className="overflow-x-auto">
              <table className="data-table heatmap-table w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 text-[11px] font-bold text-on-surface-variant uppercase border-b border-slate-200">
                    <th className="py-3 px-4">Chặng tàu</th>
                    {heatmap.columns.map((col) => (
                      <th key={col.key} className="py-3 px-4 text-center">{col.label}</th>
                    ))}
                    <th className="py-3 px-4 text-right">Nút cổ chai</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs font-semibold">
                  {heatmap.rows.map((row) => (
                    <tr key={row.seq} className="hover:bg-slate-50/55 transition-colors">
                      <td className="py-3.5 px-4 font-bold text-on-surface">{row.label}</td>
                      {heatmap.columns.map((col) => {
                        const load = row.loads[col.key];
                        if (load === null) {
                          return (
                            <td key={`${row.seq}-${col.key}`} className="py-3.5 px-4 text-center text-slate-400 font-normal">
                              —
                            </td>
                          );
                        }
                        const percent = Math.round(load);
                        let styleClass = "bg-[#eef1f8] text-[#5b607b]"; // h-low
                        if (percent >= 75) {
                          styleClass = "bg-[#fde3e8] text-[#c22a44]"; // h-high
                        } else if (percent >= 50) {
                          styleClass = "bg-[#fdf1dc] text-[#b06f00]"; // h-mid
                        }
                        return (
                          <td key={`${row.seq}-${col.key}`} className="py-3 px-4 text-center">
                            <span className={`inline-flex items-center justify-center min-w-[52px] px-2.5 py-1 rounded-lg font-extrabold text-xs ${styleClass}`}>
                              {percent}%
                            </span>
                          </td>
                        );
                      })}
                      <td className="py-3.5 px-4 text-right">
                        {row.isBottleneck ? (
                          <span className="px-2.5 py-1 bg-red-50 text-red-700 text-[10px] font-black rounded-full uppercase">
                            Cảnh báo
                          </span>
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
            <p className="text-center text-xs text-on-surface-variant py-12 font-semibold">Không có dữ liệu chặng.</p>
          )}
        </div>
      </div>

      {/* SECTION 5: Gap combining opportunities (Cơ hội tăng doanh thu) */}
      <div className="space-y-3 mt-6">
        <div className="flex items-center gap-2 mb-3">
          <span className="w-2 h-2 rounded bg-green-500" />
          <h3 className="text-xs font-black text-on-surface uppercase tracking-wider">Cơ hội tăng doanh thu</h3>
          <span className="text-xs text-on-surface-variant/80 font-medium">ghép nối chặng ngắn để lấp chỗ trống</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {suggestions.slice(0, 3).map((item, index) => (
            <div key={index} className="bg-white border border-outline-variant p-5 rounded-xl shadow-sm flex flex-col justify-between min-h-[170px] hover:shadow transition-shadow">
              <div>
                <div className="flex justify-between items-start gap-2 mb-2">
                  <span className="text-sm font-black text-on-surface">{item.route}</span>
                  <span className="flex-shrink-0 bg-[#e4f7ef] text-[#0f9d6e] px-2.5 py-1 rounded-full text-[10px] font-black uppercase whitespace-nowrap">
                    {item.benefit}
                  </span>
                </div>
                <p className="text-xs text-on-surface-variant font-medium leading-relaxed mb-4">{item.reason}</p>
              </div>
              <button
                onClick={() => {
                  const match = item.reason.match(/toa\s+([A-Za-z0-9]+)/i);
                  const coachNo = match ? match[1].trim() : "01";
                  router.push(`/train-layout?coach=${coachNo}`);
                }}
                className="bg-[#eeecff] text-[#5B4EE6] font-bold text-xs rounded-lg py-2 hover:bg-[#5B4EE6]/10 transition-colors w-full text-center cursor-pointer"
              >
                Xem chi tiết sơ đồ
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
