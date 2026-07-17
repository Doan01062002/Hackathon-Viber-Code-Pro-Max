"use client";

import { useState, useEffect } from "react";
import { SectionCard } from "@/features/rail-ui/components/Primitives";
import { seatApi } from "@/features/rail-ui/api/seatApi";
import type { CoachDto, SeatPlanDto } from "@/features/rail-ui/api/seatApi";

function seatClass(value: string) {
  if (value === "selected") return "seat-selected";
  if (value === "held") return "seat-held";
  if (value === "blocked" || value === "confirmed") return "seat-blocked";
  return "seat-available";
}

export function TrainLayoutScreen() {
  const [coaches, setCoaches] = useState<CoachDto[]>([]);
  const [selectedCoachNo, setSelectedCoachNo] = useState<string>("01");
  const [seatPlan, setSeatPlan] = useState<SeatPlanDto | null>(null);
  
  const [loadingCoaches, setLoadingCoaches] = useState(false);
  const [loadingLayout, setLoadingLayout] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 1. Tải danh sách toa tàu
  async function loadCoaches() {
    try {
      setLoadingCoaches(true);
      setError(null);
      const data = await seatApi.getCoaches(1);
      setCoaches(data);
      
      const params = new URLSearchParams(window.location.search);
      const urlCoach = params.get("coach");
      if (urlCoach && data.some(c => c.coach_no === urlCoach)) {
        setSelectedCoachNo(urlCoach);
      } else if (data.length > 0) {
        setSelectedCoachNo(data[0].coach_no);
      }
    } catch (err) {
      console.error("Lỗi tải danh sách toa:", err);
      setError("Không thể tải danh sách toa tàu.");
    } finally {
      setLoadingCoaches(false);
    }
  }

  // 2. Tải sơ đồ ghế của toa tàu đang chọn
  async function loadSeatLayout(coachNo: string) {
    try {
      setLoadingLayout(true);
      const data = await seatApi.getSeatLayout(1, coachNo);
      setSeatPlan(data);
    } catch (err) {
      console.error("Lỗi tải sơ đồ ghế:", err);
    } finally {
      setLoadingLayout(false);
    }
  }

  useEffect(() => {
    loadCoaches();
  }, []);

  useEffect(() => {
    if (selectedCoachNo) {
      loadSeatLayout(selectedCoachNo);
    }
  }, [selectedCoachNo]);

  return (
    <div className="page-stack">
      {error && (
        <div className="banner banner-warning" style={{ backgroundColor: "#3a2a18", borderLeft: "4px solid #d97706", padding: "12px", borderRadius: "6px", color: "#f59e0b", fontSize: "14px", marginBottom: "8px" }}>
          ⚠️ {error}
        </div>
      )}

      <SectionCard
        title="Danh sách toa tàu"
        subtitle="Chọn toa cần theo dõi hoặc thao tác giữ chỗ, khóa ghế và ưu tiên bán."
      >
        {loadingCoaches ? (
          <p style={{ color: "var(--muted)", padding: "12px" }}>Đang tải danh sách toa tàu...</p>
        ) : (
          <div className="course-grid">
            {coaches.map((coach) => {
              const isActive = selectedCoachNo === coach.coach_no;
              return (
                <article 
                  className="course-card course-card-wide" 
                  key={coach.name}
                  style={isActive ? { border: "2px solid var(--primary)", boxShadow: "0 0 8px rgba(59, 130, 246, 0.2)" } : {}}
                >
                  <div className="course-icon" aria-hidden="true" style={isActive ? { backgroundColor: "var(--primary)", color: "#fff" } : {}}>
                    {coach.coach_no}
                  </div>
                  <strong>{coach.name}</strong>
                  <p>{coach.type}</p>
                  <div className="progress-wrap">
                    <div className="progress-track">
                      <span className="progress-fill" style={{ width: coach.occupancy }} />
                    </div>
                    <span>Tải {coach.occupancy}</span>
                  </div>
                  <button 
                    className={`btn ${isActive ? "btn-primary" : "btn-ghost"}`} 
                    type="button"
                    onClick={() => setSelectedCoachNo(coach.coach_no)}
                  >
                    {isActive ? "Đang chọn" : "Chọn toa"}
                  </button>
                </article>
              );
            })}
          </div>
        )}
      </SectionCard>

      <div className="two-up">
        <SectionCard 
          title="Sơ đồ ghế chi tiết" 
          subtitle={seatPlan ? `${seatPlan.route} • Toa ${selectedCoachNo}` : "Đang tải..."}
        >
          {loadingLayout ? (
            <p style={{ color: "var(--muted)", padding: "20px", textAlign: "center" }}>Đang tải sơ đồ ghế...</p>
          ) : seatPlan ? (
            <div className="seat-map" style={{ display: "flex", flexDirection: "column", gap: "10px", alignItems: "center" }}>
              {seatPlan.seats.map((row, rowIndex) => {
                const cols = seatPlan.seat_type === "ngoi_mem" ? 4 : 6;
                return (
                  <div className="seat-row" key={`row-${rowIndex}`} style={{ display: "flex", gap: "10px" }}>
                    {row.map((seat, seatIndex) => {
                      const seatNum = rowIndex * cols + seatIndex + 1;
                      return (
                        <button
                          aria-label={`Ghế ${seatNum}`}
                          className={`seat ${seatClass(seat)}`}
                          key={`seat-${rowIndex}-${seatIndex}`}
                          type="button"
                          style={{
                            width: "44px",
                            height: "44px",
                            borderRadius: "6px",
                            fontSize: "12px",
                            fontWeight: 600,
                            cursor: "default"
                          }}
                        >
                          {seatNum}
                        </button>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          ) : (
            <p style={{ color: "var(--muted)", padding: "20px", textAlign: "center" }}>Chọn một toa tàu để xem sơ đồ ghế.</p>
          )}
        </SectionCard>

        <SectionCard
          title="Chú giải và thao tác"
          subtitle="Phục vụ điều độ hoặc nhân sự vận hành khi cần can thiệp vào từng ghế."
        >
          {seatPlan && (
            <div className="stack-list" style={{ marginBottom: "24px" }}>
              {seatPlan.seatLegend.map((item) => (
                <div className="legend-row" key={item.label} style={{ display: "flex", alignItems: "center", gap: "12px", padding: "6px 0" }}>
                  <span 
                    className={`legend-swatch ${seatClass(item.tone)}`} 
                    style={{ display: "inline-block", width: "24px", height: "24px", borderRadius: "4px" }} 
                  />
                  <strong style={{ fontSize: "14px", color: "var(--text)" }}>{item.label}</strong>
                </div>
              ))}
            </div>
          )}

          <div className="action-row action-row-vertical" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <button className="btn btn-primary" type="button" onClick={() => alert("Đã gửi yêu cầu giữ/mở khóa ghế lên hệ thống vận hành.")}>
              Giữ hoặc mở khóa ghế
            </button>
            <button className="btn btn-ghost" type="button">
              Ưu tiên nhóm ghế
            </button>
            <button className="btn btn-ghost" type="button">
              Chuyển sang quota chặng
            </button>
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
