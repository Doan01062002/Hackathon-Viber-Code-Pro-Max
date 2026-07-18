"use client";

import { useState, useEffect } from "react";
import { seatApi } from "@/features/rail-ui/api/seatApi";
import type { GapSuggestionDto } from "@/features/rail-ui/api/seatApi";
import { STATION_OPTIONS } from "@/features/rail-ui/stations";

export function AvailabilityScreen() {
  const [gapSuggestions, setGapSuggestions] = useState<GapSuggestionDto[]>([]);
  const [selectedTrain, setSelectedTrain] = useState<string>("SE3");
  const [loading, setLoading] = useState<boolean>(false);
  const [isPassenger, setIsPassenger] = useState<boolean>(false);

  // Load suggestions from API
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        // Using trip_id = 1 as fallback for demo
        const data = await seatApi.getGapSuggestions(1);
        setGapSuggestions(data);
      } catch (err) {
        console.error("Lỗi khi tải đề xuất ghép chặng:", err);
      } finally {
        setLoading(false);
      }
    }
    void loadData();

    // Check if we are on the passenger side or admin side based on the URL or simple check
    if (typeof window !== "undefined") {
      setIsPassenger(window.location.pathname.startsWith("/booking") || !window.location.pathname.includes("admin"));
    }
  }, []);

  // Simple handler when clicking execute
  const handleExecute = (route: string) => {
    if (isPassenger) {
      window.alert(`Đang chuyển hướng sang Đặt vé cho hành trình ghép: ${route}. Chỗ của bạn đã được ưu tiên gán liên mạch!`);
    } else {
      window.alert(`Đã thực thi ghép chặng thành công cho chặng ${route}. Hệ thống đã điều chỉnh quota bán chặng suốt.`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="bg-white border border-outline-variant rounded-2xl p-6 shadow-sm">
        <h2 className="text-xl font-black text-on-surface flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-2xl">compare_arrows</span>
          Đề Xuất Ghép Chặng Trống & Tối Ưu Quota
        </h2>
        <p className="text-xs text-on-surface-variant font-medium mt-1">
          Hệ thống AI phân tích toàn bộ ghế trống cục bộ (gaps) để tạo ra các phương án ghép chặng vé suốt, nâng cao hệ số sử dụng ghế-km.
        </p>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Left Side: Availability Table / Segment Load status */}
        <div className="col-span-12 lg:col-span-8 bg-white border border-outline-variant rounded-2xl p-6 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-bold text-sm text-on-surface flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-sm">view_list</span>
              Bảng Danh Sách Trạng Thái Đoạn Trống (Availability Table)
            </h3>
            <div className="flex gap-2">
              <select
                value={selectedTrain}
                onChange={(e) => setSelectedTrain(e.target.value)}
                className="px-3 py-1 bg-slate-50 border border-outline-variant rounded-lg text-xs font-bold text-slate-700 focus:outline-none"
              >
                <option value="SE3">Tàu SE3 (Hà Nội - Sài Gòn)</option>
                <option value="SE1">Tàu SE1 (Hà Nội - Đà Nẵng)</option>
                <option value="SE19">Tàu SE19 (Hà Nội - Vinh)</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-left text-xs">
              <thead>
                <tr className="border-b border-outline-variant/35 bg-slate-50 text-[10px] uppercase font-black tracking-wider text-slate-400">
                  <th className="py-3 px-4">Chặng (Leg)</th>
                  <th className="py-3 px-4">Sức chứa (Capacity)</th>
                  <th className="py-3 px-4">Đang trống (Available Gaps)</th>
                  <th className="py-3 px-4">Tải thực tế (Load Factor)</th>
                  <th className="py-3 px-4">Đánh giá AI</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/30 font-semibold text-slate-700">
                <tr className="hover:bg-slate-50/50">
                  <td className="py-3 px-4 font-black">Hà Nội → Vinh</td>
                  <td className="py-3 px-4">420 ghế</td>
                  <td className="py-3 px-4 text-green-600">45 ghế trống</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 bg-[#eef1f8] text-[#5b607b] text-[10px] font-black rounded-full">62% (Thấp)</span>
                  </td>
                  <td className="py-3 px-4 text-primary text-[11px]">Còn nhiều chỗ ngắn chặng đầu</td>
                </tr>
                <tr className="hover:bg-slate-50/50">
                  <td className="py-3 px-4 font-black">Vinh → Đồng Hới</td>
                  <td className="py-3 px-4">420 ghế</td>
                  <td className="py-3 px-4 text-green-600">32 ghế trống</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 bg-[#eef1f8] text-[#5b607b] text-[10px] font-black rounded-full">58% (Thấp)</span>
                  </td>
                  <td className="py-3 px-4 text-primary text-[11px]">Nhu cầu trung bình ga lẻ</td>
                </tr>
                <tr className="hover:bg-slate-50/50">
                  <td className="py-3 px-4 font-black">Đồng Hới → Huế</td>
                  <td className="py-3 px-4">420 ghế</td>
                  <td className="py-3 px-4 text-amber-600 font-bold">12 ghế trống</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 bg-[#fdf1dc] text-[#b06f00] text-[10px] font-black rounded-full">79% (Trung bình)</span>
                  </td>
                  <td className="py-3 px-4 text-amber-700 text-[11px]">Bắt đầu khan hiếm chỗ</td>
                </tr>
                <tr className="hover:bg-slate-50/50">
                  <td className="py-3 px-4 font-black">Huế → Đà Nẵng</td>
                  <td className="py-3 px-4">420 ghế</td>
                  <td className="py-3 px-4 text-red-600 font-black">2 ghế trống</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 bg-[#fde3e8] text-[#c22a44] text-[10px] font-black rounded-full">98% (Quá tải)</span>
                  </td>
                  <td className="py-3 px-4 text-red-600 text-[11px] font-black">Nút cổ chai (Bottleneck)</td>
                </tr>
                <tr className="hover:bg-slate-50/50">
                  <td className="py-3 px-4 font-black">Đà Nẵng → Nha Trang</td>
                  <td className="py-3 px-4">420 ghế</td>
                  <td className="py-3 px-4 text-green-600">54 ghế trống</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 bg-[#eef1f8] text-[#5b607b] text-[10px] font-black rounded-full">67% (Thấp)</span>
                  </td>
                  <td className="py-3 px-4 text-primary text-[11px]">Dư năng lực chặng đêm</td>
                </tr>
                <tr className="hover:bg-slate-50/50">
                  <td className="py-3 px-4 font-black">Nha Trang → Sài Gòn</td>
                  <td className="py-3 px-4">420 ghế</td>
                  <td className="py-3 px-4 text-green-600">62 ghế trống</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 bg-[#eef1f8] text-[#5b607b] text-[10px] font-black rounded-full">59% (Thấp)</span>
                  </td>
                  <td className="py-3 px-4 text-primary text-[11px]">Nhu cầu chặng cuối lỏng</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Side: Suggested OD List (AI Suggestions) */}
        <div className="col-span-12 lg:col-span-4 bg-white border border-outline-variant rounded-2xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-sm text-on-surface mb-2 border-b border-outline-variant/35 pb-2 flex items-center gap-1.5">
              <span className="material-symbols-outlined text-primary text-base">auto_awesome</span>
              Đề xuất ghép chặng trống (OD)
            </h3>
            <p className="text-[10px] text-on-surface-variant font-medium mb-4 leading-normal">
              Các phương án tối ưu hóa vé do AI đề xuất giúp kết hợp các chặng trống liên mạch thành hành trình dài bán được giá cao hơn.
            </p>

            <div className="space-y-3.5">
              {gapSuggestions.length > 0 ? (
                gapSuggestions.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 bg-surface-container-low rounded-xl border border-primary/10 hover:border-primary/20 hover:shadow-sm transition-all"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-black text-xs text-on-surface">{item.route}</span>
                      <span className="text-primary font-black text-xs">{item.benefit}</span>
                    </div>
                    <p className="text-[10.5px] text-on-surface-variant leading-relaxed font-semibold">
                      {item.reason} ({item.seatType === "ngoi_mem" ? "Ngồi mềm" : "Giường nằm"})
                    </p>
                    <div className="mt-3 flex items-center justify-between">
                      <span className={`px-2 py-0.5 rounded text-[8px] font-black uppercase ${
                        item.priority === "Cao" 
                          ? "bg-red-50 text-red-600 border border-red-200" 
                          : item.priority === "Trung bình"
                          ? "bg-amber-50 text-amber-600 border border-amber-200"
                          : "bg-blue-50 text-blue-600 border border-blue-200"
                      }`}>
                        Ưu tiên: {item.priority}
                      </span>
                      <button
                        onClick={() => handleExecute(item.route)}
                        className="py-1 px-3 bg-primary hover:bg-primary/95 text-white font-black text-[10px] rounded-lg transition-all cursor-pointer shadow-sm"
                      >
                        {isPassenger ? "Đặt vé ngay" : "Thực thi Ghép"}
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="h-40 rounded-xl border border-dashed border-outline-variant flex items-center justify-center text-xs font-semibold text-on-surface-variant">
                  {loading ? "Đang tải đề xuất..." : "Không có đề xuất ghép chặng trống nào."}
                </div>
              )}
            </div>
          </div>

          <div className="mt-6 p-4 bg-slate-50 border border-outline-variant/35 rounded-xl">
            <span className="text-[9px] text-slate-400 font-black uppercase tracking-wider block">Nguyên lý hoạt động</span>
            <p className="text-[10.5px] text-slate-600 font-semibold leading-relaxed mt-1">
              AI quét tồn kho ghế vật lý theo lead-time. Khi một ghế bị chia nhỏ thành các chặng trống không liền nhau, hệ thống tự động sinh vé ghép liên mạch hoặc điều chỉnh quota mở rộng giúp khai thác tối đa doanh thu trên mỗi chuyến tàu.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
