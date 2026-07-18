"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { seatApi } from "@/features/rail-ui/api/seatApi";
import type { CoachDto, SeatPlanDto, GapSuggestionDto } from "@/features/rail-ui/api/seatApi";

export function TrainLayoutScreen() {
  const router = useRouter();
  const [coaches, setCoaches] = useState<CoachDto[]>([]);
  const [selectedCoachNo, setSelectedCoachNo] = useState<string>("01");
  const [seatPlan, setSeatPlan] = useState<SeatPlanDto | null>(null);
  const [gapSuggestions, setGapSuggestions] = useState<GapSuggestionDto[]>([]);
  
  const [loadingCoaches, setLoadingCoaches] = useState(false);
  const [loadingLayout, setLoadingLayout] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 1. Tải danh sách toa tàu và gợi ý ghép chặng
  async function loadInitialData() {
    try {
      setLoadingCoaches(true);
      setError(null);
      
      const [coachesData, suggestionsData] = await Promise.all([
        seatApi.getCoaches(1),
        seatApi.getGapSuggestions(1)
      ]);
      
      setCoaches(coachesData);
      setGapSuggestions(suggestionsData);
      
      const params = new URLSearchParams(window.location.search);
      const urlCoach = params.get("coach");
      if (urlCoach && coachesData.some(c => c.coach_no === urlCoach)) {
        setSelectedCoachNo(urlCoach);
      } else if (coachesData.length > 0) {
        setSelectedCoachNo(coachesData[0].coach_no);
      }
    } catch (err) {
      console.error("Lỗi tải dữ liệu tàu:", err);
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
    loadInitialData();
  }, []);

  useEffect(() => {
    if (selectedCoachNo) {
      loadSeatLayout(selectedCoachNo);
    }
  }, [selectedCoachNo]);

  // CSS classes map for seats layout
  const getSeatStyles = (status: string) => {
    if (status === "selected") return "bg-primary text-white shadow-md shadow-primary/20 scale-105 border-primary";
    if (status === "held") return "bg-yellow-100 border-yellow-300 text-yellow-800 font-bold";
    if (status === "confirmed") return "bg-slate-300 text-slate-500 cursor-not-allowed border-transparent";
    if (status === "blocked") return "bg-red-100 border-red-300 text-red-800 font-bold shadow-[0_0_8px_rgba(239,68,68,0.15)]";
    return "bg-white border border-outline-variant hover:border-primary text-on-surface";
  };

  const translateSeatType = (type: string) => {
    if (type === "ngoi_mem") return "Toa Ngồi mềm điều hòa";
    if (type === "giuong_nam_k6") return "Toa Giường nằm K6";
    return type;
  };

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-lg text-yellow-700 text-xs font-semibold">
          ⚠️ Cảnh báo: {error}
        </div>
      )}

      {/* Header Section with Quick Stats */}
      <section className="flex justify-between items-center mb-6 border-b border-outline-variant/30 pb-4">
        <div>
          <h2 className="text-lg font-black text-on-surface">Giám sát và Phân bổ Chỗ ngồi</h2>
          <p className="text-xs text-on-surface-variant font-medium mt-0.5">
            Quản lý tồn kho ghế vật lý, thiết lập giới hạn quota chặng và cấu hình bid price.
          </p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 border border-primary text-primary font-bold rounded-lg hover:bg-primary/5 transition-all text-xs cursor-pointer">
            Phân đoạn Quota chặng
          </button>
          <button className="px-4 py-2 bg-primary text-on-primary font-bold rounded-lg hover:brightness-110 transition-all text-xs shadow-md cursor-pointer">
            Tái phân bổ tự động
          </button>
        </div>
      </section>

      {/* Train Capacity Map (Full Width Visual) */}
      <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
        <h3 className="font-bold text-on-surface flex items-center gap-2 mb-6">
          <span className="material-symbols-outlined text-primary">train</span>
          Sơ đồ tải trọng đoàn tàu: Tàu Thống Nhất SE1
        </h3>

        {loadingCoaches ? (
          <p className="text-center text-xs text-on-surface-variant py-6 font-semibold">Đang tải danh sách toa...</p>
        ) : (
          <div className="flex gap-2 overflow-x-auto pb-4 custom-scrollbar select-none">
            {/* Locomotive Engine */}
            <div className="min-w-[80px] h-20 bg-slate-200 text-slate-500 rounded-l-full flex flex-col items-center justify-center border-2 border-slate-300">
              <span className="material-symbols-outlined text-2xl">speed</span>
              <span className="text-[7px] font-black uppercase mt-0.5">Đầu Tàu</span>
            </div>

            {/* Coaches List */}
            {coaches.map((coach) => {
              const isActive = selectedCoachNo === coach.coach_no;
              const occupancyVal = parseInt(coach.occupancy.replace("%", "")) || 0;

              return (
                <div
                  key={coach.coach_no}
                  onClick={() => setSelectedCoachNo(coach.coach_no)}
                  className={`min-w-[145px] h-20 rounded-xl p-3 border flex flex-col justify-between cursor-pointer transition-all duration-150 ${
                    isActive
                      ? "border-2 border-primary bg-primary/5 ring-1 ring-primary"
                      : "bg-white border-outline-variant hover:bg-slate-50 text-on-surface-variant"
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-black text-on-surface">TOA {coach.coach_no}</span>
                    <span
                      className={`text-[9px] px-1.5 py-0.5 rounded font-black ${
                        occupancyVal >= 90
                          ? "bg-red-100 text-red-700"
                          : occupancyVal >= 70
                          ? "bg-green-100 text-green-700"
                          : "bg-blue-100 text-blue-700"
                      }`}
                    >
                      {coach.occupancy}
                    </span>
                  </div>

                  {/* Visual slots inside the car */}
                  <div className="grid grid-cols-4 gap-1">
                    <div className={`h-2 rounded-full ${occupancyVal > 20 ? "bg-primary" : "bg-slate-200"}`} />
                    <div className={`h-2 rounded-full ${occupancyVal > 40 ? "bg-primary" : "bg-slate-200"}`} />
                    <div className={`h-2 rounded-full ${occupancyVal > 60 ? "bg-primary" : "bg-slate-200"}`} />
                    <div className={`h-2 rounded-full ${occupancyVal > 80 ? "bg-red-500" : "bg-slate-200"}`} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Two Column Seats Layout */}
      <div className="grid grid-cols-12 gap-6">
        {/* Seat Map Panel */}
        <div className="col-span-12 lg:col-span-8 bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
          <h3 className="font-bold text-sm text-on-surface mb-1 flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-sm">airline_seat_recline_normal</span>
            Sơ đồ chỗ ngồi chi tiết
          </h3>
          <p className="text-xs text-on-surface-variant font-medium mb-6">
            {seatPlan ? `${seatPlan.route} • Toa ${selectedCoachNo} (${translateSeatType(seatPlan.seat_type)})` : "Chọn toa tàu để xem chi tiết"}
          </p>

          {loadingLayout ? (
            <p className="text-center text-xs text-on-surface-variant py-12 font-semibold">Đang tải sơ đồ ghế...</p>
          ) : seatPlan ? (
            <div className="border border-slate-200 rounded-2xl p-6 bg-slate-50/50 max-w-xl mx-auto flex items-stretch">
              <div className="w-full flex flex-col gap-3 py-1 overflow-x-auto custom-scrollbar">
                {seatPlan.seats.map((row, rowIndex) => {
                  const cols = seatPlan.seat_type === "ngoi_mem" ? 4 : 6;
                  return (
                    <div className="flex flex-row justify-center items-center gap-3" key={`row-${rowIndex}`}>
                      {row.map((seat, seatIndex) => {
                        const seatNum = rowIndex * cols + seatIndex + 1;
                        return (
                          <button
                            key={`seat-${rowIndex}-${seatIndex}`}
                            className={`w-10 h-10 rounded-lg text-xs font-bold border flex items-center justify-center transition-all flex-shrink-0 cursor-default ${getSeatStyles(seat)}`}
                            type="button"
                          >
                            {seatNum}
                          </button>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <p className="text-center text-xs text-on-surface-variant py-12 font-semibold">Không có dữ liệu sơ đồ ghế.</p>
          )}
        </div>

        {/* Legend and Operations Panel */}
        <div className="col-span-12 lg:col-span-4 bg-white border border-outline-variant rounded-xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-sm text-on-surface mb-4 border-b border-outline-variant/30 pb-2">
              Chú giải và Thao tác can thiệp
            </h3>

            {seatPlan ? (
              <div className="space-y-3 mb-6">
                {seatPlan.seatLegend.map((item) => (
                  <div className="flex items-center gap-3 py-1" key={item.label}>
                    <span 
                      className={`w-6 h-6 rounded border ${getSeatStyles(item.tone)} flex items-center justify-center`}
                    />
                    <span className="text-xs font-bold text-on-surface-variant">{item.label}</span>
                  </div>
                ))}
              </div>
            ) : null}
          </div>

          <div className="space-y-2">
            <button
              onClick={() => window.alert("Đã gửi yêu cầu điều chỉnh trạng thái ghế lên hệ thống vận hành.")}
              className="w-full py-2 bg-primary text-on-primary font-bold rounded-lg text-xs hover:brightness-110 active:scale-95 transition-all cursor-pointer shadow-sm"
            >
              Giữ hoặc mở khóa ghế
            </button>
            <button className="w-full py-2 border border-outline-variant text-on-surface hover:bg-slate-50 font-bold rounded-lg text-xs transition-all cursor-pointer">
              Ưu tiên bán nhóm ghế
            </button>
            <button className="w-full py-2 border border-outline-variant text-on-surface hover:bg-slate-50 font-bold rounded-lg text-xs transition-all cursor-pointer">
              Chuyển sang Quota chặng ngắn
            </button>
          </div>
        </div>
      </div>

      {/* Seat Inventory Table & AI Suggestions */}
      <div className="grid grid-cols-12 gap-6">
        {/* Seat Inventory Card */}
        <div className="col-span-12 lg:col-span-8 bg-white border border-outline-variant rounded-xl overflow-hidden shadow-sm">
          <div className="p-6 border-b border-outline-variant flex justify-between items-center">
            <h3 className="font-bold text-on-surface text-sm">Phân bổ tồn kho chỗ ngồi chặng (Inventory Allocation)</h3>
            <div className="flex gap-2">
              <span className="px-2 py-0.5 bg-surface-container-low text-primary rounded text-[9px] font-bold">
                CHẶNG DÀI (80%)
              </span>
              <span className="px-2 py-0.5 bg-secondary-container text-on-secondary-container rounded text-[9px] font-bold">
                CHẶNG NGẮN (20%)
              </span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-surface-container-low text-on-surface-variant font-bold text-xs">
                <tr>
                  <th className="px-6 py-4">PHÂN ĐOẠN CHẶNG</th>
                  <th className="px-6 py-4">HẠNG GHẾ</th>
                  <th className="px-6 py-4">ĐÃ PHÂN BỔ</th>
                  <th className="px-6 py-4">ĐÃ BÁN</th>
                  <th className="px-6 py-4">GIÁ CƠ HỘI</th>
                  <th className="px-6 py-4 text-right">KHUYẾN NGHỊ AI</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant text-sm font-semibold">
                <tr className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 text-on-surface">Hà Nội → Sài Gòn (Chặng Dài)</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-0.5 border border-primary/30 text-primary text-[10px] rounded font-bold uppercase">
                      Giường nằm
                    </span>
                  </td>
                  <td className="px-6 py-4 text-on-surface-variant font-medium">120 Ghế</td>
                  <td className="px-6 py-4">
                    <div className="w-full bg-slate-100 h-1.5 rounded-full mt-1 max-w-[120px]">
                      <div className="bg-primary h-1.5 rounded-full" style={{ width: "85%" }} />
                    </div>
                    <span className="text-[10px] text-on-surface-variant font-bold">102 / 120 (85%)</span>
                  </td>
                  <td className="px-6 py-4 font-mono text-xs">850.000 VND</td>
                  <td className="px-6 py-4 text-right">
                    <span className="text-red-500 font-bold text-[11px]">+12.4% Tăng giá cơ hội</span>
                  </td>
                </tr>
                <tr className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 text-on-surface">Hà Nội → Vinh (Chặng Ngắn)</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-0.5 border border-primary/30 text-primary text-[10px] rounded font-bold uppercase">
                      Ngồi mềm
                    </span>
                  </td>
                  <td className="px-6 py-4 text-on-surface-variant font-medium">400 Ghế</td>
                  <td className="px-6 py-4">
                    <div className="w-full bg-slate-100 h-1.5 rounded-full mt-1 max-w-[120px]">
                      <div className="bg-primary h-1.5 rounded-full" style={{ width: "42%" }} />
                    </div>
                    <span className="text-[10px] text-on-surface-variant font-bold">168 / 400 (42%)</span>
                  </td>
                  <td className="px-6 py-4 font-mono text-xs">220.000 VND</td>
                  <td className="px-6 py-4 text-right">
                    <span className="text-primary font-bold text-[11px]">-5.0% Chạy ưu đãi</span>
                  </td>
                </tr>
                <tr className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 text-on-surface">Vinh → Sài Gòn (Chặng Dài)</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-0.5 border border-primary/30 text-primary text-[10px] rounded font-bold uppercase">
                      Ngồi mềm
                    </span>
                  </td>
                  <td className="px-6 py-4 text-on-surface-variant font-medium">400 Ghế</td>
                  <td className="px-6 py-4">
                    <div className="w-full bg-slate-100 h-1.5 rounded-full mt-1 max-w-[120px]">
                      <div className="bg-primary h-1.5 rounded-full" style={{ width: "95%" }} />
                    </div>
                    <span className="text-[10px] text-on-surface-variant font-bold">380 / 400 (95%)</span>
                  </td>
                  <td className="px-6 py-4 font-mono text-xs">680.000 VND</td>
                  <td className="px-6 py-4 text-right">
                    <span className="text-red-500 font-bold text-[11px]">Đã chạm giới hạn</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* AI Recommendations Panel */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          <div className="bg-white border-l-4 border-primary border-y border-r border-outline-variant rounded-xl p-6 shadow-sm relative overflow-hidden">
            <div className="absolute top-0 right-0 p-2 opacity-5">
              <span className="material-symbols-outlined text-6xl">auto_awesome</span>
            </div>
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-primary text-sm">auto_awesome</span>
              <h3 className="font-bold text-on-surface">Cơ hội ghép chặng (Gap Combining)</h3>
            </div>
            <p className="text-xs text-on-surface-variant mb-4 leading-relaxed font-semibold">
              AI phát hiện các cơ hội chặng ngắn trống liên tiếp ghép thành chặng dài để tăng doanh thu.
            </p>

            <div className="space-y-3">
              {gapSuggestions.length > 0 ? (
                gapSuggestions.map((item, idx) => (
                  <div className="p-3 bg-surface-container-low rounded-lg border border-primary/10" key={idx}>
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-bold text-xs text-on-surface">{item.route}</span>
                      <span className="text-primary font-bold text-xs">{item.benefit}</span>
                    </div>
                    <p className="text-[11px] text-on-surface-variant leading-relaxed font-medium">
                      {item.reason} ({item.seatType === "ngoi_mem" ? "Ngồi mềm" : "Giường nằm"})
                    </p>
                    <button className="mt-2 w-full py-1.5 bg-primary/10 text-primary font-bold text-[10px] rounded hover:bg-primary/20 transition-all cursor-pointer">
                      Thực hiện ghép chặng
                    </button>
                  </div>
                ))
              ) : (
                <p className="text-xs text-on-surface-variant/75 text-center py-4">Không có gợi ý ghép chặng trống nào.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
