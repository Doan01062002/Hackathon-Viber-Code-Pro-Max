"use client";

import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/Button";
import { RouteMap } from "@/features/rail-ui/components/RouteMap";

type Station = "Hà Nội" | "Vinh" | "Huế" | "Đà Nẵng" | "Sài Gòn";

const coaches = [
  { id: "Toa 1", label: "Đầu tàu", type: "engine", display: "Đầu tàu", class: "" },
  { id: "Toa 2", label: "Toa 2 - Ghế", type: "seat", display: "Toa 2", class: "standard" },
  { id: "Toa 3", label: "Toa 3 - Ghế", type: "seat", display: "Toa 3", class: "standard" },
  { id: "Toa 4", label: "Toa 4 - Ghế", type: "seat", display: "Toa 4", class: "standard" },
  { id: "Toa 5", label: "Toa 5 - Giường", type: "sleeper", display: "Toa 5", class: "business" },
  { id: "Toa 6", label: "Toa 6 - Giường", type: "sleeper", display: "Toa 6", class: "business" },
  { id: "Toa 7", label: "Toa 7 - Ghế", type: "seat", display: "Toa 7", class: "standard" },
  { id: "Toa 8", label: "Toa 8 - Ghế", type: "seat", display: "Toa 8", class: "standard" },
];

export function BookingScreen() {
  const [origin, setOrigin] = useState<Station>("Hà Nội");
  const [destination, setDestination] = useState<Station>("Huế");
  const [date, setDate] = useState("2026-07-19");
  const [selectedCoach, setSelectedCoach] = useState("Toa 2");
  const [seatClass, setSeatClass] = useState<"standard" | "business">("standard");
  const [selectedSeats, setSelectedSeats] = useState<string[]>([]);

  // Sync seat class when coach changes
  useEffect(() => {
    const coach = coaches.find((c) => c.id === selectedCoach);
    if (coach && coach.class) {
      setSeatClass(coach.class as "standard" | "business");
    }
    setSelectedSeats([]); // Reset selected seats when changing coach
  }, [selectedCoach]);

  // Dynamic pricing based on selections
  const basePrices: Record<string, number> = {
    "Hà Nội-Vinh": 150000,
    "Hà Nội-Huế": 320000,
    "Hà Nội-Đà Nẵng": 450000,
    "Hà Nội-Sài Gòn": 980000,
    "Vinh-Huế": 180000,
    "Vinh-Đà Nẵng": 300000,
    "Huế-Đà Nẵng": 120000,
    "Huế-Sài Gòn": 680000,
    "Đà Nẵng-Sài Gòn": 550000,
  };

  const key = `${origin}-${destination}`;
  const inverseKey = `${destination}-${origin}`;
  const distancePrice = basePrices[key] || basePrices[inverseKey] || 250000;
  const isSleeper = coaches.find((c) => c.id === selectedCoach)?.type === "sleeper";
  const classMultiplier = isSleeper ? 1.8 : 1.0;
  
  // Total price = price per seat * number of selected seats
  const pricePerSeat = Math.round(distancePrice * classMultiplier);
  const totalDynamicPrice = pricePerSeat * selectedSeats.length;

  // Generate 33 seats (3 rows * 11 seats)
  const getSeats = () => {
    const rows = isSleeper ? ["T1", "T2", "T3"] : ["A", "B", "C"];
    const seatsList = [];
    for (const r of rows) {
      for (let i = 1; i <= 11; i++) {
        const id = `${r}${i}`;
        const code = id.charCodeAt(0) + id.charCodeAt(1) + selectedCoach.charCodeAt(selectedCoach.length - 1) + i;
        const status = code % 3 === 0 ? "booked" : "available";
        seatsList.push({ id, status });
      }
    }
    return seatsList;
  };

  const seats = getSeats();

  const handleSeatClick = (seatId: string, status: string) => {
    if (status === "booked") return;
    if (selectedSeats.includes(seatId)) {
      setSelectedSeats(selectedSeats.filter((id) => id !== seatId));
    } else {
      setSelectedSeats([...selectedSeats, seatId]);
    }
  };

  const formatVND = (value: number) =>
    new Intl.NumberFormat("vi-VN", {
      style: "currency",
      currency: "VND",
    }).format(value);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-12 gap-6">
        {/* Sơ đồ chỗ ngồi (Left Column) */}
        <section className="col-span-12 lg:col-span-8 space-y-6">
          {/* Visual Train Map Selector */}
          <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
            <h3 className="font-bold text-sm text-on-surface mb-3 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-sm">train</span>
              Sơ đồ đoàn tàu (Chọn toa)
            </h3>
            
            <div className="flex gap-1 w-full pt-1">
              {coaches.map((c) => {
                if (c.type === "engine") {
                  return (
                    <div
                      key={c.id}
                      className="flex-1 h-12 bg-slate-200 text-slate-500 rounded-l-xl flex flex-col items-center justify-center border border-slate-300 select-none"
                    >
                      <span className="material-symbols-outlined text-xs">speed</span>
                      <span className="text-[7px] font-extrabold uppercase mt-0.5">Đầu Tàu</span>
                    </div>
                  );
                }

                const isSelected = selectedCoach === c.id;
                const isSleeperCoach = c.type === "sleeper";

                return (
                  <button
                    key={c.id}
                    onClick={() => setSelectedCoach(c.id)}
                    className={`flex-1 h-12 rounded-lg p-1 flex flex-col justify-around items-center transition-all cursor-pointer ${
                      isSelected
                        ? "border-2 border-primary bg-primary/5 shadow-sm text-primary font-bold"
                        : "border border-outline-variant hover:bg-slate-50 text-on-surface-variant bg-white"
                    }`}
                  >
                    <span className="text-[8px] font-extrabold uppercase">{c.display}</span>
                    <span className="material-symbols-outlined text-lg leading-none">
                      {isSleeperCoach ? "hotel" : "chair"}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Detailed Seat Map */}
          <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
            <h3 className="font-bold text-sm text-on-surface mb-3 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-sm">airline_seat_recline_normal</span>
              Sơ đồ chỗ ngồi ({isSleeper ? "Toa Giường nằm" : "Toa Ghế ngồi"})
            </h3>

            <div className="flex gap-3 mb-4 text-[10px] font-semibold justify-center">
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 bg-white border border-outline-variant rounded" />
                Chỗ trống
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 bg-slate-300 rounded" />
                Đã đặt
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 bg-primary text-white rounded" />
                Đang chọn
              </div>
            </div>

            {/* Train Coach Container */}
            <div className="border-2 border-slate-300 rounded-2xl p-4 bg-slate-100/50 relative max-w-xl mx-auto flex items-stretch">
              <div className="absolute -left-2.5 top-1/2 -translate-y-1/2 w-2 h-8 bg-slate-400 rounded-l" />

              <div className="w-full flex flex-col gap-3 py-1 overflow-x-auto custom-scrollbar">
                {(isSleeper ? ["T1", "T2", "T3"] : ["A", "B", "C"]).map((rowId, index) => (
                  <React.Fragment key={rowId}>
                    {/* Render Aisle Line between row 2 and 3 */}
                    {index === 2 && (
                      <div className="flex items-center min-w-[480px] my-1">
                        <div className="w-10 flex-shrink-0 text-[8px] uppercase tracking-widest text-on-surface-variant/40 font-bold pl-1">
                          Lối đi
                        </div>
                        <div className="flex-grow border-t border-dashed border-slate-300" />
                      </div>
                    )}

                    <div className="flex flex-row justify-between items-center gap-2 min-w-[480px]">
                      <span className="text-[10px] font-extrabold text-on-surface-variant opacity-60 w-10 flex-shrink-0">
                        {isSleeper ? `Tầng ${rowId.slice(-1)}` : `Hàng ${rowId}`}
                      </span>
                      <div className="flex-grow flex justify-between gap-1">
                        {seats
                          .filter((s) => s.id.startsWith(rowId))
                          .map((seat) => {
                            const isSelected = selectedSeats.includes(seat.id);
                            const isBooked = seat.status === "booked";
                            const seatNum = seat.id.replace(rowId, "");

                            return (
                              <button
                                key={seat.id}
                                disabled={isBooked}
                                onClick={() => handleSeatClick(seat.id, seat.status)}
                                className={`w-8 h-8 rounded-md font-bold text-[9px] flex items-center justify-center transition-all flex-shrink-0 ${
                                  isBooked
                                    ? "bg-slate-300 text-slate-500 cursor-not-allowed border border-transparent"
                                    : isSelected
                                    ? "bg-primary text-white shadow-md shadow-primary/20 scale-105"
                                    : "bg-white border border-outline-variant hover:border-primary text-on-surface"
                                }`}
                              >
                                {seatNum}
                              </button>
                            );
                          })}
                      </div>
                    </div>
                  </React.Fragment>
                ))}
              </div>

              <div className="absolute -right-2.5 top-1/2 -translate-y-1/2 w-2 h-8 bg-slate-400 rounded-r" />
            </div>
          </div>

          {/* Route Map */}
          <RouteMap title="Bản đồ tải chặng thời gian thực (Gợi ý cho hành khách)" />
        </section>

        {/* Right Column (Search & Details stacked) */}
        <aside className="col-span-12 lg:col-span-4 space-y-6">
          {/* Tìm kiếm hành trình */}
          <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
            <h3 className="font-bold text-sm text-on-surface mb-3 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-sm">search</span>
              Tìm kiếm hành trình
            </h3>

            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <label className="text-[9px] uppercase font-bold tracking-wider text-on-surface-variant">Ga đi</label>
                  <select
                    value={origin}
                    onChange={(e) => setOrigin(e.target.value as Station)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-lg py-1.5 px-2 text-xs font-semibold outline-none focus:ring-1 focus:ring-primary"
                  >
                    <option value="Hà Nội">Hà Nội</option>
                    <option value="Vinh">Vinh</option>
                    <option value="Huế">Huế</option>
                    <option value="Đà Nẵng">Đà Nẵng</option>
                    <option value="Sài Gòn">Sài Gòn</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[9px] uppercase font-bold tracking-wider text-on-surface-variant">Ga đến</label>
                  <select
                    value={destination}
                    onChange={(e) => setDestination(e.target.value as Station)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-lg py-1.5 px-2 text-xs font-semibold outline-none focus:ring-1 focus:ring-primary"
                  >
                    <option value="Hà Nội">Hà Nội</option>
                    <option value="Vinh">Vinh</option>
                    <option value="Huế">Huế</option>
                    <option value="Đà Nẵng">Đà Nẵng</option>
                    <option value="Sài Gòn">Sài Gòn</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[9px] uppercase font-bold tracking-wider text-on-surface-variant">Ngày đi</label>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full bg-surface-container-low border border-outline-variant rounded-lg py-1.5 px-2 text-xs font-semibold outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </div>
          </div>

          {/* Chi tiết vé đặt */}
          <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
            <h3 className="font-bold text-sm text-on-surface mb-3 flex items-center gap-2 border-b border-outline-variant/30 pb-2">
              <span className="material-symbols-outlined text-primary text-sm">shopping_bag</span>
              Chi tiết vé đặt
            </h3>

            <div className="space-y-3 text-xs font-semibold">
              <div className="flex justify-between items-center py-1 border-b border-outline-variant/20">
                <span className="text-on-surface-variant font-medium">Hành trình</span>
                <span className="text-on-surface">{origin} → {destination}</span>
              </div>

              <div className="flex justify-between items-center py-1 border-b border-outline-variant/20">
                <span className="text-on-surface-variant font-medium">Ngày khởi hành</span>
                <span className="text-on-surface">{date}</span>
              </div>

              <div className="flex justify-between items-center py-1 border-b border-outline-variant/20">
                <span className="text-on-surface-variant font-medium">Số hiệu Toa</span>
                <span className="text-on-surface font-bold text-primary">{selectedCoach}</span>
              </div>

              <div className="flex justify-between items-center py-1 border-b border-outline-variant/20">
                <span className="text-on-surface-variant font-medium">Loại vé</span>
                <span className="text-on-surface uppercase font-bold text-[10px]">
                  {isSleeper ? "Giường nằm" : "Ghế thường"}
                </span>
              </div>

              <div className="flex justify-between items-start py-1 border-b border-outline-variant/20">
                <span className="text-on-surface-variant font-medium mt-0.5">Số lượng chỗ ({selectedSeats.length})</span>
                <div className="text-right">
                  {selectedSeats.length > 0 ? (
                    <div className="flex flex-wrap gap-1 justify-end max-w-[200px]">
                      {selectedSeats.map((seatId) => {
                        const num = seatId.replace(/[A-C]|T\d/, "");
                        const label = isSleeper ? `Giường ${num} (T${seatId.slice(1, 2)})` : `Ghế ${num} (${seatId.slice(0, 1)})`;
                        return (
                          <span key={seatId} className="bg-primary/10 text-primary px-1.5 py-0.5 rounded text-[9px] font-bold">
                            {label}
                          </span>
                        );
                      })}
                    </div>
                  ) : (
                    <span className="text-outline">Chưa chọn</span>
                  )}
                </div>
              </div>

              <div className="flex justify-between items-end pt-2 pb-1">
                <span className="text-on-surface-variant font-bold">Tổng tiền</span>
                <div className="text-right">
                  <span className="text-lg font-black text-primary font-mono">
                    {totalDynamicPrice.toLocaleString("vi-VN")}
                  </span>
                  <span className="text-[10px] font-bold text-on-surface-variant ml-0.5">VNĐ</span>
                </div>
              </div>

              <Button className="w-full py-2.5 mt-2 text-xs" disabled={selectedSeats.length === 0}>
                Xác nhận & Thanh toán
              </Button>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
