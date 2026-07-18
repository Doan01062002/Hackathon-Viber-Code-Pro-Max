"use client";

import React, { FormEvent, useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { SearchableStationSelect } from "@/components/ui/SearchableStationSelect";
import { useRailCatalog } from "@/features/catalog/hooks/useRailCatalog";
import { createPricingQuote } from "@/features/quote/api/quoteApi";
import type { PricingQuoteRequest, PricingQuoteResponse } from "@/features/quote/types";
import { RouteMap, MOCK_ROUTE_SEGMENTS } from "@/features/rail-ui/components/RouteMap";
import { STATION_OPTIONS, toStationOptions } from "@/features/rail-ui/stations";
import { ApiError } from "@/lib/api/client";

const initialRequest: PricingQuoteRequest = {
  origin: "HAN",
  destination: "DAN",
  seat_type: "giuong_nam_k6",
  service_date: "2025-12-30",
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
  const { catalog, error: catalogError } = useRailCatalog();
  const [request, setRequest] = useState<PricingQuoteRequest>(initialRequest);
  const [quote, setQuote] = useState<PricingQuoteResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const stationOptions = catalog ? toStationOptions(catalog.stations) : STATION_OPTIONS;

  const translatePolicy = (policy: string) => {
    const clean = policy.replace(/_ENFORCED|_CAPPED/g, "");
    if (clean === "FLOOR_PRICE") return "Bảo vệ giá sàn";
    if (clean === "CEILING_PRICE") return "Giới hạn giá trần";
    if (clean === "MAX_DAILY_DELTA") return "Biên độ ngày tối đa";
    return clean;
  };

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

  useEffect(() => {
    if (!catalog) return;

    setRequest((current) => ({
      ...current,
      origin: catalog.stations.some((station) => station.code === current.origin)
        ? current.origin
        : (catalog.stations[0]?.code ?? current.origin),
      destination: catalog.stations.some((station) => station.code === current.destination)
        ? current.destination
        : (catalog.stations[1]?.code ?? current.destination),
      service_date:
        catalog.service_date_max && current.service_date > catalog.service_date_max
          ? catalog.service_date_max
          : current.service_date,
    }));
  }, [catalog]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      setQuote(await createPricingQuote(request));
    } catch (caught) {
      setQuote(null);
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Không thể kết nối hệ thống tính toán giá động.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {error || catalogError ? (
        <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-lg text-yellow-700 text-xs font-semibold">
          Cảnh báo: {error ?? catalogError}. Đang dùng dữ liệu dự phòng.
        </div>
      ) : null}

      <div className="grid grid-cols-12 gap-6">
        <section className="col-span-12 lg:col-span-8 space-y-6">
          <div className="bg-white border border-outline-variant rounded-xl p-6 shadow-sm space-y-4">
            <h3 className="font-bold text-sm text-on-surface flex items-center gap-2">
              <span className="material-symbols-outlined text-primary text-sm">payments</span>
              Báo giá hành trình
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <SearchableStationSelect
                  label="Ga đi"
                  options={stationOptions}
                  value={request.origin}
                  onChange={(origin) => setRequest({ ...request, origin })}
                />
                <SearchableStationSelect
                  label="Ga đến"
                  align="right"
                  options={stationOptions.filter((option) => option.code !== request.origin)}
                  value={request.destination}
                  onChange={(destination) => setRequest({ ...request, destination })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant">
                    Loại chỗ
                  </label>
                  <select
                    className="w-full bg-surface-container-low border border-outline-variant rounded-lg py-2 px-3 text-xs font-semibold outline-none focus:ring-1 focus:ring-primary"
                    value={request.seat_type}
                    onChange={(event) => setRequest({ ...request, seat_type: event.target.value })}
                  >
                    {(catalog?.seat_types ?? [
                      { code: "ngoi_mem", name: "Ngồi mềm điều hòa" },
                      { code: "giuong_nam_k6", name: "Giường nằm K6" },
                    ]).map((seatType) => (
                      <option key={seatType.code} value={seatType.code}>{seatType.name}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant">
                    Ngày đi
                  </label>
                  <Input
                    type="date"
                    min={catalog?.service_date_min ?? undefined}
                    max={catalog?.service_date_max ?? undefined}
                    value={request.service_date}
                    onChange={(event) => setRequest({ ...request, service_date: event.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <Button type="submit" disabled={isLoading}>
                  {isLoading ? "Đang tính toán..." : "Lấy báo giá tối ưu"}
                </Button>
              </div>
            </form>
          </div>

          <RouteMap
            segments={MOCK_ROUTE_SEGMENTS}
            selectedOrigin={request.origin}
            selectedDestination={request.destination}
          />
        </section>

        <aside className="col-span-12 lg:col-span-4 space-y-6">
          <div
            className={`bg-white border border-outline-variant rounded-xl p-5 shadow-sm transition-opacity duration-200 ${
              isLoading ? "opacity-50" : "opacity-100"
            }`}
          >
            <h3 className="font-bold text-xs text-on-surface uppercase tracking-wider mb-3 border-b border-outline-variant/30 pb-2">
              Kết quả báo giá tối ưu
            </h3>

            {quote ? (
              <div className="space-y-4">
                <div>
                  <span className="text-[10px] text-on-surface-variant font-bold uppercase">
                    Giá đề xuất tối ưu
                  </span>
                  <p className="text-2xl font-black text-primary font-mono mt-1">
                    {formatMoney(quote.final_price)}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4 text-xs font-semibold pt-1">
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-outline-variant/30">
                    <span className="text-[9px] text-on-surface-variant font-bold uppercase">
                      Quyết định
                    </span>
                    <p
                      className={`font-extrabold mt-0.5 ${
                        quote.decision === "accepted" ? "text-green-600" : "text-red-600"
                      }`}
                    >
                      {quote.decision === "accepted"
                        ? "Chấp nhận (AI)"
                        : quote.decision === "rejected"
                          ? "Từ chối (AI)"
                          : "Chặn bán (AI)"}
                    </p>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded-lg border border-outline-variant/30">
                    <span className="text-[9px] text-on-surface-variant font-bold uppercase">
                      Chi phí cơ hội
                    </span>
                    <p className="font-bold mt-0.5 text-on-surface font-mono">
                      {formatMoney(quote.opportunity_cost)}
                    </p>
                  </div>
                </div>

                <div className="text-[10px] text-on-surface-variant font-semibold bg-slate-50/50 p-2 rounded border border-dashed border-outline-variant flex justify-between">
                  <span>Khả dụng:</span>
                  <span className="font-bold text-primary">Còn {quote.availability} chỗ</span>
                </div>
              </div>
            ) : (
              <div className="text-xs font-semibold text-on-surface-variant py-4 text-center">
                Vui lòng điền thông tin và lấy báo giá tối ưu.
              </div>
            )}
          </div>

          {quote ? (
            <div className="bg-white border border-outline-variant rounded-xl p-5 shadow-sm space-y-3">
              <h3 className="font-bold text-xs text-on-surface uppercase tracking-wider border-b border-outline-variant/30 pb-2">
                Diễn giải báo giá
              </h3>

              <div className="text-xs font-semibold leading-relaxed text-on-surface-variant space-y-3">
                <p>
                  Nút cổ chai:{" "}
                  <strong className="text-on-surface">
                    {quote.explanation.bottleneck_segment ?? "Không xác định"}
                  </strong>
                  . Giá vé được đối chiếu với tổng giá chào mua (bid price) của toàn bộ chặng O-D.
                </p>
                <div className="pt-2">
                  <span className="text-[10px] font-bold text-on-surface-variant uppercase">
                    Chính sách áp dụng:
                  </span>
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {quote.explanation.applied_policies.length > 0 ? (
                      quote.explanation.applied_policies.map((policy) => (
                        <span
                          key={policy}
                          className="bg-yellow-50 text-yellow-700 border border-yellow-300 px-2 py-0.5 rounded text-[8px] font-extrabold uppercase"
                        >
                          {translatePolicy(policy)}
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
            </div>
          ) : null}

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
              <p className="text-sm font-semibold">Đang theo dõi 4 điểm tắc nghẽn</p>
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
