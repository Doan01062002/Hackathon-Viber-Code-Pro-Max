"use client";

import { type FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getBookingDetail } from "@/features/booking/api/bookingApi";
import { getCombinedBooking } from "@/features/booking/api/combinedBookingApi";
import { CombinedTicketCard } from "@/features/booking/components/CombinedTicketCard";
import {
  EmptyState,
  InfoBox,
  InfoLine,
  SectionTitle,
  ticketStatusStyles,
} from "@/features/booking/components/TicketPrimitives";
import type { BookingDetail, CombinedBooking } from "@/features/booking/types";
import { ApiError } from "@/lib/api/client";
import { getSeatTypeName } from "@/lib/utils";

const moneyFormatter = new Intl.NumberFormat("vi-VN", {
  style: "currency",
  currency: "VND",
  maximumFractionDigits: 0,
});

const dateFormatter = new Intl.DateTimeFormat("vi-VN", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  timeZone: "Asia/Ho_Chi_Minh",
});

const dateTimeFormatter = new Intl.DateTimeFormat("vi-VN", {
  hour: "2-digit",
  minute: "2-digit",
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  timeZone: "Asia/Ho_Chi_Minh",
});

const tripStatus: Record<BookingDetail["trip_status"], string> = {
  scheduled: "Sắp khởi hành",
  boarding: "Đang đón khách",
  departed: "Đã khởi hành",
  completed: "Đã hoàn thành",
  cancelled: "Đã hủy chuyến",
};

function formatDate(value: string) {
  return dateFormatter.format(new Date(`${value}T00:00:00+07:00`));
}

function formatDateTime(value: string) {
  return dateTimeFormatter.format(new Date(value));
}

/**
 * Vé thường tra theo booking_code (?code=), vé ghép chặng tra theo group_code
 * (?groupCode=). Hai loại mã khác nhau nên gọi hai endpoint khác nhau.
 */
type LookupKind = "single" | "combined";

type TicketResult =
  | { kind: "single"; data: BookingDetail }
  | { kind: "combined"; data: CombinedBooking };

export function TicketDetailsScreen() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryCode = searchParams.get("code")?.trim().toUpperCase() ?? "";
  const queryGroupCode = searchParams.get("groupCode")?.trim().toUpperCase() ?? "";

  const activeKind: LookupKind = queryGroupCode ? "combined" : "single";
  const activeCode = queryGroupCode || queryCode;

  const [kind, setKind] = useState<LookupKind>(activeKind);
  const [code, setCode] = useState(activeCode);
  const [result, setResult] = useState<TicketResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTicket = useCallback(
    async (lookupKind: LookupKind, lookupCode: string, signal?: AbortSignal) => {
      setLoading(true);
      setError(null);
      setResult(null);
      try {
        const data =
          lookupKind === "combined"
            ? await getCombinedBooking(lookupCode, signal)
            : await getBookingDetail(lookupCode, signal);
        setResult(
          lookupKind === "combined"
            ? { kind: "combined", data: data as CombinedBooking }
            : { kind: "single", data: data as BookingDetail },
        );
      } catch (caught) {
        if (caught instanceof DOMException && caught.name === "AbortError") return;
        if (caught instanceof ApiError && caught.status === 404) {
          setError(
            lookupKind === "combined"
              ? "Không tìm thấy nhóm vé ghép chặng này trong hệ thống."
              : "Không tìm thấy mã đặt vé này trong hệ thống.",
          );
        } else {
          setError(caught instanceof Error ? caught.message : "Không tải được chi tiết vé.");
        }
      } finally {
        if (!signal?.aborted) setLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    setKind(activeKind);
    setCode(activeCode);
    if (!activeCode) {
      setResult(null);
      setError(null);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    void loadTicket(activeKind, activeCode, controller.signal);
    return () => controller.abort();
  }, [activeKind, activeCode, loadTicket]);

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanCode = code.trim().toUpperCase();
    if (!cleanCode) {
      setError(kind === "combined" ? "Vui lòng nhập mã nhóm vé." : "Vui lòng nhập mã đặt vé.");
      setResult(null);
      return;
    }
    if (kind === activeKind && cleanCode === activeCode) {
      void loadTicket(kind, cleanCode);
      return;
    }
    const param = kind === "combined" ? "groupCode" : "code";
    router.push(`/ticket-details?${param}=${encodeURIComponent(cleanCode)}`);
  }

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
        <aside className="col-span-12 space-y-4 lg:col-span-4">
          <form
            onSubmit={handleSearch}
            className="space-y-4 rounded-2xl border border-outline-variant bg-white p-6 shadow-sm"
          >
            <h3 className="flex items-center gap-2 text-sm font-bold text-on-surface">
              <span className="material-symbols-outlined text-sm text-primary">search</span>
              Tra cứu đặt vé
            </h3>

            <div className="grid grid-cols-2 gap-1 rounded-lg border border-outline-variant bg-surface-container-low p-1">
              {(["single", "combined"] as const).map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setKind(option)}
                  aria-pressed={kind === option}
                  className={`rounded-md px-2 py-1.5 text-[10px] font-black uppercase tracking-wider transition-all ${
                    kind === option
                      ? "bg-primary text-white shadow-sm"
                      : "text-on-surface-variant hover:bg-slate-100"
                  }`}
                >
                  {option === "single" ? "Vé thường" : "Vé ghép chặng"}
                </button>
              ))}
            </div>

            <label className="block space-y-1">
              <span className="text-[10px] font-bold uppercase text-on-surface-variant">
                {kind === "combined" ? "Mã nhóm vé" : "Mã đặt vé"}
              </span>
              <input
                value={code}
                onChange={(event) => setCode(event.target.value.toUpperCase())}
                placeholder={kind === "combined" ? "Nhập mã nhóm vé ghép" : "Nhập mã trên vé của bạn"}
                autoComplete="off"
                className="w-full rounded-lg border border-outline-variant bg-surface-container-low px-3 py-2.5 text-xs font-bold uppercase outline-none transition-colors focus:border-primary"
              />
            </label>

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-xs font-black text-white transition-all hover:brightness-110 disabled:cursor-wait disabled:opacity-70"
            >
              {loading ? (
                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : null}
              {loading ? "Đang tra cứu..." : "Xem chi tiết vé"}
            </button>
          </form>

          <div className="rounded-2xl border border-primary/15 bg-primary/5 p-5">
            <h4 className="flex items-center gap-1.5 text-xs font-black text-primary">
              <span className="material-symbols-outlined text-sm">database</span>
              Thông tin từ cơ sở dữ liệu
            </h4>
            <p className="mt-2 text-[11px] font-medium leading-relaxed text-on-surface-variant">
              Trang chỉ hiển thị dữ liệu đã lưu của mã vé: chuyến tàu, thời gian, hành trình, giá vé và
              chỗ được phân. Hệ thống không tự tạo thông tin hành khách khi cơ sở dữ liệu chưa lưu
              trường này.
            </p>
          </div>
        </aside>

        <section className="col-span-12 lg:col-span-8">
          {loading ? (
            <EmptyState
              icon="progress_activity"
              title="Đang tải chi tiết vé"
              description="Hệ thống đang đồng bộ dữ liệu đặt vé."
              spinning
            />
          ) : error ? (
            <EmptyState icon="search_off" title="Không thể hiển thị vé" description={error} tone="error" />
          ) : result?.kind === "combined" ? (
            <CombinedTicketCard booking={result.data} />
          ) : result?.kind === "single" ? (
            <TicketCard ticket={result.data} />
          ) : (
            <EmptyState
              icon="confirmation_number"
              title="Chưa có vé được chọn"
              description="Nhập mã đặt vé để xem thông tin hành trình và chỗ ngồi."
            />
          )}
        </section>
      </div>
    </div>
  );
}

function TicketCard({ ticket }: { ticket: BookingDetail }) {
  const status = ticketStatusStyles[ticket.status];
  return (
    <article className="animate-fade-in overflow-hidden rounded-2xl border border-outline-variant bg-white shadow-sm">
      <header className="flex flex-col gap-5 bg-primary p-6 text-white sm:flex-row sm:items-start sm:justify-between">
        <div>
          <span className="rounded-full bg-white/20 px-2.5 py-1 text-[9px] font-black uppercase tracking-wider">Vé tàu điện tử</span>
          <h3 className="mt-3 text-xl font-black">
            {ticket.origin_name} <span className="opacity-60">→</span> {ticket.destination_name}
          </h3>
          <p className="mt-1 text-xs font-semibold text-white/80">
            {ticket.origin_code} → {ticket.destination_code} · {ticket.distance_km.toLocaleString("vi-VN")} km
          </p>
        </div>
        <div className="sm:text-right">
          <span className="text-[10px] font-bold uppercase tracking-widest text-white/65">Mã đặt vé</span>
          <p className="font-mono text-xl font-black tracking-wider">{ticket.booking_code}</p>
        </div>
      </header>

      <div className="space-y-6 p-6">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <InfoBox label="Tàu" value={ticket.train_name ? `${ticket.train_code} · ${ticket.train_name}` : ticket.train_code} />
          <InfoBox label="Ngày chạy" value={formatDate(ticket.service_date)} />
          <InfoBox label="Khởi hành" value={formatDateTime(ticket.departure_at)} />
          <InfoBox label="Đến nơi" value={formatDateTime(ticket.arrival_at)} />
        </div>

        <div className="grid gap-5 border-y border-outline-variant/35 py-5 md:grid-cols-2">
          <div>
            <SectionTitle icon="event_seat">Chỗ ngồi</SectionTitle>
            <div className="mt-3 grid grid-cols-2 gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <InfoLine label="Loại chỗ" value={getSeatTypeName(ticket.seat_type_name)} />
              <InfoLine label="Hạng vé" value={ticket.fare_class} />
              <InfoLine label="Toa" value={ticket.coach_no ? `Toa ${ticket.coach_no}` : "Chưa phân toa"} />
              <InfoLine label="Số chỗ" value={ticket.seat_no ?? "Chưa phân chỗ"} highlight />
            </div>
          </div>

          <div>
            <SectionTitle icon="receipt_long">Thông tin đặt vé</SectionTitle>
            <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <InfoLine label="Giá vé" value={moneyFormatter.format(ticket.booked_price)} highlight />
              <InfoLine label="Kênh đặt" value={ticket.channel ?? "Không xác định"} />
              <InfoLine label="Thời điểm đặt" value={formatDateTime(ticket.booked_at)} />
              <InfoLine label="Trạng thái chuyến" value={tripStatus[ticket.trip_status]} />
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}
