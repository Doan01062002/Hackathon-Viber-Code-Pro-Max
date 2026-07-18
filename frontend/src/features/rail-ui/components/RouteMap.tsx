"use client";

import React, { useState } from "react";

export interface RouteSegment {
  id: string;
  label: string;
  loadPct: number;
}

interface StationNode {
  name: string;
  code: string;
  x: number;
  y: number;
}

// ─── Station database (17 stations) ──────────────────────────────────────────

const STATIONS: StationNode[] = [
  { name: "Hà Nội", code: "HN", x: 50, y: 45 },
  { name: "Nam Định", code: "ND", x: 50, y: 145 },
  { name: "Ninh Bình", code: "NB", x: 150, y: 45 },
  { name: "Thanh Hóa", code: "TH", x: 150, y: 145 },
  { name: "Vinh", code: "VII", x: 250, y: 45 },
  { name: "Đồng Hới", code: "DH", x: 250, y: 145 },
  { name: "Huế", code: "HUE", x: 350, y: 45 },
  { name: "Đà Nẵng", code: "DAD", x: 350, y: 145 },
  { name: "Tam Kỳ", code: "TK", x: 450, y: 45 },
  { name: "Quảng Ngãi", code: "QN", x: 450, y: 145 },
  { name: "Quy Nhơn", code: "QNH", x: 550, y: 45 },
  { name: "Tuy Hòa", code: "THO", x: 550, y: 145 },
  { name: "Nha Trang", code: "NHA", x: 650, y: 45 },
  { name: "Phan Rang", code: "PR", x: 650, y: 145 },
  { name: "Bình Thuận", code: "BT", x: 750, y: 45 },
  { name: "Biên Hòa", code: "BH", x: 750, y: 145 },
  { name: "TP. HCM", code: "SGN", x: 850, y: 45 },
];

export const MOCK_ROUTE_SEGMENTS: RouteSegment[] = [
  { id: "HN-NAM", label: "Hà Nội - Nam Định", loadPct: 55 },
  { id: "NAM-NB", label: "Nam Định - Ninh Bình", loadPct: 68 },
  { id: "NB-TH", label: "Ninh Bình - Thanh Hóa", loadPct: 45 },
  { id: "TH-VINH", label: "Thanh Hóa - Vinh", loadPct: 92 },
  { id: "VINH-DH", label: "Vinh - Đồng Hới", loadPct: 74 },
  { id: "DH-HUE", label: "Đồng Hới - Huế", loadPct: 88 },
  { id: "HUE-DN", label: "Huế - Đà Nẵng", loadPct: 96 },
  { id: "DN-TK", label: "Đà Nẵng - Tam Kỳ", loadPct: 35 },
  { id: "TK-QN", label: "Tam Kỳ - Quảng Ngãi", loadPct: 48 },
  { id: "QN-QNH", label: "Quảng Ngãi - Quy Nhơn", loadPct: 62 },
  { id: "QNH-THO", label: "Quy Nhơn - Tuy Hòa", loadPct: 71 },
  { id: "THO-NT", label: "Tuy Hòa - Nha Trang", loadPct: 82 },
  { id: "NT-PR", label: "Nha Trang - Phan Rang", loadPct: 50 },
  { id: "PR-BT", label: "Phan Rang - Bình Thuận", loadPct: 67 },
  { id: "BT-BH", label: "Bình Thuận - Biên Hòa", loadPct: 89 },
  { id: "BH-SGN", label: "Biên Hòa - TP. HCM", loadPct: 98 },
];

interface RouteMapProps {
  segments?: RouteSegment[];
  title?: string;
}

export function RouteMap({ segments = MOCK_ROUTE_SEGMENTS, title = "Bản đồ tải chặng tuyến Bắc - Nam" }: RouteMapProps) {
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
          {/* Top and Bottom grey backbone lines */}
          <line x1="50" y1="45" x2="850" y2="45" stroke="#cbd5e1" strokeWidth="1.5" strokeDasharray="3 3" />
          <line x1="50" y1="145" x2="750" y2="145" stroke="#cbd5e1" strokeWidth="1.5" strokeDasharray="3 3" />

          {/* Connecting segments (Lines) */}
          {segments.map((seg, idx) => {
            const start = STATIONS[idx];
            const end = STATIONS[idx + 1];
            const isHovered = hoveredIdx === idx;
            const strokeColor = getSegmentColor(seg.loadPct);

            return (
              <g key={seg.id}>
                {/* Glow layer when hovered */}
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
                {/* Active rail segment line */}
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
                    // Calculate coordinate in SVG space for tooltip
                    const midX = (start.x + end.x) / 2;
                    const midY = (start.y + end.y) / 2;
                    setTooltipPos({ x: midX, y: midY });
                  }}
                  onMouseLeave={() => setHoveredIdx(null)}
                />
                {/* Glowing train pulse travel animation along the active segment lines */}
                {(idx === 3 || idx === 8 || idx === 14) && (
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
                {/* Label show % on segment line */}
                <g transform={`translate(${(start.x + end.x) / 2}, ${(start.y + end.y) / 2})`}>
                  <rect
                    x="-15"
                    y="-8"
                    width="30"
                    height="16"
                    rx="4"
                    fill="#1e293b"
                    className="pointer-events-none"
                  />
                  <text
                    x="0"
                    y="3"
                    fill="#fff"
                    fontSize="9"
                    fontWeight="bold"
                    textAnchor="middle"
                    className="pointer-events-none font-mono"
                  >
                    {seg.loadPct}%
                  </text>
                </g>
              </g>
            );
          })}

          {/* Station Nodes */}
          {STATIONS.map((station, idx) => {
            const isTop = idx % 2 === 0;
            return (
              <g key={station.code}>
                {/* Outer circle */}
                <circle
                  cx={station.x}
                  cy={station.y}
                  r="8"
                  fill="#334155"
                />
                {/* Inner core */}
                <circle
                  cx={station.x}
                  cy={station.y}
                  r="4"
                  fill="#fff"
                />
                {/* Station name text */}
                <text
                  x={station.x}
                  y={isTop ? 22 : 172}
                  textAnchor="middle"
                  className="text-[10px] font-black text-on-surface"
                >
                  {station.name}
                </text>
                {/* Station Code */}
                <text
                  x={station.x}
                  y={isTop ? 10 : 184}
                  textAnchor="middle"
                  className="text-[8px] font-extrabold text-on-surface-variant/50 font-mono"
                >
                  {station.code}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Floating Tooltip */}
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
              Tải chặng: <span className="font-black text-white">{segments[hoveredIdx].loadPct}%</span>
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
