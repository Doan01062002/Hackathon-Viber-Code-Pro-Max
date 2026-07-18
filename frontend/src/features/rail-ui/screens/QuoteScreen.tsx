"use client";

import React, { useState, useEffect } from "react";
import { apiClient } from "@/lib/api/client";
import { quoteResult as mockQuote } from "@/features/rail-ui/mockData";
import { RouteMap, MOCK_ROUTE_SEGMENTS } from "@/features/rail-ui/components/RouteMap";

// ─── Types ─────────────────────────────────────────────────────────────────────

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

// ─── Main Screen ────────────────────────────────────────────────────────────────

export function QuoteScreen() {
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<number | "">("");
  const [quote, setQuote] = useState<QuoteResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const translatePolicy = (policy: string) => {
    const clean = policy.replace(/_ENFORCED|_CAPPED/g, "");
    if (clean === "FLOOR_PRICE") return "Bảo vệ giá sàn";
    if (clean === "CEILING_PRICE") return "Giới hạn giá trần";
    if (clean === "MAX_DAILY_DELTA") return "Biên độ ngày tối đa";
    return clean;
  };

  useEffect(() => {
    async function fetchProducts() {
      try {
        const data = await apiClient.get<ProductItem[]>("/api/v1/pricing/products");
        setProducts(data);
        if (data.length > 0) setSelectedProductId(data[0].id);
      } catch (err) {
        console.error("Không tải được danh sách sản phẩm:", err);
      }
    }
    fetchProducts();
  }, []);

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
        console.warn("Lỗi kết nối API báo giá:", err);
        setError("Không kết nối được hệ thống tính toán giá động.");
      } finally {
        setLoading(false);
      }
    }
    fetchQuote();
  }, [selectedProductId]);

  const activeProduct = products.find((p) => p.id === selectedProductId);
  const formatVND = (value: number) =>
    new Intl.NumberFormat("vi-VN", {
      style: "currency",
      currency: "VND",
    }).format(value);

  return (
    <div className="space-y-6">
      {error ? (
        <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-lg text-yellow-700 text-xs font-semibold">
          Cảnh báo: {error} Đang hiển thị dữ liệu báo giá Demo.
        </div>
      ) : null}

      {/* Main Layout */}
      <div className="grid grid-cols-12 gap-6">
        {/* Left: Form + Route Map */}
        <section className="col-span-12 lg:col-span-8 space-y-6">
          {/* Pricing Form */}
          <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-sm text-on-surface flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-sm">
                payments
              </span>
              Báo giá hành trình
            </h3>
            <div className="space-y-4">
              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant">
                  Chọn sản phẩm hành trình (OD Product)
                </label>
                <select
                  value={selectedProductId}
                  onChange={(e) =>
                    setSelectedProductId(Number(e.target.value))
                  }
                  className="w-full bg-surface-container-low border border-outline-variant rounded-lg py-2 px-3 text-xs font-semibold outline-none focus:ring-1 focus:ring-primary"
                >
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.origin_station_code} - {p.destination_station_code} (
                      {p.seat_type === "soft_seat" ? "Ngồi mềm" : "Giường nằm"}
                      ) - Giá gốc: {formatVND(p.base_price)}
                    </option>
                  ))}
                </select>
              </div>

              {activeProduct ? (
                <div className="grid grid-cols-4 gap-4 pt-2">
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-outline-variant/35 text-xs">
                    <span className="text-[9px] text-on-surface-variant font-bold uppercase">
                      Ga đi
                    </span>
                    <p className="font-bold mt-0.5">
                      {activeProduct.origin_station_code}
                    </p>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-outline-variant/35 text-xs">
                    <span className="text-[9px] text-on-surface-variant font-bold uppercase">
                      Ga đến
                    </span>
                    <p className="font-bold mt-0.5">
                      {activeProduct.destination_station_code}
                    </p>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-outline-variant/35 text-xs">
                    <span className="text-[9px] text-on-surface-variant font-bold uppercase">
                      Loại chỗ
                    </span>
                    <p className="font-bold mt-0.5">
                      {activeProduct.seat_type === "soft_seat"
                        ? "Ngồi mềm"
                        : "Giường nằm"}
                    </p>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-outline-variant/35 text-xs">
                    <span className="text-[9px] text-on-surface-variant font-bold uppercase">
                      Mã chuyến
                    </span>
                    <p className="font-bold mt-0.5">
                      Trip #{activeProduct.trip_id}
                    </p>
                  </div>
                </div>
              ) : null}
            </div>
          </div>

          {/* Route Map visualization */}
          <RouteMap segments={MOCK_ROUTE_SEGMENTS} />
        </section>

        {/* Right: Quote Results */}
        <aside className="col-span-12 lg:col-span-4 space-y-6">
          {/* Kết quả báo giá */}
          <div
            className={`bg-white border border-outline-variant rounded-xl p-5 shadow-sm transition-opacity duration-200 ${
              loading ? "opacity-50" : "opacity-100"
            }`}
          >
            <h3 className="font-bold text-xs text-on-surface uppercase tracking-wider mb-3 border-b border-outline-variant/30 pb-2">
              Kết quả báo giá tối ưu
            </h3>

            <div className="space-y-4">
              <div>
                <span className="text-[10px] text-on-surface-variant font-bold uppercase">
                  Giá đề xuất tối ưu
                </span>
                <p className="text-2xl font-black text-primary font-mono mt-1">
                  {quote ? formatVND(quote.final_price) : mockQuote.finalPrice}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs font-semibold pt-1">
                <div className="bg-slate-50 p-2.5 rounded-lg border border-outline-variant/30">
                  <span className="text-[9px] text-on-surface-variant font-bold uppercase">
                    Quyết định
                  </span>
                  <p className="text-green-600 font-extrabold mt-0.5">
                    Chấp nhận (AI)
                  </p>
                </div>
                <div className="bg-slate-50 p-2.5 rounded-lg border border-outline-variant/30">
                  <span className="text-[9px] text-on-surface-variant font-bold uppercase">
                    Chi phí cơ hội
                  </span>
                  <p className="font-bold mt-0.5 text-on-surface font-mono">
                    {quote
                      ? formatVND(quote.opportunity_cost)
                      : mockQuote.opportunityCost}
                  </p>
                </div>
              </div>

              <div className="text-[10px] text-on-surface-variant font-semibold bg-slate-50/50 p-2 rounded border border-dashed border-outline-variant flex justify-between">
                <span>Thời gian hết hạn:</span>
                <span className="font-bold font-mono text-primary">
                  {quote
                    ? new Date(quote.expires_at).toLocaleTimeString()
                    : "15:00"}
                </span>
              </div>
            </div>
          </div>

          {/* Diễn giải báo giá */}
          <div
            className={`bg-white border border-outline-variant rounded-xl p-5 shadow-sm transition-opacity duration-200 ${
              loading ? "opacity-50" : "opacity-100"
            }`}
          >
            <h3 className="font-bold text-xs text-on-surface uppercase tracking-wider mb-2 border-b border-outline-variant/30 pb-2">
              Diễn giải báo giá
            </h3>

            <div className="text-xs font-semibold leading-relaxed text-on-surface-variant space-y-3">
              {quote ? (
                <div>
                  <p>
                    Giá tối ưu bằng{" "}
                    <strong className="text-on-surface">
                      Giá gốc + 1.2 x Chi phí cơ hội
                    </strong>
                    .{" "}
                    {quote.explanation.applied_policies.length > 0
                      ? "Báo giá đang được bảo vệ bởi bộ lọc trần/sàn giá vé."
                      : "Báo giá hoạt động bình thường, chặng thông thoáng."}
                  </p>
                  <div className="pt-2">
                    <span className="text-[10px] font-bold text-on-surface-variant uppercase">
                      Chính sách áp dụng:
                    </span>
                    <div className="flex flex-wrap gap-1.5 mt-1.5">
                      {quote.explanation.applied_policies.length > 0 ? (
                        quote.explanation.applied_policies.map((p) => (
                          <span
                            key={p}
                            className="bg-yellow-50 text-yellow-700 border border-yellow-300 px-2 py-0.5 rounded text-[8px] font-extrabold uppercase"
                          >
                            {translatePolicy(p)}
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
                    <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[8px] font-extrabold uppercase">
                      Giá cơ hội cao
                    </span>
                    <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[8px] font-extrabold uppercase">
                      Nhu cầu vượt tồn kho
                    </span>
                    <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[8px] font-extrabold uppercase">
                      Ưu tiên luồng dài
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Network Map thumbnail */}
          <div className="bg-white border border-outline-variant rounded-xl overflow-hidden shadow-sm h-64 relative">
            <img
              className="w-full h-full object-cover"
              alt="Bản đồ mạng lưới chặng"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuDqefbziBtF-K_WFMPtQn5LoS4TRXshMSMORahY21cRunFCAS-YIGVYOapfQPJs_AVTnCAAOIvB4JmcTGxKcMvoE9inf24681pb8l_PTPzNQy4nHdsaxk1pqUGEPmMNBqoB-GPFiXrKkzMVVdYLW5m3wn-z7nzBhIAhzge2n5DIF_iPrLuB-6MTh-i4kpwtsfjRb529jgpp9l6kPZ3AZRilbpzO34_FLgDy--x43QtVqGi__FnW0G1pyd8X45cCLP7L-NmERI4PPWS2"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
            <div className="absolute bottom-4 left-4 text-white">
              <p className="text-[10px] font-bold uppercase tracking-widest opacity-80">
                Bản đồ lớp phủ mạng lưới
              </p>
              <p className="text-sm font-semibold">
                Đang theo dõi 4 điểm tắc nghẽn
              </p>
            </div>
            <button className="absolute top-4 right-4 bg-white/20 backdrop-blur-md p-2 rounded-full text-white hover:bg-white/40 transition-all flex items-center justify-center">
              <span className="material-symbols-outlined text-sm">
                fullscreen
              </span>
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}
