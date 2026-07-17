"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { SectionCard } from "@/features/rail-ui/components/Primitives";
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

function severityClass(value: string) {
  return value === "Trung bình" ? "severity-trung-binh" : "severity-cao";
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
    type: a.title.includes("cháy vé") ? "bottleneck" : "empty"
  }));

  const filteredAlerts = alertsToRender.filter((alert) => {
    if (filterType === "all") return true;
    return alert.type === filterType;
  });

  return (
    <div className="page-stack">
      <SectionCard
        title="Bộ lọc cảnh báo"
        subtitle="Lọc theo mức độ, loại vấn đề và nhóm chặng để xử lý theo ưu tiên."
      >
        <div className="scenario-strip">
          <button 
            className={`scenario-chip ${filterType === "all" ? "scenario-chip-active" : ""}`} 
            type="button"
            onClick={() => setFilterType("all")}
          >
            Tất cả ({alertsToRender.length})
          </button>
          <button 
            className={`scenario-chip ${filterType === "bottleneck" ? "scenario-chip-active" : ""}`} 
            type="button"
            onClick={() => setFilterType("bottleneck")}
          >
            Sắp cháy vé ({alertsToRender.filter(a => a.type === "bottleneck").length})
          </button>
          <button 
            className={`scenario-chip ${filterType === "empty" ? "scenario-chip-active" : ""}`} 
            type="button"
            onClick={() => setFilterType("empty")}
          >
            Trống cao ({alertsToRender.filter(a => a.type === "empty").length})
          </button>
        </div>
      </SectionCard>

      <SectionCard
        title="Danh sách cảnh báo điều hành"
        subtitle="Tập trung vào cảnh báo đáng xử lý ngay trong ca trực hiện tại."
      >
        <div className="stack-list">
          {filteredAlerts.map((item, idx) => (
            <article className={`alert-card ${severityClass(item.severity)}`} key={idx}>
              <div>
                <span className="alert-pill">{item.severity}</span>
                <strong>{item.title}</strong>
                <p>{item.detail}</p>
              </div>
              <button 
                className="btn btn-ghost" 
                type="button" 
                onClick={() => {
                  const routeMatch = item.title.match(/(?:Chặng|Đoạn)\s+([A-Z0-9]+)\s*→\s*([A-Z0-9]+)/i);
                  const seatMatch = item.title.match(/\(([^)]+)\)/);
                  
                  const origin = routeMatch ? routeMatch[1].trim() : "HAN";
                  const destination = routeMatch ? routeMatch[2].trim() : "DAN";
                  
                  let seatType = "giuong_nam_k6";
                  if (seatMatch && seatMatch[1].includes("Ngồi mềm")) {
                    seatType = "ngoi_mem";
                  }
                  
                  router.push(`/quote?origin=${origin}&destination=${destination}&seatType=${seatType}&date=2024-01-01`);
                }}
              >
                Xem chi tiết
              </button>
            </article>
          ))}
          {filteredAlerts.length === 0 && (
            <p style={{ textAlign: "center", color: "#888", padding: "20px" }}>
              Không có cảnh báo nào thuộc bộ lọc này.
            </p>
          )}
        </div>
      </SectionCard>
    </div>
  );
}
