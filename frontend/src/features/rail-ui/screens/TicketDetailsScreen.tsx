"use client";

import { useState } from "react";
import { apiClient } from "@/lib/api/client";

export function TicketDetailsScreen() {
  const [bookingCode, setBookingCode] = useState<string>("SE3-COMBINED");
  const [searched, setSearched] = useState<boolean>(true);
  const [ticketDetail, setTicketDetail] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    const cleanCode = bookingCode.trim();
    if (!cleanCode) return;

    setSearched(true);
    setLoading(true);
    setError(null);
    setTicketDetail(null);

    // Bypass real API if it's the demo booking code
    if (cleanCode === "SE3-COMBINED") {
      setLoading(false);
      return;
    }

    try {
      const data = await apiClient.get<any>(`/api/v1/booking/code/${cleanCode}`);
      setTicketDetail(data);
    } catch (err: any) {
      console.warn("Không tìm thấy mã đặt vé trong DB backend:", err);
      setError("Không tìm thấy mã đặt vé này trong hệ thống cơ sở dữ liệu.");
    } finally {
      setLoading(false);
    }
  };

  // Demo ticket data representing a combined journey
  const demoTicket = {
    code: "SE3-COMBINED",
    passenger: "Nguyễn Văn Hùng",
    train: "SE3",
    date: "19/07/2026",
    route: "Hà Nội (HAN) → Đà Nẵng (DAD)",
    totalPrice: 850000,
    isCombined: true,
    legs: [
      {
        id: 1,
        leg: "Hà Nội → Vinh",
        time: "19:30 (19/07) - 00:15 (20/07)",
        coach: "Toa 02",
        type: "Giường nằm K6",
        seatNo: "Giường 03 (Tầng 2 - Dãy A)",
        status: "Đã xác nhận",
      },
      {
        id: 2,
        leg: "Vinh → Đà Nẵng",
        time: "00:25 (20/07) - 06:10 (20/07)",
        coach: "Toa 02",
        type: "Giường nằm K6",
        seatNo: "Giường 03 (Tầng 2 - Dãy A) [Giữ nguyên chỗ]",
        status: "Đã xác nhận",
        note: "✦ Bạn không cần đổi giường/toa tại ga Vinh. Chỗ ngồi đã được AI tự động gộp liên mạch suốt chặng.",
      },
    ],
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-outline-variant rounded-2xl p-6 shadow-sm">
        <h2 className="text-xl font-black text-on-surface flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-2xl">confirmation_number</span>
          Tra Cứu Vé & Chi Tiết Hành Trình
        </h2>
        <p className="text-xs text-on-surface-variant font-medium mt-1">
          Nhập mã đặt vé của bạn để kiểm tra chi tiết chỗ ngồi, vé chặng ghép (nếu có) và hướng dẫn di chuyển giữa các chặng.
        </p>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Lookup form */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          <div className="bg-white border border-outline-variant rounded-2xl p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-sm text-on-surface flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-sm">search</span>
              Tra cứu đặt vé
            </h3>
            <div className="space-y-1">
              <label className="text-[10px] uppercase font-bold text-on-surface-variant">Mã đặt vé (Booking Code)</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={bookingCode}
                  onChange={(e) => setBookingCode(e.target.value.toUpperCase())}
                  placeholder="Ví dụ: SE3-COMBINED"
                  className="flex-grow rounded-lg border border-outline-variant bg-surface-container-low px-3 py-2 text-xs font-semibold uppercase focus:outline-none focus:border-primary"
                />
                <button
                  onClick={handleSearch}
                  disabled={loading}
                  className="px-4 py-2 bg-primary hover:bg-primary/95 text-white font-bold text-xs rounded-lg transition-all cursor-pointer flex items-center justify-center min-w-[60px]"
                >
                  {loading ? (
                    <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  ) : (
                    "Tìm"
                  )}
                </button>
              </div>
            </div>
            <p className="text-[10px] text-on-surface-variant/70 leading-relaxed">
              Mẹo: Nhập mã <code className="bg-slate-100 px-1 py-0.5 rounded font-mono font-bold text-primary">SE3-COMBINED</code> để xem mô phỏng vé ghép chặng tự động tối ưu của AI.
            </p>
          </div>

          {/* AI Helper Card */}
          <div className="bg-gradient-to-br from-primary/5 to-brand-soft border border-primary/20 rounded-2xl p-5 shadow-sm space-y-3">
            <h4 className="font-black text-xs text-primary flex items-center gap-1.5">
              <span className="material-symbols-outlined text-sm">auto_awesome</span>
              Về Vé Ghép Chặng AI
            </h4>
            <p className="text-[11px] text-on-surface-variant leading-relaxed font-semibold">
              Để đáp ứng nhu cầu đi lại chặng dài khi hết vé suốt, hệ thống tự động tìm kiếm các đoạn ghế trống trên các chuyến tàu và ghép thành một hành trình đi suốt. Bạn có thể:
            </p>
            <ul className="text-[10.5px] text-on-surface-variant/90 space-y-1.5 list-disc pl-4 font-medium">
              <li>Ngồi nguyên một chỗ nếu 2 chặng liên tiếp trống cùng ghế.</li>
              <li>Chỉ di chuyển chỗ ngồi tại các ga trung gian trung chuyển nếu có sự thay đổi ghế (được ghi rõ trong chi tiết vé).</li>
            </ul>
          </div>
        </div>

        {/* Ticket Details Display */}
        <div className="col-span-12 lg:col-span-8">
          {ticketDetail ? (
            <div className="bg-white border border-outline-variant rounded-2xl shadow-sm overflow-hidden animate-fade-in">
              {/* Premium Ticket Header */}
              <div className="bg-primary text-white p-6 flex justify-between items-center">
                <div>
                  <span className="px-2.5 py-0.5 bg-white/20 text-white text-[9px] font-black rounded-full uppercase tracking-wider">
                    Vé Tàu Hỏa Chính Thức
                  </span>
                  <h3 className="text-lg font-black mt-1.5">{ticketDetail.origin_name} ({ticketDetail.origin_code}) → {ticketDetail.destination_name} ({ticketDetail.destination_code})</h3>
                  <p className="text-xs opacity-90 font-medium mt-0.5">Tàu {ticketDetail.train_code} • Ngày đi: {ticketDetail.service_date}</p>
                </div>
                <div className="text-right">
                  <span className="text-[10px] uppercase font-bold tracking-wider opacity-75">Mã đặt vé</span>
                  <p className="text-xl font-black font-mono tracking-widest">{ticketDetail.booking_code}</p>
                </div>
              </div>

              {/* Ticket Body */}
              <div className="p-6 space-y-6">
                {/* Passenger details row */}
                <div className="grid grid-cols-3 gap-4 border-b border-outline-variant/30 pb-4 text-xs font-semibold">
                  <div>
                    <span className="text-on-surface-variant font-bold block mb-0.5">Mã đặt vé hệ thống</span>
                    <span className="font-black text-on-surface text-sm">#{ticketDetail.booking_id}</span>
                  </div>
                  <div>
                    <span className="text-on-surface-variant font-bold block mb-0.5">Giá vé đã trả</span>
                    <span className="font-black text-primary text-sm font-mono">
                      {new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(ticketDetail.booked_price)}
                    </span>
                  </div>
                  <div>
                    <span className="text-on-surface-variant font-bold block mb-0.5">Trạng thái</span>
                    <span className="px-2 py-0.5 bg-green-50 text-green-700 font-black rounded-full uppercase text-[9px] border border-green-200">
                      {ticketDetail.status}
                    </span>
                  </div>
                </div>

                {/* Seats detail */}
                <div className="space-y-4">
                  <h4 className="text-xs font-black text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-sm text-primary">event_seat</span>
                    Vị Trí Chỗ Ngồi Chi Tiết
                  </h4>

                  <div className="bg-slate-50 border border-slate-100 rounded-lg p-4 grid grid-cols-3 gap-4 text-xs font-semibold">
                    <div>
                      <span className="text-slate-400 block font-bold">Toa Tàu</span>
                      <span className="font-black text-slate-700 text-sm">Toa {ticketDetail.coach_no || "01"}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block font-bold">Loại chỗ</span>
                      <span className="font-black text-slate-700 text-sm">
                        {ticketDetail.seat_type === "giuong_nam_k6" ? "Giường nằm K6" : "Ngồi mềm điều hòa"}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block font-bold">Vị Trí Chỗ</span>
                      <span className="font-black text-primary text-sm">Ghế/Giường {ticketDetail.seat_no || "Chưa xếp"}</span>
                    </div>
                  </div>
                </div>

                {/* Ticket Footer / Barcode */}
                <div className="border-t border-dashed border-outline-variant/60 pt-6 flex flex-col items-center gap-4">
                  <div className="flex flex-col items-center gap-1 select-none">
                    <div className="flex items-center justify-center gap-[1.5px] h-12">
                      <div className="w-[1.5px] h-full bg-slate-800"></div>
                      <div className="w-[3px] h-full bg-slate-800"></div>
                      <div className="w-[1px] h-full bg-slate-800"></div>
                      <div className="w-[4px] h-full bg-slate-800"></div>
                      <div className="w-[1.5px] h-full bg-slate-800"></div>
                      <div className="w-[1px] h-full bg-slate-800"></div>
                      <div className="w-[2px] h-full bg-slate-800"></div>
                      <div className="w-[4px] h-full bg-slate-800"></div>
                      <div className="w-[1.5px] h-full bg-slate-800"></div>
                      <div className="w-[3px] h-full bg-slate-800"></div>
                    </div>
                    <span className="text-[10px] font-bold text-slate-400 font-mono tracking-widest">
                      *{ticketDetail.booking_code}*
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 text-center font-bold">
                    Vé tàu hỏa điện tử được đồng bộ thời gian thực từ cơ sở dữ liệu hệ thống SRRM.
                  </p>
                </div>
              </div>
            </div>
          ) : searched && bookingCode === "SE3-COMBINED" ? (
            <div className="bg-white border border-outline-variant rounded-2xl shadow-sm overflow-hidden">
              {/* Premium Ticket Header */}
              <div className="bg-primary text-white p-6 flex justify-between items-center">
                <div>
                  <span className="px-2.5 py-0.5 bg-white/20 text-white text-[9px] font-black rounded-full uppercase tracking-wider">
                    Vé Ghép Chặng Tối Ưu (AI Combined)
                  </span>
                  <h3 className="text-lg font-black mt-1.5">{demoTicket.route}</h3>
                  <p className="text-xs opacity-90 font-medium mt-0.5">Tàu {demoTicket.train} • Ngày đi: {demoTicket.date}</p>
                </div>
                <div className="text-right">
                  <span className="text-[10px] uppercase font-bold tracking-wider opacity-75">Mã đặt vé</span>
                  <p className="text-xl font-black font-mono tracking-widest">{demoTicket.code}</p>
                </div>
              </div>

              {/* Ticket Body */}
              <div className="p-6 space-y-6">
                {/* Passenger details row */}
                <div className="grid grid-cols-3 gap-4 border-b border-outline-variant/30 pb-4 text-xs">
                  <div>
                    <span className="text-on-surface-variant font-bold block mb-0.5">Hành khách</span>
                    <span className="font-black text-on-surface text-sm">{demoTicket.passenger}</span>
                  </div>
                  <div>
                    <span className="text-on-surface-variant font-bold block mb-0.5">Giá vé gộp</span>
                    <span className="font-black text-primary text-sm font-mono">
                      {new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(demoTicket.totalPrice)}
                    </span>
                  </div>
                  <div>
                    <span className="text-on-surface-variant font-bold block mb-0.5">Trạng thái</span>
                    <span className="px-2 py-0.5 bg-green-50 text-green-700 font-black rounded-full uppercase text-[9px] border border-green-200">
                      Đã thanh toán
                    </span>
                  </div>
                </div>

                {/* Combined legs breakdown */}
                <div className="space-y-4">
                  <h4 className="text-xs font-black text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-sm text-primary">route</span>
                    Chi Tiết Hành Trình Từng Phân Đoạn
                  </h4>

                  <div className="relative border-l-2 border-primary/20 ml-3.5 pl-6 space-y-6">
                    {demoTicket.legs.map((legItem, idx) => (
                      <div key={legItem.id} className="relative">
                        {/* Dot Indicator */}
                        <div className="absolute -left-[31px] top-1.5 w-4.5 h-4.5 rounded-full border-4 border-white bg-primary shadow-sm flex items-center justify-center">
                          <span className="w-1.5 h-1.5 bg-white rounded-full"></span>
                        </div>

                        <div className="space-y-1.5">
                          <div className="flex justify-between items-center">
                            <span className="font-black text-xs text-on-surface">
                              Chặng {legItem.id}: {legItem.leg}
                            </span>
                            <span className="px-2 py-0.5 bg-primary/10 text-primary text-[10px] font-black rounded uppercase">
                              {legItem.status}
                            </span>
                          </div>
                          <p className="text-[11px] text-on-surface-variant/80 font-bold">Thời gian: {legItem.time}</p>
                          <div className="bg-slate-50 border border-slate-100 rounded-lg p-3 grid grid-cols-3 gap-2 text-[11px]">
                            <div>
                              <span className="text-slate-400 block font-bold">Toa</span>
                              <span className="font-black text-slate-700">{legItem.coach}</span>
                            </div>
                            <div>
                              <span className="text-slate-400 block font-bold">Loại chỗ</span>
                              <span className="font-black text-slate-700">{legItem.type}</span>
                            </div>
                            <div>
                              <span className="text-slate-400 block font-bold">Vị trí giường</span>
                              <span className="font-black text-primary">{legItem.seatNo}</span>
                            </div>
                          </div>
                          {legItem.note && (
                            <p className="text-[10px] text-green-700 font-extrabold italic bg-green-50/50 p-2 rounded border border-green-100">
                              {legItem.note}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Ticket Footer / Barcode */}
                <div className="border-t border-dashed border-outline-variant/60 pt-6 flex flex-col items-center gap-4">
                  <div className="flex flex-col items-center gap-1 select-none">
                    {/* Simulated Barcode */}
                    <div className="flex items-center justify-center gap-[1.5px] h-12">
                      <div className="w-[1.5px] h-full bg-slate-800"></div>
                      <div className="w-[3px] h-full bg-slate-800"></div>
                      <div className="w-[1px] h-full bg-slate-800"></div>
                      <div className="w-[4px] h-full bg-slate-800"></div>
                      <div className="w-[1.5px] h-full bg-slate-800"></div>
                      <div className="w-[1px] h-full bg-slate-800"></div>
                      <div className="w-[2px] h-full bg-slate-800"></div>
                      <div className="w-[4px] h-full bg-slate-800"></div>
                      <div className="w-[1px] h-full bg-slate-800"></div>
                      <div className="w-[3px] h-full bg-slate-800"></div>
                      <div className="w-[1.5px] h-full bg-slate-800"></div>
                      <div className="w-[2px] h-full bg-slate-800"></div>
                      <div className="w-[1px] h-full bg-slate-800"></div>
                      <div className="w-[4px] h-full bg-slate-800"></div>
                      <div className="w-[2px] h-full bg-slate-800"></div>
                      <div className="w-[3px] h-full bg-slate-800"></div>
                      <div className="w-[1px] h-full bg-slate-800"></div>
                      <div className="w-[1.5px] h-full bg-slate-800"></div>
                      <div className="w-[4px] h-full bg-slate-800"></div>
                      <div className="w-[2px] h-full bg-slate-800"></div>
                    </div>
                    <span className="text-[10px] font-bold text-slate-400 font-mono tracking-widest">
                      *SE3-COMBINED-20260719*
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 text-center font-bold">
                    Vui lòng xuất trình mã QR/Barcode này tại cửa soát vé ga và khi lên tàu để nhân viên xác nhận.
                  </p>
                </div>
              </div>
            </div>
          ) : error ? (
            <div className="bg-white border border-outline-variant rounded-2xl p-12 text-center shadow-sm space-y-3">
              <span className="material-symbols-outlined text-red-500 text-5xl">warning</span>
              <p className="text-sm font-black text-on-surface">Không tìm thấy mã đặt vé</p>
              <p className="text-xs text-on-surface-variant font-medium">
                {error}
              </p>
            </div>
          ) : (
            <div className="bg-white border border-outline-variant rounded-2xl p-12 text-center shadow-sm space-y-2">
              <span className="material-symbols-outlined text-slate-300 text-5xl">confirmation_number</span>
              <p className="text-xs text-on-surface-variant font-semibold">Nhập mã đặt vé ở cột bên trái để bắt đầu tra cứu hành trình.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
