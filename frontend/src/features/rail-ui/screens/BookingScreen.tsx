"use client";

import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/Button";

type Station = "Hà Nội" | "Vinh" | "Huế" | "Đà Nẵng" | "Sài Gòn";

const coaches = [
  { id: "Toa 1", label: "Đầu tàu", type: "engine", display: "Đầu tàu", class: "" },
  { id: "Toa 2", label: "Toa 2 - Ghế ngồi", type: "seat", display: "Toa 2", class: "standard" },
  { id: "Toa 3", label: "Toa 3 - Ghế ngồi", type: "seat", display: "Toa 3", class: "standard" },
  { id: "Toa 4", label: "Toa 4 - Ghế ngồi", type: "seat", display: "Toa 4", class: "standard" },
  { id: "Toa 5", label: "Toa 5 - Giường nằm", type: "sleeper", display: "Toa 5", class: "business" },
  { id: "Toa 6", label: "Toa 6 - Giường nằm", type: "sleeper", display: "Toa 6", class: "business" },
  { id: "Toa 7", label: "Toa 7 - Ghế ngồi", type: "seat", display: "Toa 7", class: "standard" },
  { id: "Toa 8", label: "Toa 8 - Ghế ngồi", type: "seat", display: "Toa 8", class: "standard" },
];

export function BookingScreen() {
  const [origin, setOrigin] = useState<Station>("Hà Nội");
  const [destination, setDestination] = useState<Station>("Huế");
  const [date, setDate] = useState("2026-07-19");
  const [selectedCoach, setSelectedCoach] = useState("Toa 2");
  const [seatClass, setSeatClass] = useState<"standard" | "business">("standard");
  const [selectedSeat, setSelectedSeat] = useState<string | null>(null);

  // Sync seat class when coach changes
  useEffect(() => {
    const coach = coaches.find((c) => c.id === selectedCoach);
    if (coach && coach.class) {
      setSeatClass(coach.class as "standard" | "business");
    }
    setSelectedSeat(null); // Reset selected seat when changing coach
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
  const dynamicPrice = Math.round(distancePrice * classMultiplier);

  // Generate 33 seats deterministically (3 rows * 11 seats)
  const getSeats = () => {
    const rows = isSleeper ? ["T1", "T2", "T3"] : ["A", "B", "C"];
    const seatsList = [];
    for (const r of rows) {
      for (let i = 1; i <= 11; i++) {
        const id = `${r}${i}`;
        // Deterministic seat booking status
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
    setSelectedSeat(selectedSeat === seatId ? null : seatId);
  };

  return (
    <div className="grid grid-cols-12 gap-6 max-w-5xl mx-auto">
      {/* Selection Panel (Left Column) */}
      <div className="col-span-12 lg:col-span-7 space-y-6">
        {/* Search Route */}
        <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
          <h3 className="font-extrabold text-lg text-on-surface mb-6 flex items-center gap-2">
            <span className="material-symbols-outlined text-primary">search</span>
            Tìm kiếm hành trình
          </h3>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant">Ga đi</label>
              <select
                value={origin}
                onChange={(e) => setOrigin(e.target.value as Station)}
                className="w-full bg-surface-container-low border border-outline-variant rounded-lg p-2.5 text-sm font-semibold outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="Hà Nội">Hà Nội</option>
                <option value="Vinh">Vinh</option>
                <option value="Huế">Huế</option>
                <option value="Đà Nẵng">Đà Nẵng</option>
                <option value="Sài Gòn">Sài Gòn</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant">Ga đến</label>
              <select
                value={destination}
                onChange={(e) => setDestination(e.target.value as Station)}
                className="w-full bg-surface-container-low border border-outline-variant rounded-lg p-2.5 text-sm font-semibold outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="Hà Nội">Hà Nội</option>
                <option value="Vinh">Vinh</option>
                <option value="Huế">Huế</option>
                <option value="Đà Nẵng">Đà Nẵng</option>
                <option value="Sài Gòn">Sài Gòn</option>
              </select>
            </div>

            <div className="space-y-1 col-span-2">
              <label className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant">Ngày đi</label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full bg-surface-container-low border border-outline-variant rounded-lg p-2.5 text-sm font-semibold outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
        </div>

        {/* Coach and Seat Selection Panel */}
        <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm">
          {/* Visual Train Map Selector */}
          <div className="mb-6">
            <h3 className="font-extrabold text-lg text-on-surface mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">train</span>
              Sơ đồ đoàn tàu (Chọn toa để chọn chỗ)
            </h3>
            
            <div className="flex gap-2 overflow-x-auto pb-4 pt-1 custom-scrollbar">
              {coaches.map((c) => {
                if (c.type === "engine") {
                  return (
                    <div
                      key={c.id}
                      className="min-w-[90px] h-16 bg-slate-200 text-slate-500 rounded-l-2xl flex flex-col items-center justify-center border border-slate-300 select-none"
                    >
                      <span className="material-symbols-outlined text-lg">speed</span>
                      <span className="text-[9px] font-extrabold mt-1 uppercase">Đầu Tàu</span>
                    </div>
                  );
                }

                const isSelected = selectedCoach === c.id;
                const isSleeperCoach = c.type === "sleeper";

                return (
                  <button
                    key={c.id}
                    onClick={() => setSelectedCoach(c.id)}
                    className={`min-w-[90px] h-16 rounded-lg p-1.5 flex flex-col justify-between items-center transition-all cursor-pointer ${
                      isSelected
                        ? "border-2 border-primary bg-primary/5 shadow-sm text-primary font-bold"
                        : "border border-outline-variant hover:bg-slate-50 text-on-surface-variant bg-white"
                    }`}
                  >
                    <span className="text-[10px] font-extrabold uppercase">{c.display}</span>
                    <span className="material-symbols-outlined text-sm">
                      {isSleeperCoach ? "hotel" : "chair"}
                    </span>
                    <span className="text-[8px] font-bold leading-none">
                      {isSleeperCoach ? "Giường nằm" : "Ghế ngồi"}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          <h3 className="font-extrabold text-lg text-on-surface mb-4 flex items-center gap-2">
            <span className="material-symbols-outlined text-primary">airline_seat_recline_normal</span>
            Sơ đồ chi tiết chỗ ngồi (Toa 33 chỗ: 3 hàng &times; 11 cột)
          </h3>

          <div className="flex gap-4 mb-6 text-xs font-semibold justify-center">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-white border border-outline-variant rounded" />
              Chỗ trống
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-slate-300 rounded" />
              Đã đặt
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-primary text-white rounded flex items-center justify-center" />
              Đang chọn
            </div>
          </div>

          {/* Train Coach Container */}
          <div className="border-2 border-slate-300 rounded-2xl p-4 bg-slate-100/50 relative max-w-2xl mx-auto flex items-stretch">
            {/* Left Coupler/Connector */}
            <div className="absolute -left-2.5 top-1/2 -translate-y-1/2 w-2 h-10 bg-slate-400 rounded-l" />

            {/* Coach Cabin Inner */}
            <div className="w-full flex flex-col gap-4 py-2 overflow-x-auto custom-scrollbar">
              {(isSleeper ? ["T1", "T2", "T3"] : ["A", "B", "C"]).map((rowId) => (
                <div key={rowId} className="flex flex-row justify-between items-center gap-2 min-w-[550px]">
                  {/* Row Label */}
                  <span className="text-xs font-extrabold text-on-surface-variant opacity-60 w-12 flex-shrink-0">
                    {isSleeper ? `Tầng ${rowId.slice(-1)}` : `Hàng ${rowId}`}
                  </span>
                  {/* Seats Grid horizontal */}
                  <div className="flex-grow flex justify-between gap-1">
                    {seats
                      .filter((s) => s.id.startsWith(rowId))
                      .map((seat) => {
                        const isSelected = selectedSeat === seat.id;
                        const isBooked = seat.status === "booked";
                        const seatNum = seat.id.replace(rowId, "");

                        return (
                          <button
                            key={seat.id}
                            disabled={isBooked}
                            onClick={() => handleSeatClick(seat.id, seat.status)}
                            className={`w-9 h-9 rounded-md font-bold text-[10px] flex items-center justify-center transition-all flex-shrink-0 ${
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
              ))}
            </div>

            {/* Right Coupler/Connector */}
            <div className="absolute -right-2.5 top-1/2 -translate-y-1/2 w-2 h-10 bg-slate-400 rounded-r" />
          </div>
        </div>
      </div>

      {/* Booking Summary Card (Right Column) */}
      <div className="col-span-12 lg:col-span-5">
        <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm sticky top-24">
          <h3 className="font-extrabold text-lg text-on-surface mb-6 flex items-center gap-2 border-b border-outline-variant/30 pb-4">
            <span className="material-symbols-outlined text-primary">shopping_bag</span>
            Chi tiết vé đặt
          </h3>

          <div className="space-y-4 text-sm font-semibold">
            <div className="flex justify-between items-center py-2 border-b border-outline-variant/20">
              <span className="text-on-surface-variant font-medium">Hành trình</span>
              <span className="text-on-surface">{origin} → {destination}</span>
            </div>

            <div className="flex justify-between items-center py-2 border-b border-outline-variant/20">
              <span className="text-on-surface-variant font-medium">Ngày khởi hành</span>
              <span className="text-on-surface">{date}</span>
            </div>

            <div className="flex justify-between items-center py-2 border-b border-outline-variant/20">
              <span className="text-on-surface-variant font-medium">Số hiệu Toa</span>
              <span className="text-on-surface font-extrabold text-primary">{selectedCoach}</span>
            </div>

            <div className="flex justify-between items-center py-2 border-b border-outline-variant/20">
              <span className="text-on-surface-variant font-medium">Loại vé</span>
              <span className="text-on-surface uppercase font-bold text-xs">
                {isSleeper ? "Giường nằm" : "Ghế ngồi thường"}
              </span>
            </div>

            <div className="flex justify-between items-center py-2 border-b border-outline-variant/20">
              <span className="text-on-surface-variant font-medium">Chỗ ngồi chọn</span>
              <span className="text-primary font-bold text-base">
                {selectedSeat
                  ? (isSleeper ? `Giường ${selectedSeat.replace(/T\d/, "")} (Tầng ${selectedSeat.slice(1, 2)})` : `Ghế ${selectedSeat.replace(/[A-C]/, "")} (Hàng ${selectedSeat.slice(0, 1)})`)
                  : "Chưa chọn"}
              </span>
            </div>

            <div className="flex justify-between items-end pt-4 pb-2">
              <span className="text-on-surface-variant font-bold text-base">Tổng tiền</span>
              <div className="text-right">
                <span className="text-2xl font-black text-primary font-mono">
                  {dynamicPrice.toLocaleString("vi-VN")}
                </span>
                <span className="text-xs font-bold text-on-surface-variant ml-1">VNĐ</span>
              </div>
            </div>

            <Button className="w-full py-4 mt-6 text-sm" disabled={!selectedSeat}>
              Xác nhận đặt vé & Thanh toán
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
