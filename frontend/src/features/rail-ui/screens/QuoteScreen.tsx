"use client";

import React, { useState, useEffect } from "react";
import { apiClient } from "@/lib/api/client";
import { quoteResult as mockQuote } from "@/features/rail-ui/mockData";

interface ProductItem {
  id: number;
  trip_id: number;
  origin_station_code: string;
  destination_station_code: string;
  seat_type: string;
  base_price: number;
}

interface QuoteExplanation {
  base_opportunity_cost: number;
  markup_factor: number;
  applied_policies: string[];
}

interface QuoteResponse {
  quote_id: number;
  od_product_id: number;
  policy_id: number | null;
  opportunity_cost: number;
  proposed_price: number;
  final_price: number;
  decision: string;
  explanation: QuoteExplanation;
  expires_at: string;
}

export function QuoteScreen() {
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<number | "">("");
  const [quote, setQuote] = useState<QuoteResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [strategy, setStrategy] = useState("revenue");

  // 1. Tải danh sách sản phẩm OD khi mount
  useEffect(() => {
    async function fetchProducts() {
      try {
        const data = await apiClient.get<ProductItem[]>("/api/v1/pricing/products");
        setProducts(data);
        if (data.length > 0) {
          setSelectedProductId(data[0].id);
        }
      } catch (err) {
        console.error("Không tải được danh sách sản phẩm:", err);
      }
    }
    fetchProducts();
  }, []);

  // 2. Tải báo giá động khi chọn sản phẩm khác nhau
  useEffect(() => {
    if (!selectedProductId) return;

    async function fetchQuote() {
      try {
        setLoading(true);
        setError(null);
        const data = await apiClient.get<QuoteResponse>(
          `/api/v1/pricing/quote?od_product_id=${selectedProductId}`
        );
        setQuote(data);
      } catch (err) {
        console.warn("Lỗi kết nối API báo giá, sử dụng fallback:", err);
        setError("Không kết nối được API báo giá động.");
      } finally {
        setLoading(false);
      }
    }

    fetchQuote();
  }, [selectedProductId]);

  const activeProduct = products.find((p) => p.id === selectedProductId);

  // Định dạng hiển thị tiền tệ
  const formatVND = (value: number) => {
    return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value);
  };

  return (
    <div className="space-y-6">

      {error && (
        <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-lg text-yellow-700 text-xs font-semibold">
          ⚠️ Cảnh báo: {error} Đang hiển thị dữ liệu báo giá Demo cục bộ.
        </div>
      )}

      {/* Alerts Banner */}
      <div className="flex gap-4 overflow-x-auto pb-2 custom-scrollbar">
        <div className="flex-shrink-0 flex items-center gap-3 bg-error-container/30 border border-error/20 p-4 rounded-xl min-w-[320px]">
          <div className="w-10 h-10 rounded-full bg-error flex items-center justify-center text-white">
            <span className="material-symbols-outlined text-base">warning</span>
          </div>
          <div>
            <p className="font-bold text-sm text-error">Bottleneck: Leg HN-Vinh</p>
            <p className="text-xs text-on-error-container font-semibold">
              Load factor at 96%. Suggest +15% price shift.
            </p>
          </div>
        </div>

        <div className="flex-shrink-0 flex items-center gap-3 bg-primary-container/10 border border-primary/20 p-4 rounded-xl min-w-[320px]">
          <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-white">
            <span className="material-symbols-outlined text-base">bolt</span>
          </div>
          <div>
            <p className="font-bold text-sm text-primary">Opportunity: Vinh-Hue</p>
            <p className="text-xs text-primary/80 font-semibold">
              Competitor outage detected. Optimize yield.
            </p>
          </div>
        </div>

        <div className="flex-shrink-0 flex items-center gap-3 bg-secondary-container/30 border border-secondary/20 p-4 rounded-xl min-w-[320px]">
          <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center text-white">
            <span className="material-symbols-outlined text-base">trending_down</span>
          </div>
          <div>
            <p className="font-bold text-sm text-secondary">Low Demand: Hue-DN</p>
            <p className="text-xs text-on-secondary-container font-semibold">
              Price ceiling holding too high. Soften -8%.
            </p>
          </div>
        </div>
      </div>

      {/* Main Pricing Layout */}
      <div className="grid grid-cols-12 gap-6">
        {/* Left Columns (Form and Suggestions) */}
        <section className="col-span-12 lg:col-span-8 space-y-6">
          {/* Biểu mẫu báo giá */}
          <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-sm text-on-surface flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-sm">payments</span>
              Biểu mẫu báo giá hành trình
            </h3>
            
            <div className="space-y-4">
              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant">Chọn sản phẩm hành trình (OD Product)</label>
                <select
                  value={selectedProductId}
                  onChange={(e) => setSelectedProductId(Number(e.target.value))}
                  className="w-full bg-surface-container-low border border-outline-variant rounded-lg py-2 px-3 text-xs font-semibold outline-none focus:ring-1 focus:ring-primary"
                >
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.origin_station_code} → {p.destination_station_code} ({p.seat_type === "soft_seat" ? "Ngồi mềm" : "Giường nằm"}) - Giá gốc: {formatVND(p.base_price)}
                    </option>
                  ))}
                </select>
              </div>

              {activeProduct && (
                <div className={`grid grid-cols-2 md:grid-cols-4 gap-4 pt-2 transition-opacity duration-200 ${loading ? "opacity-50" : "opacity-100"}`}>
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-outline-variant/35 text-xs">
                    <span className="text-[9px] text-on-surface-variant font-bold uppercase">Ga đi</span>
                    <p className="font-bold mt-0.5">{activeProduct.origin_station_code}</p>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-outline-variant/35 text-xs">
                    <span className="text-[9px] text-on-surface-variant font-bold uppercase">Ga đến</span>
                    <p className="font-bold mt-0.5">{activeProduct.destination_station_code}</p>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-outline-variant/35 text-xs">
                    <span className="text-[9px] text-on-surface-variant font-bold uppercase">Loại chỗ</span>
                    <p className="font-bold mt-0.5">{activeProduct.seat_type === "soft_seat" ? "Ngồi mềm điều hòa" : "Giường nằm"}</p>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-outline-variant/35 text-xs">
                    <span className="text-[9px] text-on-surface-variant font-bold uppercase">Mã chuyến</span>
                    <p className="font-bold mt-0.5">Trip #{activeProduct.trip_id}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Table suggestion */}
          <div className="bg-white border border-outline-variant rounded-xl overflow-hidden shadow-sm">
            <div className="p-6 border-b border-outline-variant flex justify-between items-center bg-white">
              <div>
                <h3 className="font-bold text-sm text-on-surface">Pricing Control Center</h3>
                <p className="text-[11px] text-on-surface-variant font-semibold mt-0.5">
                  OD (Origin-Destination) Pair Recommendations
                </p>
              </div>
              <div className="flex gap-2">
                <button className="px-3 py-1.5 border border-outline-variant rounded-md text-xs font-bold hover:bg-surface-container transition-colors text-on-surface">
                  Export CSV
                </button>
                <button className="px-3 py-1.5 bg-primary text-white rounded-md text-xs font-bold hover:brightness-110 transition-all">
                  Accept All Suggestions
                </button>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-surface-container-low text-xs text-on-surface-variant font-bold uppercase">
                  <tr>
                    <th className="px-6 py-4">Chặng / Sản phẩm</th>
                    <th className="px-6 py-4 text-center">Giá hiện tại</th>
                    <th className="px-6 py-4 text-center">Giá đề xuất AI</th>
                    <th className="px-6 py-4">Chi phí cơ hội</th>
                    <th className="px-6 py-4">Trạng thái</th>
                    <th className="px-6 py-4"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant/30 text-sm">
                  {/* London -> Manchester mapped to VN routes */}
                  <tr className="hover:bg-surface-container-low transition-colors">
                    <td className="px-6 py-5">
                      <p className="font-bold text-on-surface">Hà Nội ↔ Vinh</p>
                      <p className="text-xs text-on-surface-variant font-medium">Toa Ngồi mềm điều hòa</p>
                    </td>
                    <td className="px-6 py-5 text-center font-bold font-mono">150.000đ</td>
                    <td className="px-6 py-5 text-center">
                      <span className="bg-primary/10 text-primary px-2.5 py-1 rounded font-bold font-mono">195.000đ</span>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-surface-container rounded-full overflow-hidden">
                          <div className="h-full bg-primary" style={{ width: "85%" }} />
                        </div>
                        <span className="text-xs font-bold text-primary font-mono">220.000đ</span>
                      </div>
                      <p className="text-[10px] text-on-surface-variant mt-1 font-semibold">Tải chặng đạt 92%</p>
                    </td>
                    <td className="px-6 py-5">
                      <span className="inline-flex items-center gap-1.5 bg-error/10 text-error px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider">
                        <span className="w-1.5 h-1.5 rounded-full bg-error animate-pulse" />
                        Bottleneck
                      </span>
                    </td>
                    <td className="px-6 py-5 text-right">
                      <button className="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors text-base">more_vert</button>
                    </td>
                  </tr>

                  {/* Paris -> Lyon mapped to VN routes */}
                  <tr className="hover:bg-surface-container-low transition-colors">
                    <td className="px-6 py-5">
                      <p className="font-bold text-on-surface">Vinh ↔ Huế</p>
                      <p className="text-xs text-on-surface-variant font-medium">Toa Giường nằm khoang 6</p>
                    </td>
                    <td className="px-6 py-5 text-center font-bold font-mono">320.000đ</td>
                    <td className="px-6 py-5 text-center">
                      <span className="bg-primary/10 text-primary px-2.5 py-1 rounded font-bold font-mono">350.000đ</span>
                    </td>
                    <td className="px-6 py-5">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-surface-container rounded-full overflow-hidden">
                          <div className="h-full bg-primary" style={{ width: "45%" }} />
                        </div>
                        <span className="text-xs font-bold text-primary font-mono">360.000đ</span>
                      </div>
                      <p className="text-[10px] text-on-surface-variant mt-1 font-semibold">Cầu tải ổn định</p>
                    </td>
                    <td className="px-6 py-5">
                      <span className="inline-flex items-center gap-1.5 bg-slate-100 text-slate-700 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                        Stable
                      </span>
                    </td>
                    <td className="px-6 py-5 text-right">
                      <button className="material-symbols-outlined text-on-surface-variant hover:text-primary transition-colors text-base">more_vert</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Right Columns (Quote Results and Pricing Rules) */}
        <aside className="col-span-12 lg:col-span-4 space-y-6">
          {/* Kết quả báo giá */}
          <div className={`bg-white border border-outline-variant rounded-xl p-5 shadow-sm transition-opacity duration-200 ${loading ? "opacity-50" : "opacity-100"}`}>
            <h3 className="font-bold text-xs text-on-surface uppercase tracking-wider mb-3 border-b border-outline-variant/30 pb-2">
              Kết quả báo giá tối ưu
            </h3>
            
            <div className="space-y-4">
              <div>
                <span className="text-[10px] text-on-surface-variant font-bold uppercase">Giá đề xuất tối ưu</span>
                <p className="text-2xl font-black text-primary font-mono mt-1">
                  {quote ? formatVND(quote.final_price) : mockQuote.finalPrice}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs font-semibold pt-1">
                <div className="bg-slate-50 p-2.5 rounded-lg border border-outline-variant/30">
                  <span className="text-[9px] text-on-surface-variant font-bold uppercase">Quyết định</span>
                  <p className="text-green-600 font-extrabold mt-0.5">Chấp nhận (AI)</p>
                </div>
                <div className="bg-slate-50 p-2.5 rounded-lg border border-outline-variant/30">
                  <span className="text-[9px] text-on-surface-variant font-bold uppercase">Chi phí cơ hội</span>
                  <p className="font-bold mt-0.5 text-on-surface font-mono">
                    {quote ? formatVND(quote.opportunity_cost) : mockQuote.opportunityCost}
                  </p>
                </div>
              </div>

              <div className="text-[10px] text-on-surface-variant font-semibold bg-slate-50/50 p-2 rounded border border-dashed border-outline-variant flex justify-between">
                <span>Thời gian hết hạn:</span>
                <span className="font-bold font-mono text-primary">
                  {quote ? new Date(quote.expires_at).toLocaleTimeString() : "15:00"}
                </span>
              </div>
            </div>
          </div>

          {/* PriceExplainCard */}
          <div className={`bg-white border border-outline-variant rounded-xl p-5 shadow-sm transition-opacity duration-200 ${loading ? "opacity-50" : "opacity-100"}`}>
            <h3 className="font-bold text-xs text-on-surface uppercase tracking-wider mb-2 border-b border-outline-variant/30 pb-2">
              Diễn giải báo giá (PriceExplain)
            </h3>
            
            <div className="text-xs font-semibold leading-relaxed text-on-surface-variant space-y-3">
              {quote ? (
                <div>
                  <p>
                    Giá tối ưu bằng <strong className="text-on-surface">Giá gốc + 1.2 × Chi phí cơ hội</strong>. 
                    {quote.explanation.applied_policies.length > 0 
                      ? " Báo giá đang được bảo vệ bởi bộ lọc trần/sàn giá vé." 
                      : " Báo giá hoạt động bình thường, chặng thông thoáng."}
                  </p>
                  <div className="pt-2">
                    <span className="text-[10px] font-bold text-on-surface-variant uppercase">Chính sách áp dụng:</span>
                    <div className="flex flex-wrap gap-1.5 mt-1.5">
                      {quote.explanation.applied_policies.length > 0 ? (
                        quote.explanation.applied_policies.map((p) => (
                          <span key={p} className="bg-yellow-50 text-yellow-700 border border-yellow-300 px-2 py-0.5 rounded text-[8px] font-extrabold uppercase">
                            {p.replace(/_ENFORCED|_CAPPED/g, "")}
                          </span>
                        ))
                      ) : (
                        <span className="bg-slate-100 text-slate-500 border border-outline-variant/35 px-2 py-0.5 rounded text-[8px] font-extrabold uppercase">
                          Không có ràng buộc
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div>
                  <p>{mockQuote.explanation}</p>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[8px] font-extrabold uppercase">Bid price cao</span>
                    <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[8px] font-extrabold uppercase">Nhu cầu vượt tồn kho</span>
                    <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[8px] font-extrabold uppercase">Ưu tiên luồng dài</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Pricing Rule Engine */}
          <div className="bg-surface-container-highest/50 border border-primary/10 rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-6">
              <span className="material-symbols-outlined text-primary">rule_settings</span>
              <h3 className="font-bold text-base text-on-surface">Pricing Rule Engine</h3>
            </div>

            <div className="space-y-6">
              {/* Floor/Ceiling constraints */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                    Price Range Constraint
                  </label>
                  <span className="material-symbols-outlined text-xs cursor-help">info</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white p-3 border border-outline-variant rounded-lg">
                    <p className="text-[10px] text-on-surface-variant mb-1 font-bold">Floor (Min)</p>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-on-surface-variant">VND</span>
                      <input
                        className="border-none p-0 w-full font-bold focus:ring-0 text-xs bg-transparent outline-none"
                        type="text"
                        defaultValue="80.000"
                      />
                    </div>
                  </div>
                  <div className="bg-white p-3 border border-outline-variant rounded-lg">
                    <p className="text-[10px] text-on-surface-variant mb-1 font-bold">Ceiling (Max)</p>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-on-surface-variant">VND</span>
                      <input
                        className="border-none p-0 w-full font-bold focus:ring-0 text-xs bg-transparent outline-none"
                        type="text"
                        defaultValue="1.500.000"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Delta Range Slider */}
              <div className="space-y-3">
                <label className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                  Max Daily Delta (%)
                </label>
                <input
                  className="w-full accent-primary bg-surface-container h-2 rounded-full appearance-none cursor-pointer"
                  type="range"
                  min="5"
                  max="30"
                  defaultValue="15"
                />
                <div className="flex justify-between text-[10px] font-bold">
                  <span>5%</span>
                  <span className="text-primary">Current: 15%</span>
                  <span>30%</span>
                </div>
              </div>

              {/* Strategy selectors */}
              <div className="space-y-3">
                <label className="text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                  Optimization Strategy
                </label>
                <div className="space-y-2">
                  <label
                    className={`flex items-center gap-3 p-3 bg-white border-2 rounded-lg cursor-pointer transition-all ${
                      strategy === "revenue" ? "border-primary" : "border-outline-variant"
                    }`}
                    onClick={() => setStrategy("revenue")}
                  >
                    <input
                      checked={strategy === "revenue"}
                      onChange={() => {}}
                      className="text-primary focus:ring-primary scale-90"
                      name="strategy"
                      type="radio"
                    />
                    <div>
                      <p className="text-xs font-bold text-on-surface">Revenue Maximizer</p>
                      <p className="text-[10px] text-on-surface-variant font-medium mt-0.5">
                        Prioritizes high-yield premium bookings
                      </p>
                    </div>
                  </label>

                  <label
                    className={`flex items-center gap-3 p-3 bg-white border rounded-lg cursor-pointer hover:bg-surface-container-low transition-all ${
                      strategy === "load" ? "border-primary border-2" : "border-outline-variant"
                    }`}
                    onClick={() => setStrategy("load")}
                  >
                    <input
                      checked={strategy === "load"}
                      onChange={() => {}}
                      className="text-primary focus:ring-primary scale-90"
                      name="strategy"
                      type="radio"
                    />
                    <div>
                      <p className="text-xs font-bold text-on-surface">Load Factor Filler</p>
                      <p className="text-[10px] text-on-surface-variant font-medium mt-0.5">
                        Aggressive pricing to fill empty seats
                      </p>
                    </div>
                  </label>
                </div>
              </div>

              <button className="w-full py-3.5 bg-on-background text-white rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-black transition-all text-xs cursor-pointer">
                <span className="material-symbols-outlined text-sm">published_with_changes</span>
                Update Engine Rules
              </button>
            </div>
          </div>

          {/* Contextual Network Map overlay */}
          <div className="bg-white border border-outline-variant rounded-xl overflow-hidden shadow-sm h-64 relative group">
            <img
              className="w-full h-full object-cover"
              alt="Active Network Map"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuDqefbziBtF-K_WFMPtQn5LoS4TRXshMSMORahY21cRunFCAS-YIGVYOapfQPJs_AVTnCAAOIvB4JmcTGxKcMvoE9inf24681pb8l_PTPzNQy4nHdsaxk1pqUGEPmMNBqoB-GPFiXrKkzMVVdYLW5m3wn-z7nzBhIAhzge2n5DIF_iPrLuB-6MTh-i4kpwtsfjRb529jgpp9l6kPZ3AZRilbpzO34_FLgDy--x43QtVqGi__FnW0G1pyd8X45cCLP7L-NmERI4PPWS2"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
            <div className="absolute bottom-4 left-4 text-white">
              <p className="text-[10px] font-bold uppercase tracking-widest opacity-80">
                Active Network Overlay
              </p>
              <p className="text-sm font-semibold">Monitoring 4 active bottlenecks</p>
            </div>
            <button className="absolute top-4 right-4 bg-white/20 backdrop-blur-md p-2 rounded-full text-white hover:bg-white/40 transition-all flex items-center justify-center">
              <span className="material-symbols-outlined text-sm">fullscreen</span>
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}
