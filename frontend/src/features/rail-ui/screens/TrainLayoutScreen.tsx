"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { seatApi } from "@/features/rail-ui/api/seatApi";
import type { CoachDto, SeatPlanDto, GapSuggestionDto, TripOptionDto } from "@/features/rail-ui/api/seatApi";

export function TrainLayoutScreen() {
  const router = useRouter();
  const [trips, setTrips] = useState<TripOptionDto[]>([]);
  const [selectedTripId, setSelectedTripId] = useState<number | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [coaches, setCoaches] = useState<CoachDto[]>([]);
  const [selectedCoachNo, setSelectedCoachNo] = useState<string>("01");
  const [seatPlan, setSeatPlan] = useState<SeatPlanDto | null>(null);
  const [gapSuggestions, setGapSuggestions] = useState<GapSuggestionDto[]>([]);
  
  const [loadingCoaches, setLoadingCoaches] = useState(false);
  const [loadingLayout, setLoadingLayout] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 1. Tải danh sách chuyến tàu lúc khởi động
  async function loadInitialData() {
    try {
      setLoadingCoaches(true);
      setError(null);
      
      const tripsData = await seatApi.getTrips();
      setTrips(tripsData);
      
      if (tripsData.length > 0) {
        const params = new URLSearchParams(window.location.search);
        const urlTripId = params.get("tripId");
        
        let initialTrip = tripsData[0];
        if (urlTripId) {
          const matched = tripsData.find(t => String(t.trip_id) === urlTripId);
          if (matched) initialTrip = matched;
        }
        
        setSelectedDate(initialTrip.service_date);
        setSelectedTripId(initialTrip.trip_id);
      }
    } catch (err) {
      console.error("Lỗi tải danh sách chuyến tàu:", err);
      setError("Không thể tải danh sách chuyến tàu.");
    } finally {
      setLoadingCoaches(false);
    }
  }

  // 2. Tải danh sách toa và khuyến nghị AI khi selectedTripId thay đổi
  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (!selectedTripId) return;

    let active = true;
    async function loadTripData() {
      try {
        setLoadingCoaches(true);
        const [coachesData, suggestionsData] = await Promise.all([
          seatApi.getCoaches(selectedTripId),
          seatApi.getGapSuggestions(selectedTripId)
        ]);
        if (!active) return;
        setCoaches(coachesData);
        setGapSuggestions(suggestionsData);

        const params = new URLSearchParams(window.location.search);
        const urlCoach = params.get("coach");

        if (coachesData.length > 0) {
          const coachNos = coachesData.map(c => c.coach_no);
          if (urlCoach && coachNos.includes(urlCoach)) {
            setSelectedCoachNo(urlCoach);
          } else {
            setSelectedCoachNo(coachesData[0].coach_no);
          }
        }
      } catch (err) {
        console.error("Lỗi tải dữ liệu toa tàu:", err);
      } finally {
        if (active) setLoadingCoaches(false);
      }
    }

    void loadTripData();
    return () => { active = false; };
  }, [selectedTripId]);

  // 3. Tải sơ đồ ghế của toa tàu đang chọn
  useEffect(() => {
    if (!selectedTripId || !selectedCoachNo) return;

    let active = true;
    async function loadSeatLayout() {
      try {
        setLoadingLayout(true);
        const data = await seatApi.getSeatLayout(selectedTripId, selectedCoachNo);
        if (active) setSeatPlan(data);
      } catch (err) {
        console.error("Lỗi tải sơ đồ ghế:", err);
      } finally {
        if (active) setLoadingLayout(false);
      }
    }

    void loadSeatLayout();
    return () => { active = false; };
  }, [selectedTripId, selectedCoachNo]);

  // CSS classes map for seats layout
  const getSeatStyles = (status: string) => {
    if (status === "selected") return "bg-primary text-white shadow-md shadow-primary/20 scale-105 border-primary";
    if (status === "held") return "bg-yellow-100 border-yellow-300 text-yellow-800 font-bold";
    if (status === "confirmed") return "bg-slate-200 text-slate-500 cursor-not-allowed border-transparent";
    if (status === "blocked") return "bg-red-100 border-red-300 text-red-800 font-bold shadow-[0_0_8px_rgba(239,68,68,0.15)]";
    return "bg-white border border-outline-variant hover:border-primary text-on-surface hover:bg-slate-50/50";
  };

  const translateSeatType = (type: string) => {
    if (type === "ngoi_mem") return "Toa Ngồi mềm điều hòa";
    if (type === "giuong_nam_k6") return "Toa Giường nằm K6";
    return type;
  };

  const activeSuggestionsCount = gapSuggestions.length;
  const activeTrip = trips.find(t => t.trip_id === selectedTripId);

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-lg text-yellow-700 text-xs font-semibold">
          ⚠️ Cảnh báo: {error}
        </div>
      )}

      {/* Header Section */}
      <section className="flex flex-wrap justify-between items-center gap-4 border-b border-outline-variant/30 pb-4">
        <div>
          <h2 className="text-lg font-black text-on-surface">Giám sát và Phân bổ Chỗ ngồi</h2>
          <p className="text-xs text-on-surface-variant font-medium mt-0.5">
            Quản lý tồn kho ghế vật lý, thiết lập giới hạn quota chặng và cấu hình phân bổ doanh thu.
          </p>
        </div>
        <div className="flex gap-2">
          <button className="px-4 py-2 border border-outline-variant hover:bg-slate-50 text-on-surface font-bold rounded-lg transition-all text-xs cursor-pointer">
            Cấu hình Quota Chặng
          </button>
          <button className="px-4 py-2 bg-primary text-on-primary font-bold rounded-lg hover:brightness-110 transition-all text-xs shadow-md cursor-pointer">
            Tối ưu hóa Phân bổ
          </button>
        </div>
      </section>

      {/* Onboarding KPI Grid - Giải thích chức năng các cấu phần */}
      <section className="grid grid-cols-12 gap-4">
        <div className="col-span-12 sm:col-span-6 lg:col-span-3 bg-white border border-outline-variant rounded-xl p-4 shadow-sm hover:shadow transition-all flex flex-col justify-between">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-black text-slate-400 tracking-wider">Toa Tàu & Tải Trọng</span>
              <h4 className="text-xs font-black text-on-surface">Giám sát hệ số tải</h4>
              <p className="text-[10.5px] text-on-surface-variant/80 font-medium leading-relaxed mt-1">
                Theo dõi tỉ lệ lấp đầy (Occupancy %) thực tế trên từng toa tàu theo thời gian thực để phát hiện nhu cầu chặng.
              </p>
            </div>
            <span className="material-symbols-outlined text-primary bg-primary/5 p-1.5 rounded-lg text-lg">monitoring</span>
          </div>
          <div className="border-t border-slate-100 pt-2.5 mt-3 flex justify-between items-center text-[10px] font-bold text-primary">
            <span>Tải trung bình đoàn:</span>
            <span className="font-black text-xs">78.5%</span>
          </div>
        </div>

        <div className="col-span-12 sm:col-span-6 lg:col-span-3 bg-white border border-outline-variant rounded-xl p-4 shadow-sm hover:shadow transition-all flex flex-col justify-between">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-black text-slate-400 tracking-wider">Sơ Đồ Ghế Vật Lý</span>
              <h4 className="text-xs font-black text-on-surface">Quản lý trạng thái ghế</h4>
              <p className="text-[10.5px] text-on-surface-variant/80 font-medium leading-relaxed mt-1">
                Xem chi tiết sơ đồ ghế ngồi/giường nằm. Hỗ trợ khóa kỹ thuật hoặc mở khóa chỗ ngồi khi có yêu cầu nghiệp vụ.
              </p>
            </div>
            <span className="material-symbols-outlined text-primary bg-primary/5 p-1.5 rounded-lg text-lg">airline_seat_recline_normal</span>
          </div>
          <div className="border-t border-slate-100 pt-2.5 mt-3 flex justify-between items-center text-[10px] font-bold text-red-600">
            <span>Ghế đang khóa vận hành:</span>
            <span className="font-black text-xs">8 Ghế</span>
          </div>
        </div>

        <div className="col-span-12 sm:col-span-6 lg:col-span-3 bg-white border border-outline-variant rounded-xl p-4 shadow-sm hover:shadow transition-all flex flex-col justify-between">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-black text-slate-400 tracking-wider">Tồn Kho Phân Bổ</span>
              <h4 className="text-xs font-black text-on-surface">Điều tiết Quota chỗ</h4>
              <p className="text-[10.5px] text-on-surface-variant/80 font-medium leading-relaxed mt-1">
                Phân chia số ghế mở bán giữa chặng dài (Long-haul) và chặng ngắn (Short-haul) để tối đa doanh số ghế-km.
              </p>
            </div>
            <span className="material-symbols-outlined text-primary bg-primary/5 p-1.5 rounded-lg text-lg">analytics</span>
          </div>
          <div className="border-t border-slate-100 pt-2.5 mt-3 flex justify-between items-center text-[10px] font-bold text-green-600">
            <span>Tỉ lệ ưu tiên chặng dài:</span>
            <span className="font-black text-xs">80% / 20%</span>
          </div>
        </div>

        <div className="col-span-12 sm:col-span-6 lg:col-span-3 bg-white border border-l-4 border-primary border-y border-r rounded-xl p-4 shadow-sm hover:shadow transition-all flex flex-col justify-between">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-black text-primary tracking-wider">Cơ Hội Ghép Chặng AI</span>
              <h4 className="text-xs font-black text-on-surface">Đề xuất tối ưu ghép chặng</h4>
              <p className="text-[10.5px] text-on-surface-variant/80 font-medium leading-relaxed mt-1">
                AI tự động phát hiện các khoảng trống ngắn liền kề trên sơ đồ ghế để ghép thành chặng dài nguyên vẹn.
              </p>
            </div>
            <span className="material-symbols-outlined text-primary bg-primary/5 p-1.5 rounded-lg text-lg">auto_awesome</span>
          </div>
          <div className="border-t border-slate-100 pt-2.5 mt-3 flex justify-between items-center text-[10px] font-bold text-primary">
            <span>Khuyến nghị hoạt động:</span>
            <span className="font-black text-xs">+{activeSuggestionsCount} gợi ý</span>
          </div>
        </div>
      </section>

      {/* Selectors Bar - Bộ chọn Chuyến tàu và Ngày chạy */}
      <section className="bg-white border border-outline-variant rounded-xl p-5 shadow-sm">
        <h3 className="font-bold text-xs uppercase tracking-wider text-on-surface flex items-center gap-2 mb-4">
          <span className="material-symbols-outlined text-primary text-sm">settings_input_component</span>
          Bộ lọc Giám sát Hành trình
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-1">
            <label className="text-[10px] uppercase font-black text-slate-400 tracking-wider">
              Chọn Ngày đi
            </label>
            <select
              className="w-full bg-surface-container-low border border-outline-variant rounded-lg py-2 px-3 text-xs font-semibold outline-none focus:ring-1 focus:ring-primary cursor-pointer text-on-surface"
              value={selectedDate}
              onChange={(e) => {
                const newDate = e.target.value;
                setSelectedDate(newDate);
                const tripsForDate = trips.filter(t => t.service_date === newDate);
                if (tripsForDate.length > 0) {
                  setSelectedTripId(tripsForDate[0].trip_id);
                }
              }}
            >
              {Array.from(new Set(trips.map(t => t.service_date)))
                .sort((a, b) => b.localeCompare(a))
                .map((dateStr) => {
                  const [y, m, d] = dateStr.split("-");
                  return (
                    <option key={dateStr} value={dateStr}>
                      {`${d}/${m}/${y}`}
                    </option>
                  );
                })}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] uppercase font-black text-slate-400 tracking-wider">
              Chọn Chuyến tàu khả dụng
            </label>
            <select
              className="w-full bg-surface-container-low border border-outline-variant rounded-lg py-2 px-3 text-xs font-semibold outline-none focus:ring-1 focus:ring-primary cursor-pointer text-on-surface"
              value={selectedTripId ?? ""}
              onChange={(e) => setSelectedTripId(Number(e.target.value))}
            >
              {trips
                .filter((t) => t.service_date === selectedDate)
                .map((trip) => (
                  <option key={trip.trip_id} value={trip.trip_id}>
                    {trip.train_code} (Trip ID: #{trip.trip_id})
                  </option>
                ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => {
                loadInitialData();
              }}
              className="w-full py-2 bg-slate-100 hover:bg-slate-200/80 text-on-surface font-bold rounded-lg text-xs transition-all cursor-pointer flex items-center justify-center gap-1.5 border border-outline-variant/30"
            >
              <span className="material-symbols-outlined text-sm">refresh</span>
              Làm mới dữ liệu
            </button>
          </div>
        </div>
      </section>

      {/* Train Capacity Map (Full Width Visual) */}
      <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
        <h3 className="font-bold text-on-surface flex items-center gap-2 mb-4">
          <span className="material-symbols-outlined text-primary">train</span>
          Giám Sát Tải Trọng Đoàn Tàu: {activeTrip ? `Tàu Thống Nhất ${activeTrip.train_code}` : "Tàu Thống Nhất SE1"}
        </h3>
        <p className="text-xs text-on-surface-variant font-medium mb-6 -mt-3">
          Chọn từng toa bên dưới để kiểm tra sơ đồ ghế chi tiết và phân phối tồn kho chặng.
        </p>

        {loadingCoaches ? (
          <div className="h-20 rounded-xl bg-slate-100 animate-pulse flex items-center justify-center">
            <p className="text-xs text-on-surface-variant font-semibold">Đang tải danh sách toa...</p>
          </div>
        ) : (
          <div className="flex gap-2 overflow-x-auto pb-2 pt-1 custom-scrollbar select-none">
            {/* Locomotive Engine - Đồng bộ BookingScreen */}
            <div className="w-24 h-[70px] bg-slate-100 border border-slate-200 text-slate-400 rounded-lg flex flex-col items-center justify-center gap-1 shrink-0 select-none">
              <span className="material-symbols-outlined text-lg leading-none">train</span>
              <span className="text-[9px] font-black uppercase tracking-wider leading-none">ĐẦU TÀU</span>
            </div>

            {/* Coaches List - Đồng bộ BookingScreen */}
            {coaches.map((coach) => {
              const isActive = selectedCoachNo === coach.coach_no;
              const occupancyVal = parseInt(coach.occupancy.replace("%", "")) || 0;

              return (
                <div
                  key={coach.coach_no}
                  onClick={() => setSelectedCoachNo(coach.coach_no)}
                  className={`w-24 h-[70px] rounded-lg p-2 border flex flex-col justify-center items-center gap-0.5 cursor-pointer transition-all shrink-0 select-none ${
                    isActive
                      ? "ring-1 ring-primary border-primary bg-primary/5 font-bold"
                      : occupancyVal >= 100
                      ? "bg-slate-100/60 border-slate-200 text-slate-400"
                      : "bg-white border-outline-variant hover:bg-slate-50 text-on-surface-variant"
                  }`}
                >
                  <span className="text-[10px] font-black leading-none">TOA {coach.coach_no}</span>
                  <div className="flex flex-col items-center gap-0.5">
                    <span className="text-[8px] font-bold text-slate-400 leading-none">{coach.type}</span>
                    <span
                      className={`text-[9px] font-black leading-none mt-0.5 ${
                        occupancyVal >= 90
                          ? "text-red-500"
                          : occupancyVal >= 70
                          ? "text-green-600"
                          : "text-primary"
                      }`}
                    >
                      {coach.occupancy}
                    </span>
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
            Sơ Đồ Ghế Vật Lý Chi Tiết
          </h3>
          <p className="text-xs text-on-surface-variant font-medium mb-6">
            {seatPlan ? `${seatPlan.route} • Toa ${selectedCoachNo} (${translateSeatType(seatPlan.seat_type)})` : "Chọn toa tàu để xem chi tiết"}
          </p>

          {loadingLayout ? (
            <div className="h-48 rounded-2xl bg-slate-100 animate-pulse flex items-center justify-center">
              <p className="text-xs text-on-surface-variant font-semibold">Đang tải sơ đồ ghế...</p>
            </div>
          ) : seatPlan ? (
            <div className="border border-slate-200 rounded-2xl p-6 bg-slate-50/55 overflow-hidden w-full">
              {seatPlan.seat_type === "ngoi_mem" ? (
                /* Ghế ngồi mềm trải ngang có lối đi giữa - Đồng bộ BookingScreen */
                <div className="overflow-x-auto custom-scrollbar pb-2">
                  <div className="min-w-max p-4 flex flex-col gap-2 bg-white rounded-xl border border-slate-200">
                    {/* Hàng 1 (Dãy trên - ngoài cùng) */}
                    <div className="flex gap-2 justify-center">
                      {seatPlan.seats.map((row, rowIndex) => {
                        const seat = row[0];
                        const seatNum = rowIndex * 4 + 1;
                        return (
                          <button
                            key={`seat-${rowIndex}-0`}
                            className={`w-10 h-10 rounded-lg text-xs font-bold border flex items-center justify-center transition-all flex-shrink-0 cursor-default ${getSeatStyles(seat)}`}
                          >
                            {seatNum}
                          </button>
                        );
                      })}
                    </div>

                    {/* Hàng 2 (Dãy trên - phía trong) */}
                    <div className="flex gap-2 justify-center">
                      {seatPlan.seats.map((row, rowIndex) => {
                        const seat = row[1];
                        const seatNum = rowIndex * 4 + 2;
                        return (
                          <button
                            key={`seat-${rowIndex}-1`}
                            className={`w-10 h-10 rounded-lg text-xs font-bold border flex items-center justify-center transition-all flex-shrink-0 cursor-default ${getSeatStyles(seat)}`}
                          >
                            {seatNum}
                          </button>
                        );
                      })}
                    </div>

                    {/* Lối đi ở giữa */}
                    <div className="h-6 flex items-center relative my-1 bg-slate-200/50 rounded border-y border-slate-200/80 w-full">
                      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <span className="text-[9px] font-black uppercase tracking-[0.25em] text-slate-400">Lối đi</span>
                      </div>
                    </div>

                    {/* Hàng 3 (Dãy dưới - phía trong) */}
                    <div className="flex gap-2 justify-center">
                      {seatPlan.seats.map((row, rowIndex) => {
                        const seat = row[2];
                        const seatNum = rowIndex * 4 + 3;
                        return (
                          <button
                            key={`seat-${rowIndex}-2`}
                            className={`w-10 h-10 rounded-lg text-xs font-bold border flex items-center justify-center transition-all flex-shrink-0 cursor-default ${getSeatStyles(seat)}`}
                          >
                            {seatNum}
                          </button>
                        );
                      })}
                    </div>

                    {/* Hàng 4 (Dãy dưới - ngoài cùng) */}
                    <div className="flex gap-2 justify-center">
                      {seatPlan.seats.map((row, rowIndex) => {
                        const seat = row[3];
                        const seatNum = rowIndex * 4 + 4;
                        return (
                          <button
                            key={`seat-${rowIndex}-3`}
                            className={`w-10 h-10 rounded-lg text-xs font-bold border flex items-center justify-center transition-all flex-shrink-0 cursor-default ${getSeatStyles(seat)}`}
                          >
                            {seatNum}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ) : (
                /* Khoang Giường nằm K6 sửa lại đầy đủ 6 giường chia Dãy A & B đối xứng qua vách ngăn */
                <div className="w-full flex flex-col gap-2">
                  <div className="flex gap-4 overflow-x-auto pb-4 pt-1 custom-scrollbar">
                    {seatPlan.seats.map((cabinSeats, cabinIdx) => (
                      <div
                        key={cabinIdx}
                        className="bg-white border border-outline-variant rounded-xl p-4 min-w-[180px] flex flex-col gap-3 relative shadow-sm hover:shadow-md transition-all flex-shrink-0"
                      >
                        <div className="text-[10px] font-black text-primary border-b border-outline-variant/35 pb-1 text-center uppercase tracking-wider">
                          Phòng {cabinIdx + 1}
                        </div>

                        <div className="flex justify-between gap-3">
                          {/* Hàng A (Tầng 1, 2, 3 Trái) */}
                          <div className="flex flex-col gap-2">
                            <span className="text-[8px] font-black text-slate-400 text-center uppercase">Dãy A</span>
                            
                            <div className="flex flex-col items-center gap-0.5">
                              <span className="text-[7px] text-on-surface-variant/60 font-bold uppercase">A - Trên (T3)</span>
                              <button
                                type="button"
                                className={`w-10 h-8 rounded text-xs font-black border flex items-center justify-center transition-all cursor-default ${getSeatStyles(cabinSeats[4])}`}
                              >
                                {cabinIdx * 6 + 5}
                              </button>
                            </div>
                            
                            <div className="flex flex-col items-center gap-0.5">
                              <span className="text-[7px] text-on-surface-variant/60 font-bold uppercase">A - Giữa (T2)</span>
                              <button
                                type="button"
                                className={`w-10 h-8 rounded text-xs font-black border flex items-center justify-center transition-all cursor-default ${getSeatStyles(cabinSeats[2])}`}
                              >
                                {cabinIdx * 6 + 3}
                              </button>
                            </div>
                            
                            <div className="flex flex-col items-center gap-0.5">
                              <span className="text-[7px] text-on-surface-variant/60 font-bold uppercase">A - Dưới (T1)</span>
                              <button
                                type="button"
                                className={`w-10 h-8 rounded text-xs font-black border flex items-center justify-center transition-all cursor-default ${getSeatStyles(cabinSeats[0])}`}
                              >
                                {cabinIdx * 6 + 1}
                              </button>
                            </div>
                          </div>

                          {/* Vách ngăn chia giữa cabin */}
                          <div className="w-px border-r border-slate-100 my-2" />

                          {/* Hàng B (Tầng 1, 2, 3 Phải) */}
                          <div className="flex flex-col gap-2">
                            <span className="text-[8px] font-black text-slate-400 text-center uppercase">Dãy B</span>
                            
                            <div className="flex flex-col items-center gap-0.5">
                              <span className="text-[7px] text-on-surface-variant/60 font-bold uppercase">B - Trên (T3)</span>
                              <button
                                type="button"
                                className={`w-10 h-8 rounded text-xs font-black border flex items-center justify-center transition-all cursor-default ${getSeatStyles(cabinSeats[5])}`}
                              >
                                {cabinIdx * 6 + 6}
                              </button>
                            </div>
                            
                            <div className="flex flex-col items-center gap-0.5">
                              <span className="text-[7px] text-on-surface-variant/60 font-bold uppercase">B - Giữa (T2)</span>
                              <button
                                type="button"
                                className={`w-10 h-8 rounded text-xs font-black border flex items-center justify-center transition-all cursor-default ${getSeatStyles(cabinSeats[3])}`}
                              >
                                {cabinIdx * 6 + 4}
                              </button>
                            </div>
                            
                            <div className="flex flex-col items-center gap-0.5">
                              <span className="text-[7px] text-on-surface-variant/60 font-bold uppercase">B - Dưới (T1)</span>
                              <button
                                type="button"
                                className={`w-10 h-8 rounded text-xs font-black border flex items-center justify-center transition-all cursor-default ${getSeatStyles(cabinSeats[1])}`}
                              >
                                {cabinIdx * 6 + 2}
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Hành lang / Lối đi bên ngoài */}
                  <div className="flex items-center w-full mt-2 pt-3 border-t border-dashed border-slate-300">
                    <div className="text-[9px] uppercase tracking-widest text-on-surface-variant/50 font-black pl-3 flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-xs">directions_walk</span>
                      HÀNH LANG / LỐI ĐI
                    </div>
                    <div className="flex-grow border-t border-dashed border-slate-300/40 ml-4" />
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-center text-xs text-on-surface-variant py-12 font-semibold">Không có dữ liệu sơ đồ ghế.</p>
          )}
        </div>

        {/* Legend and Operations Panel */}
        <div className="col-span-12 lg:col-span-4 bg-white border border-outline-variant rounded-xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-sm text-on-surface mb-2 border-b border-outline-variant/30 pb-2">
              Chú Giải & Can Thiệp Quota
            </h3>
            <p className="text-[10px] text-on-surface-variant/75 font-semibold mb-4 leading-normal">
              Điều chỉnh trạng thái ghế để mở khóa bán chặng ngắn hoặc khóa bảo vệ giữ chỗ chặng dài.
            </p>

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

          <div className="space-y-2 pt-4 border-t border-slate-100">
            <button
              onClick={() => window.alert("Đã gửi yêu cầu điều chỉnh trạng thái ghế lên hệ thống vận hành.")}
              className="w-full py-2 bg-primary text-on-primary font-bold rounded-lg text-xs hover:brightness-110 active:scale-95 transition-all cursor-pointer shadow-sm"
            >
              Giữ hoặc mở khóa ghế
            </button>
            <button className="w-full py-2 border border-outline-variant text-on-surface hover:bg-slate-50/50 font-bold rounded-lg text-xs transition-all cursor-pointer">
              Ưu tiên bán nhóm ghế
            </button>
            <button className="w-full py-2 border border-outline-variant text-on-surface hover:bg-slate-50/50 font-bold rounded-lg text-xs transition-all cursor-pointer">
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
            <div>
              <h3 className="font-bold text-on-surface text-sm">Phân Bổ Tồn Kho Chỗ Ngồi Chặng</h3>
              <p className="text-[10px] text-on-surface-variant font-medium mt-0.5">
                Cơ cấu phân bổ số ghế bán chặng dài và chặng ngắn trên tàu.
              </p>
            </div>
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
                  <td className="px-6 py-4 font-mono text-xs text-on-surface">850.000 VND</td>
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
                  <td className="px-6 py-4 font-mono text-xs text-on-surface">220.000 VND</td>
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
                  <td className="px-6 py-4 font-mono text-xs text-on-surface">680.000 VND</td>
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
          <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm relative overflow-hidden">
            <div className="flex items-center gap-2 mb-2">
              <span className="material-symbols-outlined text-primary text-sm">auto_awesome</span>
              <h3 className="font-bold text-on-surface">Đề Xuất Ghép Chặng</h3>
            </div>
            <p className="text-[10px] text-on-surface-variant/80 mb-4 leading-relaxed font-semibold">
              AI tự động phân tích và đề xuất giải phóng các ghế chặng ngắn bị phân rã liền kề để ghép bán chặng dài có doanh thu cao hơn.
            </p>

            <div className="space-y-3">
              {gapSuggestions.length > 0 ? (
                gapSuggestions.map((item, idx) => (
                  <div className="p-3 bg-surface-container-low rounded-lg border border-primary/10 hover:border-primary/20 transition-all" key={idx}>
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-bold text-xs text-on-surface">{item.route}</span>
                      <span className="text-primary font-bold text-xs">{item.benefit}</span>
                    </div>
                    <p className="text-[11px] text-on-surface-variant leading-relaxed font-medium">
                      {item.reason} ({item.seatType === "ngoi_mem" ? "Ngồi mềm" : "Giường nằm"})
                    </p>
                    <button 
                      onClick={() => window.alert(`Đang áp dụng khuyến nghị ghép chặng cho ${item.route}`)}
                      className="mt-2 w-full py-1.5 bg-primary/10 text-primary font-bold text-[10px] rounded hover:bg-primary/20 transition-all cursor-pointer border border-transparent hover:border-primary/25"
                    >
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
