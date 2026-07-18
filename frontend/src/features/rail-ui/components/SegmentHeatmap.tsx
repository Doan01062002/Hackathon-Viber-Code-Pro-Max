import React, { useState } from "react";

interface HeatmapRow {
  segment: string;
  slots: number[];
}

interface SegmentHeatmapProps {
  data?: HeatmapRow[];
}

const DEFAULT_SLOTS = ["Chuyến SE1", "Chuyến SE3", "Chuyến SE5", "Chuyến SE7", "Chuyến SE9", "Chuyến SE11"];

export function SegmentHeatmap({ data = [] }: SegmentHeatmapProps) {
  const [hoveredCell, setHoveredCell] = useState<{
    rowIdx: number;
    colIdx: number;
    val: number;
    x: number;
    y: number;
  } | null>(null);

  // Thang màu theo tải trọng
  const getCellStyles = (val: number) => {
    if (val >= 90) return "bg-red-500 text-white border-red-400 font-bold shadow-[0_0_12px_rgba(239,68,68,0.35)] animate-pulse";
    if (val >= 70) return "bg-green-600 text-white border-green-500 font-bold shadow-[0_0_8px_rgba(22,163,74,0.25)]";
    return "bg-green-100 text-green-800 border-green-200 font-medium";
  };

  return (
    <div className="bg-white border border-outline-variant rounded-xl overflow-hidden shadow-sm relative">
      <div className="p-6 border-b border-outline-variant flex flex-wrap justify-between items-center gap-4">
        <div>
          <h3 className="text-base font-bold text-on-surface">Bản đồ nhiệt tải chặng</h3>
          <p className="text-xs text-on-surface-variant font-medium mt-0.5">
            Tổng quan mật độ lấp đầy chỗ của từng phân đoạn chặng theo các lượt chạy trong ngày.
          </p>
        </div>
        
        {/* Heatmap Legend */}
        <div className="flex items-center gap-3 text-[10px] font-bold text-on-surface-variant">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-green-100 border border-green-200 inline-block" />
            Ổn định (&lt;70%)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-green-600 border border-green-500 inline-block" />
            Tốt (70–90%)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-red-500 border border-red-400 inline-block shadow-sm" />
            Nghẽn (&gt;90%)
          </span>
        </div>
      </div>

      <div className="p-6 overflow-x-auto">
        <div className="min-w-[640px] relative">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="p-2.5 text-left text-xs font-bold uppercase tracking-wider text-on-surface-variant w-[200px]">
                  Phân đoạn hành trình
                </th>
                {DEFAULT_SLOTS.map((slot, idx) => (
                  <th
                    key={idx}
                    className="p-2.5 text-center text-xs font-bold uppercase tracking-wider text-on-surface-variant"
                  >
                    {slot}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, rowIdx) => (
                <tr key={rowIdx} className="hover:bg-slate-50/50 transition-colors">
                  <td className="p-2.5 text-xs font-bold text-on-surface border-b border-outline-variant/30">
                    {row.segment}
                  </td>
                  {row.slots.map((val, colIdx) => (
                    <td
                      key={colIdx}
                      className="p-2 text-center border-b border-outline-variant/30 relative"
                    >
                      <div
                        className={`h-9 w-full rounded-lg border flex items-center justify-center text-xs transition-all duration-150 cursor-pointer ${getCellStyles(
                          val
                        )}`}
                        onMouseEnter={(e) => {
                          const rect = e.currentTarget.getBoundingClientRect();
                          setHoveredCell({
                            rowIdx,
                            colIdx,
                            val,
                            x: rect.left + rect.width / 2,
                            y: rect.top - 10,
                          });
                        }}
                        onMouseLeave={() => setHoveredCell(null)}
                      >
                        {val}%
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>

          {/* Detailed Floating Tooltip */}
          {hoveredCell && (
            <div
              style={{
                position: "fixed",
                left: `${hoveredCell.x}px`,
                top: `${hoveredCell.y}px`,
                transform: "translate(-50%, -100%)",
              }}
              className="z-50 pointer-events-none bg-gray-900 text-white text-[11px] font-semibold p-3 rounded-lg shadow-xl border border-gray-800 space-y-1 w-48 transition-all duration-100"
            >
              <p className="font-extrabold text-xs text-primary-container">
                {data[hoveredCell.rowIdx].segment}
              </p>
              <p className="opacity-90">
                Lượt chạy: <span className="font-bold text-white">{DEFAULT_SLOTS[hoveredCell.colIdx]}</span>
              </p>
              <p className="opacity-90">
                Hệ số lấp đầy:{" "}
                <span
                  className={`font-black ${
                    hoveredCell.val >= 90
                      ? "text-red-400"
                      : hoveredCell.val >= 70
                      ? "text-green-400"
                      : "text-green-300"
                  }`}
                >
                  {hoveredCell.val}%
                </span>
              </p>
              <p className="text-[9px] text-gray-400 mt-1">
                {hoveredCell.val >= 90
                  ? "⚠️ Cảnh báo nút cổ chai: Khuyến nghị tăng giá cơ hội để tối ưu hóa doanh thu."
                  : hoveredCell.val >= 70
                  ? "👍 Trạng thái lý tưởng: Doanh thu đang được tối đa hóa ổn định."
                  : "💡 Trống nhiều chỗ: Khuyến nghị chạy khuyến mãi ngắn hạn."}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
