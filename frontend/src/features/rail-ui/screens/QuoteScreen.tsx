"use client";

import { useState, useEffect } from "react";
import { SectionCard } from "@/features/rail-ui/components/Primitives";
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
    <div className="page-stack">
      {error && (
        <div className="banner banner-warning" style={{ backgroundColor: "#3a2a18", borderLeft: "4px solid #d97706", padding: "12px", borderRadius: "6px", color: "#f59e0b", fontSize: "14px", marginBottom: "8px" }}>
          ⚠️ <strong>Cảnh báo:</strong> {error} Hiển thị dữ liệu báo giá Demo.
        </div>
      )}

      <SectionCard title="Biểu mẫu báo giá" subtitle="Chọn ga đi/đến, chặng bay và loại chỗ để lấy giá vé đề xuất thời gian thực.">
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <label className="field" style={{ maxWidth: "500px" }}>
            <span>Chọn sản phẩm hành trình (OD Product)</span>
            <select
              className="input"
              value={selectedProductId}
              onChange={(e) => setSelectedProductId(Number(e.target.value))}
              style={{ backgroundColor: "#1e1e24", color: "#fff", border: "1px solid #333", borderRadius: "4px", padding: "8px", width: "100%" }}
            >
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.origin_station_code} → {p.destination_station_code} ({p.seat_type === "soft_seat" ? "Ngồi mềm" : "Giường nằm K6"}) - Giá gốc: {formatVND(p.base_price)}
                </option>
              ))}
            </select>
          </label>

          {activeProduct && (
            <div className="form-grid" style={{ opacity: loading ? 0.5 : 1, transition: "opacity 0.2s" }}>
              <label className="field">
                <span>Ga đi</span>
                <input className="input" value={activeProduct.origin_station_code} readOnly style={{ backgroundColor: "#151518", color: "#888" }} />
              </label>
              <label className="field">
                <span>Ga đến</span>
                <input className="input" value={activeProduct.destination_station_code} readOnly style={{ backgroundColor: "#151518", color: "#888" }} />
              </label>
              <label className="field">
                <span>Loại chỗ</span>
                <input className="input" value={activeProduct.seat_type === "soft_seat" ? "Ngồi mềm điều hòa" : "Giường nằm khoang 6"} readOnly style={{ backgroundColor: "#151518", color: "#888" }} />
              </label>
              <label className="field">
                <span>Mã chuyến tàu</span>
                <input className="input" value={`Trip #${activeProduct.trip_id}`} readOnly style={{ backgroundColor: "#151518", color: "#888" }} />
              </label>
            </div>
          )}
        </div>
      </SectionCard>

      <div className="two-up" style={{ opacity: loading ? 0.5 : 1, transition: "opacity 0.2s" }}>
        <SectionCard title="Kết quả báo giá" subtitle="Giá cuối cùng đã áp dụng hạn ngạch và chi phí cơ hội.">
          <div className="quote-card">
            <div>
              <span className="mini-label">Giá đề xuất tối ưu</span>
              <strong className="quote-price">
                {quote ? formatVND(quote.final_price) : mockQuote.finalPrice}
              </strong>
            </div>
            <div className="quote-meta">
              <article>
                <span>Quyết định</span>
                <strong style={{ color: "#10b981" }}>Chấp nhận (AI)</strong>
              </article>
              <article>
                <span>Chi phí cơ hội (Opportunity Cost)</span>
                <strong>
                  {quote ? formatVND(quote.opportunity_cost) : mockQuote.opportunityCost}
                </strong>
              </article>
              <article>
                <span>Hết hạn báo giá</span>
                <strong style={{ fontSize: "11px", wordBreak: "break-all" }}>
                  {quote ? new Date(quote.expires_at).toLocaleTimeString() : "15 phút"}
                </strong>
              </article>
            </div>
          </div>
        </SectionCard>

        <SectionCard
          title="Thẻ diễn giải giá (PriceExplainCard)"
          subtitle="Giải thích cấu trúc tính toán và các chính sách kiểm soát giá đang áp dụng."
        >
          <div className="explain-card">
            {quote ? (
              <div>
                <p>
                  Giá tối ưu bằng <strong>Giá gốc + 1.2 × Chi phí cơ hội</strong>. 
                  {quote.explanation.applied_policies.length > 0 
                    ? " Báo giá đang được bảo vệ bởi bộ lọc trần/sàn giá vé." 
                    : " Báo giá hoạt động bình thường, chặng thông thoáng."}
                </p>
                <div style={{ marginTop: "12px" }}>
                  <span className="mini-label">Ràng buộc chính sách áp dụng:</span>
                  <ul className="tag-list" style={{ marginTop: "6px" }}>
                    {quote.explanation.applied_policies.length > 0 ? (
                      quote.explanation.applied_policies.map((p) => (
                        <li key={p} style={{ backgroundColor: "#3b2a18", color: "#f59e0b", border: "1px solid #78350f" }}>
                          {p === "MIN_PRICE_ENFORCED" && "ÉP SÀN GIÁ VÉ (MIN_PRICE)"}
                          {p === "MAX_PRICE_ENFORCED" && "CHẶN TRẦN GIÁ VÉ (MAX_PRICE)"}
                          {p === "MAX_STEP_CHANGE_CAPPED" && "GIỚI HẠN BƯỚC NHẢY TĂNG (MAX_STEP)"}
                          {p === "MIN_STEP_CHANGE_CAPPED" && "GIỚI HẠN BƯỚC NHẢY GIẢM (MIN_STEP)"}
                        </li>
                      ))
                    ) : (
                      <li style={{ backgroundColor: "#111827", color: "#9ca3af", border: "1px solid #374151" }}>
                        KHÔNG CÓ RÀNG BUỘC ACTIVE
                      </li>
                    )}
                  </ul>
                </div>
              </div>
            ) : (
              <div>
                <p>{mockQuote.explanation}</p>
                <ul className="tag-list">
                  <li>Bid price cao</li>
                  <li>Nhu cầu vượt tồn kho</li>
                  <li>Ưu tiên luồng dài</li>
                </ul>
              </div>
            )}
          </div>
        </SectionCard>
      </div>

      <SectionCard
        title="Lựa chọn thay thế"
        subtitle="Đề xuất các phương án gần nhất để giữ tỷ lệ chuyển đổi khi route chính nóng."
      >
        <div className="stack-list">
          {mockQuote.alternatives.map((item) => (
            <article className="list-card" key={item.label}>
              <div>
                <strong>{item.label}</strong>
                <p>{item.note}</p>
              </div>
              <div className="list-aside">
                <strong>{item.price}</strong>
                <button className="btn btn-ghost" type="button">
                  Chọn phương án
                </button>
              </div>
            </article>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
