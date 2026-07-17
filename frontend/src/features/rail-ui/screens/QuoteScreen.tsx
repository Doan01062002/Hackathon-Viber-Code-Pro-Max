"use client";

import { FormEvent, useState, useEffect } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { SectionCard } from "@/features/rail-ui/components/Primitives";
import { createPricingQuote } from "@/features/quote/api/quoteApi";
import type { PricingQuoteRequest, PricingQuoteResponse } from "@/features/quote/types";
import { ApiError } from "@/lib/api/client";

const initialRequest: PricingQuoteRequest = {
  origin: "HN",
  destination: "DAN",
  seat_type: "giuong_nam_k6",
  service_date: "2026-07-19",
};

const moneyFormatter = new Intl.NumberFormat("vi-VN", {
  style: "currency",
  currency: "VND",
  maximumFractionDigits: 0,
});

function formatMoney(value: number): string {
  return moneyFormatter.format(value);
}

export function QuoteScreen() {
  const [request, setRequest] = useState<PricingQuoteRequest>(initialRequest);
  const [quote, setQuote] = useState<PricingQuoteResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const origin = params.get("origin");
    const destination = params.get("destination");
    const seatType = params.get("seatType");
    const date = params.get("date");
    
    if (origin || destination || seatType || date) {
      setRequest({
        origin: origin || initialRequest.origin,
        destination: destination || initialRequest.destination,
        seat_type: seatType || initialRequest.seat_type,
        service_date: date || initialRequest.service_date,
      });
    }
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      setQuote(await createPricingQuote(request));
    } catch (caught) {
      setQuote(null);
      setError(caught instanceof ApiError ? caught.message : "Không thể lấy báo giá");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="page-stack">
      <SectionCard title="Biểu mẫu báo giá" subtitle="Nhập luồng OD, loại chỗ và ngày đi để xem giá đề xuất.">
        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <label className="field">
              <span>Ga đi</span>
              <Input
                value={request.origin}
                onChange={(event) => setRequest({ ...request, origin: event.target.value })}
                placeholder="Mã hoặc tên ga, ví dụ HN"
                required
              />
            </label>
            <label className="field">
              <span>Ga đến</span>
              <Input
                value={request.destination}
                onChange={(event) => setRequest({ ...request, destination: event.target.value })}
                placeholder="Mã hoặc tên ga, ví dụ DAN"
                required
              />
            </label>
            <label className="field">
              <span>Loại chỗ</span>
              <select
                className="input"
                value={request.seat_type}
                onChange={(event) => setRequest({ ...request, seat_type: event.target.value })}
              >
                <option value="ngoi_mem">Ngồi mềm điều hòa</option>
                <option value="giuong_nam_k6">Giường nằm K6</option>
              </select>
            </label>
            <label className="field">
              <span>Ngày đi</span>
              <Input
                type="date"
                value={request.service_date}
                onChange={(event) => setRequest({ ...request, service_date: event.target.value })}
                required
              />
            </label>
          </div>
          <div className="quote-form-actions">
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Đang tính giá..." : "Lấy báo giá"}
            </Button>
            {error ? <p className="error" role="alert">{error}</p> : null}
          </div>
        </form>
      </SectionCard>

      {quote ? (
        <div className="two-up" aria-live="polite">
          <SectionCard title="Kết quả báo giá" subtitle={`${quote.origin} → ${quote.destination}`}>
            <div className="quote-card">
              <div>
                <span className="mini-label">Giá đề xuất</span>
                <strong className="quote-price">{formatMoney(quote.final_price)}</strong>
              </div>
              <div className="quote-meta">
                <article>
                  <span>Khả dụng</span>
                  <strong>Còn {quote.availability} chỗ</strong>
                </article>
                <article>
                  <span>Chi phí cơ hội</span>
                  <strong>{formatMoney(quote.opportunity_cost)}</strong>
                </article>
                <article>
                  <span>Quyết định</span>
                  <strong>{quote.decision === "accepted" ? "Chấp nhận" : "Từ chối"}</strong>
                </article>
              </div>
            </div>
          </SectionCard>

          <SectionCard title="Thẻ diễn giải giá" subtitle="Kết quả ánh xạ chặng và kiểm tra bid price.">
            <div className="explain-card">
              <p>
                Nút cổ chai: {quote.explanation.bottleneck_segment ?? "Không xác định"}. Giá vé được
                đối chiếu với tổng bid price của toàn bộ chặng OD.
              </p>
              <ul className="tag-list">
                <li>Quote #{quote.quote_id}</li>
                <li>{Object.keys(quote.explanation.segment_bid_prices).length} chặng</li>
                {quote.explanation.applied_policies.map((policy) => <li key={policy}>{policy}</li>)}
              </ul>
            </div>
          </SectionCard>
        </div>
      ) : null}
    </div>
  );
}
