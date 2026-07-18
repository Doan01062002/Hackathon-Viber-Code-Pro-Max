"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api/client";
import { alerts as mockAlerts } from "@/features/rail-ui/mockData";

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

export function AlertsScreen() {
  const router = useRouter();
  const [legs, setLegs] = useState<LegHeatmapItem[]>([]);
  const [filterType, setFilterType] = useState<"all" | "bottleneck" | "empty">("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchLegs() {
      try {
        const res = await apiClient.get<LegHeatmapResponse>("/api/v1/analytics/legs-heatmap?trip_id=1");
        setLegs(res.legs);
      } catch (err) {
        console.warn("Lỗi tải chặng heatmap, sử dụng fallback alerts:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchLegs();
  }, []);

  // Phát sinh cảnh báo động từ dữ liệu chặng thực tế trong DB
  const generatedAlerts = legs.map((leg) => {
    const load = Math.round(((leg.capacity - leg.remaining) / leg.capacity) * 100);
    const seatName = leg.seat_type === "soft_seat" ? "Ngồi mềm" : "Giường nằm";
    
    if (leg.is_bottleneck || load >= 85) {
      return {
        severity: "Cao",
        title: `Chặng ${leg.origin_station_code} → ${leg.destination_station_code} sắp cháy vé (${seatName})`,
        detail: `Tồn kho còn ${leg.remaining} / ${leg.capacity} ghế (Tải: ${load}%). Giá cơ hội hiện tại đang ở mức cao: ${leg.bid_price.toLocaleString()} VND.`,
        type: "bottleneck"
      };
    } else if (load <= 40) {
      return {
        severity: "Trung bình",
        title: `Đoạn ${leg.origin_station_code} → ${leg.destination_station_code} trống cao (${seatName})`,
        detail: `Tồn kho dư thừa ${leg.remaining} / ${leg.capacity} ghế (Tải: ${load}%). Khuyến nghị điều chỉnh giảm bid price để tăng lấp đầy.`,
        type: "empty"
      };
    }
    return null;
  }).filter((x): x is NonNullable<typeof x> => x !== null);

  const alertsToRender = generatedAlerts.length > 0 ? generatedAlerts : mockAlerts.map(a => ({
    ...a,
    type: a.title.includes("cháy vé") || a.severity === "Cao" ? "bottleneck" : "empty"
  }));

  const filteredAlerts = alertsToRender.filter((alert) => {
    if (filterType === "all") return true;
    return alert.type === filterType;
  });

  return (
    <div className="space-y-6">

      {/* Filter Buttons */}
      <div className="flex gap-2 border-b border-outline-variant/30 pb-4">
        <button
          onClick={() => setFilterType("all")}
          className={`px-4 py-2 rounded-lg font-bold text-xs transition-all ${
            filterType === "all"
              ? "bg-primary text-on-primary"
              : "bg-white border border-outline-variant text-on-surface hover:bg-slate-50"
          }`}
        >
          Tất cả ({alertsToRender.length})
        </button>
        <button
          onClick={() => setFilterType("bottleneck")}
          className={`px-4 py-2 rounded-lg font-bold text-xs transition-all ${
            filterType === "bottleneck"
              ? "bg-primary text-on-primary"
              : "bg-white border border-outline-variant text-on-surface hover:bg-slate-50"
          }`}
        >
          Sắp cháy vé ({alertsToRender.filter(a => a.type === "bottleneck").length})
        </button>
        <button
          onClick={() => setFilterType("empty")}
          className={`px-4 py-2 rounded-lg font-bold text-xs transition-all ${
            filterType === "empty"
              ? "bg-primary text-on-primary"
              : "bg-white border border-outline-variant text-on-surface hover:bg-slate-50"
          }`}
        >
          Trống cao ({alertsToRender.filter(a => a.type === "empty").length})
        </button>
      </div>

      {/* Alerts List */}
      <div className="space-y-4">
        {filteredAlerts.map((alert, idx) => {
          const isHigh = alert.severity === "Cao";
          return (
            <div
              key={idx}
              className={`p-5 rounded-xl border flex justify-between items-start gap-4 transition-colors duration-200 ${
                isHigh
                  ? "bg-error-container/10 border-error/20 hover:bg-error-container/20"
                  : "bg-surface border-outline-variant hover:bg-surface-container-low"
              }`}
            >
              <div className="flex gap-4">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                    isHigh ? "bg-error text-white" : "bg-secondary text-white"
                  }`}
                >
                  <span className="material-symbols-outlined text-base">
                    {isHigh ? "warning" : "info"}
                  </span>
                </div>
                <div>
                  <p className={`font-bold text-sm ${isHigh ? "text-error" : "text-on-surface"}`}>
                    {alert.title}
                  </p>
                  <p className="text-xs text-on-surface-variant font-semibold mt-1 leading-relaxed">
                    {alert.detail}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 flex-shrink-0">
                <span
                  className={`px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                    isHigh ? "bg-error/15 text-error" : "bg-secondary-container text-on-secondary-container"
                  }`}
                >
                  {alert.severity}
                </span>
                <button
                  onClick={() => {
                    const routeMatch = alert.title.match(/(?:Chặng|Đoạn)\s+([A-Za-z0-9]+)\s*→\s*([A-Za-z0-9]+)/i);
                    const seatMatch = alert.title.match(/\(([^)]+)\)/);
                    
                    const origin = routeMatch ? routeMatch[1].trim() : "HN";
                    const destination = routeMatch ? routeMatch[2].trim() : "DAN";
                    
                    let seatType = "giuong_nam_k6";
                    if (seatMatch && seatMatch[1].includes("Ngồi mềm")) {
                      seatType = "ngoi_mem";
                    }
                    
                    router.push(`/quote?origin=${origin}&destination=${destination}&seatType=${seatType}&date=2026-07-19`);
                  }}
                  className="px-3 py-1.5 border border-outline-variant rounded-md text-xs font-bold hover:bg-surface-container transition-colors text-on-surface cursor-pointer"
                >
                  Xem chi tiết
                </button>
              </div>
            </div>
          );
        })}

        {filteredAlerts.length === 0 && (
          <p className="text-center text-xs text-on-surface-variant font-semibold py-8">
            Không có cảnh báo nào thuộc bộ lọc này.
          </p>
        )}
      </div>
    </div>
  );
}
