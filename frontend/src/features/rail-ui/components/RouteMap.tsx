"use client";

import React, { useState } from "react";

export interface RouteSegment {
  id: string;
  label: string;
  loadPct: number;
  originCode?: string;
  originName?: string;
  destinationCode?: string;
  destinationName?: string;
  remaining?: number;
  capacity?: number;
}

export const MOCK_ROUTE_SEGMENTS: RouteSegment[] = [
  { id: "HAN-NDI", label: "Ha Noi - Nam Dinh", loadPct: 55, originCode: "HAN", originName: "Ha Noi", destinationCode: "NDI", destinationName: "Nam Dinh" },
  { id: "NDI-NBH", label: "Nam Dinh - Ninh Binh", loadPct: 68, originCode: "NDI", originName: "Nam Dinh", destinationCode: "NBH", destinationName: "Ninh Binh" },
  { id: "NBH-THH", label: "Ninh Binh - Thanh Hoa", loadPct: 45, originCode: "NBH", originName: "Ninh Binh", destinationCode: "THH", destinationName: "Thanh Hoa" },
  { id: "THH-VIH", label: "Thanh Hoa - Vinh", loadPct: 92, originCode: "THH", originName: "Thanh Hoa", destinationCode: "VIH", destinationName: "Vinh" },
  { id: "VIH-HUE", label: "Vinh - Hue", loadPct: 74, originCode: "VIH", originName: "Vinh", destinationCode: "HUE", destinationName: "Hue" },
  { id: "HUE-DAN", label: "Hue - Da Nang", loadPct: 88, originCode: "HUE", originName: "Hue", destinationCode: "DAN", destinationName: "Da Nang" },
];

interface RouteMapProps {
  segments?: RouteSegment[];
  title?: string;
  loading?: boolean;
  selectedOrigin?: string;
  selectedDestination?: string;
}

export function RouteMap({
  segments = MOCK_ROUTE_SEGMENTS,
  title = "Bản đồ tải chặng",
  loading = false,
  selectedOrigin,
  selectedDestination,
}: RouteMapProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const getSegmentColor = (load: number) => {
    if (load >= 90) return "#ef4444"; // Đỏ (Nghẽn)
    if (load >= 70) return "#16a34a"; // Xanh đậm (Tốt)
    return "#86efac"; // Xanh nhạt (Ổn định)
  };

  const getSegmentLabel = (load: number) => {
    if (load >= 90) return "Tắc nghẽn";
    if (load >= 70) return "Tốt";
    return "Ổn định";
  };

  if (loading) {
    return (
      <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
        <div className="h-40 rounded-xl bg-slate-100 animate-pulse" />
      </div>
    );
  }

  if (segments.length === 0) {
    return (
      <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
        <div className="h-40 rounded-xl border border-dashed border-outline-variant flex items-center justify-center text-xs font-semibold text-on-surface-variant">
          Chọn hành trình để tải bản đồ chặng.
        </div>
      </div>
    );
  }

  const columnsCount = Math.ceil((segments.length + 1) / 2);
  const stride = columnsCount > 1 ? 800 / (columnsCount - 1) : 0;

  // Danh sách mã ga trên tuyến thực tế
  const routeStationCodes = [
    segments[0]?.originCode ?? "",
    ...segments.map((s) => s.destinationCode ?? ""),
  ];

  const originIdx = selectedOrigin ? routeStationCodes.indexOf(selectedOrigin) : -1;
  const destIdx = selectedDestination ? routeStationCodes.indexOf(selectedDestination) : -1;

  const isSegmentSelected = (idx: number) => {
    if (originIdx === -1 || destIdx === -1) return false;
    const min = Math.min(originIdx, destIdx);
    const max = Math.max(originIdx, destIdx);
    return idx >= min && idx < max;
  };

  const isStationSelected = (idx: number) => {
    if (originIdx === -1 || destIdx === -1) return true;
    const min = Math.min(originIdx, destIdx);
    const max = Math.max(originIdx, destIdx);
    return idx >= min && idx <= max;
  };

  // Xây dựng danh sách ga động dựa trên dữ liệu chặng từ database
  const stationsList = Array.from({ length: segments.length + 1 }, (_, i) => {
    const isTop = i % 2 === 0;
    const colIdx = Math.floor(i / 2);
    const name = i === 0
      ? (segments[0].originName ?? segments[0].originCode ?? "Ga đầu")
      : (segments[i - 1].destinationName ?? segments[i - 1].destinationCode ?? `Ga ${i}`);
    const code = i === 0
      ? segments[0].originCode
      : segments[i - 1].destinationCode;

    const x = columnsCount > 1 ? 50 + colIdx * stride : 450;

    return {
      name,
      code: code ?? "",
      x,
      y: isTop ? 45 : 145,
      isTop,
    };
  });

  return (
    <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
      <style>{`
        @keyframes rail-pulse {
          from {
            stroke-dashoffset: 16;
          }
          to {
            stroke-dashoffset: 0;
          }
        }
        .rail-pulse-line {
          stroke-dasharray: 8 8;
          animation: rail-pulse 0.8s linear infinite;
        }
      `}</style>
      <div className="flex flex-wrap items-center gap-2 mb-6">
        <span className="material-symbols-outlined text-primary text-sm">route</span>
        <h3 className="font-bold text-sm text-on-surface">{title}</h3>
        <div className="ml-auto flex items-center gap-3 text-[10px] font-bold text-on-surface-variant">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-green-300 inline-block" />
            Ổn định (&lt;70%)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-green-600 inline-block" />
            Tốt (70-90%)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" />
            Nghẽn (&gt;90%)
          </span>
        </div>
      </div>

      <div className="relative w-full">
        <svg className="w-full h-auto overflow-visible select-none" viewBox="0 0 900 220">
          {/* Đường trục răng cưa nét đứt hàng trên và hàng dưới */}
          <line x1="50" y1="45" x2={columnsCount > 1 ? 850 : 450} y2="45" stroke="#cbd5e1" strokeWidth="1.5" strokeDasharray="3 3" />
          <line x1="50" y1="145" x2={columnsCount > 1 ? (segments.length % 2 === 0 ? 850 - stride : 850) : 450} y2="145" stroke="#cbd5e1" strokeWidth="1.5" strokeDasharray="3 3" />

          {/* Các chặng liên kết (Đoạn thẳng và Hiệu ứng mạch xung) */}
          {segments.map((seg, idx) => {
            const start = stationsList[idx];
            const end = stationsList[idx + 1];
            const isHovered = hoveredIdx === idx;
            const selected = isSegmentSelected(idx);
            // Nếu chặng nằm ngoài vùng được chọn, hiển thị màu xanh dương nhạt
            const strokeColor = selected ? getSegmentColor(seg.loadPct) : "#bfdbfe";
            const shouldPulse = selected && seg.loadPct >= 70;

            return (
              <g key={seg.id}>
                {/* Hiệu ứng hào quang phát sáng khi hover */}
                {isHovered && (
                  <line
                    x1={start.x}
                    y1={start.y}
                    x2={end.x}
                    y2={end.y}
                    stroke={strokeColor}
                    strokeWidth="10"
                    strokeLinecap="round"
                    opacity="0.3"
                    className="transition-all duration-150"
                  />
                )}
                
                {/* Đường ray chính của chặng */}
                <line
                  x1={start.x}
                  y1={start.y}
                  x2={end.x}
                  y2={end.y}
                  stroke={strokeColor}
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  className="cursor-pointer transition-all duration-150 hover:stroke-[5px]"
                  onMouseEnter={() => {
                    setHoveredIdx(idx);
                    const midX = (start.x + end.x) / 2;
                    const midY = (start.y + end.y) / 2;
                    setTooltipPos({ x: midX, y: midY });
                  }}
                  onMouseLeave={() => setHoveredIdx(null)}
                />
                
                {/* Hoạt ảnh tàu chạy dạng mạch xung phát sáng (dành cho chặng đông hoặc nghẽn) */}
                {shouldPulse && (
                  <>
                    <line
                      x1={start.x}
                      y1={start.y}
                      x2={end.x}
                      y2={end.y}
                      stroke={strokeColor}
                      strokeWidth="6"
                      strokeLinecap="round"
                      opacity="0.35"
                      className="pointer-events-none"
                    />
                    <line
                      x1={start.x}
                      y1={start.y}
                      x2={end.x}
                      y2={end.y}
                      stroke="#ffffff"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      className="rail-pulse-line opacity-95 pointer-events-none"
                    />
                  </>
                )}

                {/* Nhãn % lấp đầy nằm đè trên trung điểm đường ray */}
                <g transform={`translate(${(start.x + end.x) / 2}, ${(start.y + end.y) / 2})`}>
                  <rect
                    x="-18"
                    y="-8"
                    width="36"
                    height="16"
                    rx="4"
                    fill={selected ? "#1e293b" : "#cbd5e1"}
                    className="pointer-events-none"
                  />
                  <text
                    x="0"
                    y="3"
                    fill={selected ? "#fff" : "#64748b"}
                    fontSize="9"
                    fontWeight="bold"
                    textAnchor="middle"
                    className="pointer-events-none font-mono"
                  >
                    {seg.loadPct.toFixed(0)}%
                  </text>
                </g>
              </g>
            );
          })}

          {/* Các Node ga tàu (Vòng tròn kép và nhãn Tên/Mã ga) */}
          {stationsList.map((station, idx) => {
            const isTop = station.isTop;
            const selected = isStationSelected(idx);
            
            // Màu sắc vòng ngoài (mờ đi nếu ngoài vùng chọn)
            const outerCircleColor = selected
              ? (idx === destIdx ? "#3525cd" : "#334155")
              : "#cbd5e1";

            return (
              <g key={`${station.code}-${idx}`}>
                {/* Vòng tròn bên ngoài */}
                <circle
                  cx={station.x}
                  cy={station.y}
                  r="8"
                  fill={outerCircleColor}
                />
                {/* Nhân trắng bên trong */}
                <circle
                  cx={station.x}
                  cy={station.y}
                  r="4"
                  fill="#fff"
                />
                {/* Tên ga tiếng Việt */}
                <text
                  x={station.x}
                  y={isTop ? 22 : 172}
                  textAnchor="middle"
                  className={`text-[10px] font-black transition-all ${
                    selected ? "text-on-surface" : "text-on-surface-variant/40"
                  }`}
                >
                  {station.name}
                </text>
                {/* Mã ga viết tắt */}
                <text
                  x={station.x}
                  y={isTop ? 10 : 184}
                  textAnchor="middle"
                  className={`text-[8px] font-extrabold font-mono transition-all ${
                    selected ? "text-on-surface-variant/50" : "text-on-surface-variant/20"
                  }`}
                >
                  {station.code}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Tooltip nổi khi Hover qua các chặng */}
        {hoveredIdx !== null && (
          <div
            style={{
              position: "absolute",
              left: `${(tooltipPos.x / 900) * 100}%`,
              top: `${tooltipPos.y - 12}px`,
              transform: "translate(-50%, -100%)",
            }}
            className="z-50 pointer-events-none bg-slate-900 text-white text-[10px] font-semibold px-3 py-2 rounded-lg shadow-xl whitespace-nowrap space-y-0.5 border border-slate-800"
          >
            <p className="font-bold text-xs text-primary-container">
              {segments[hoveredIdx].label}
            </p>
            <p>
              Tải chặng: <span className="font-black text-white">{segments[hoveredIdx].loadPct.toFixed(1)}%</span>
            </p>
            <p className="opacity-75">
              Trạng thái: <span className="font-bold">{getSegmentLabel(segments[hoveredIdx].loadPct)}</span>
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
