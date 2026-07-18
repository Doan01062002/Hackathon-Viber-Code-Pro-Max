"use client";

import { type FormEvent, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getBookingDetail } from "@/features/booking/api/bookingApi";
import type { BookingDetail } from "@/features/booking/types";
import { ApiError } from "@/lib/api/client";

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

const bookingStatus = {
  held: { label: "Đang giữ chỗ", className: "border-amber-200 bg-amber-50 text-amber-700" },
  confirmed: { label: "Đã xác nhận", className: "border-emerald-200 bg-emerald-50 text-emerald-700" },
  cancelled: { label: "Đã hủy", className: "border-red-200 bg-red-50 text-red-700" },
  refunded: { label: "Đã hoàn tiền", className: "border-sky-200 bg-sky-50 text-sky-700" },
} satisfies Record<BookingDetail["status"], { label: string; className: string }>;

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

export function TicketDetailsScreen() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryCode = searchParams.get("code")?.trim().toUpperCase() ?? "";
  const [bookingCode, setBookingCode] = useState(queryCode);
  const [ticket, setTicket] = useState<BookingDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setBookingCode(queryCode);
    if (!queryCode) {
      setTicket(null);
      setError(null);
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    void loadTicket(queryCode, controller.signal);
    return () => controller.abort();
  }, [queryCode]);

  async function loadTicket(code: string, signal?: AbortSignal) {
    setLoading(true);
    setError(null);
    setTicket(null);
    try {
      setTicket(await getBookingDetail(code, signal));
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") return;
      if (caught instanceof ApiError && caught.status === 404) {
        setError("Không tìm thấy mã đặt vé này trong hệ thống.");
      } else {
        setError(caught instanceof Error ? caught.message : "Không tải được chi tiết vé.");
      }
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanCode = bookingCode.trim().toUpperCase();
    if (!cleanCode) {
      setError("Vui lòng nhập mã đặt vé.");
      setTicket(null);
      return;
    }
    if (cleanCode === queryCode) {
      void loadTicket(cleanCode);
      return;
    }
    router.push(`/ticket-details?code=${encodeURIComponent(cleanCode)}`);
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-outline-variant bg-white p-6 shadow-sm">
        <h2 className="flex items-center gap-2 text-xl font-black text-on-surface">
          <span className="material-symbols-outlined text-2xl text-primary">confirmation_number</span>
          Tra cứu vé và hành trình
        </h2>
        <p className="mt-1 text-xs font-medium text-on-surface-variant">
          Dữ liệu vé, lịch chạy và chỗ ngồi được lấy trực tiếp từ hệ thống đặt vé.
        </p>
      </div>

      <div className="grid grid-cols-12 gap-6">
        <aside className="col-span-12 space-y-4 lg:col-span-4">
          <form onSubmit={handleSearch} className="space-y-4 rounded-2xl border border-outline-variant bg-white p-6 shadow-sm">
            <h3 className="flex items-center gap-2 text-sm font-bold text-on-surface">
              <span className="material-symbols-outlined text-sm text-primary">search</span>
              Tra cứu đặt vé
            </h3>
            <label className="block space-y-1">
              <span className="text-[10px] font-bold uppercase text-on-surface-variant">Mã đặt vé</span>
              <input
                value={bookingCode}
                onChange={(event) => setBookingCode(event.target.value.toUpperCase())}
                placeholder="Nhập mã trên vé của bạn"
                autoComplete="off"
                className="w-full rounded-lg border border-outline-variant bg-surface-container-low px-3 py-2.5 text-xs font-bold uppercase outline-none transition-colors focus:border-primary"
              />
            </label>
            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-xs font-black text-white transition-all hover:brightness-110 disabled:cursor-wait disabled:opacity-70"
            >
              {loading ? <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" /> : null}
              {loading ? "Đang tra cứu..." : "Xem chi tiết vé"}
            </button>
          </form>

          <div className="rounded-2xl border border-primary/15 bg-primary/5 p-5">
            <h4 className="flex items-center gap-1.5 text-xs font-black text-primary">
              <span className="material-symbols-outlined text-sm">database</span>
              Thông tin từ cơ sở dữ liệu
            </h4>
            <p className="mt-2 text-[11px] font-medium leading-relaxed text-on-surface-variant">
              Trang chỉ hiển thị dữ liệu đã lưu của mã vé: chuyến tàu, thời gian, hành trình, giá vé và chỗ được phân. Hệ thống không tự tạo thông tin hành khách khi cơ sở dữ liệu chưa lưu trường này.
            </p>
          </div>
        </aside>

        <section className="col-span-12 lg:col-span-8">
          {loading ? (
            <EmptyState icon="progress_activity" title="Đang tải chi tiết vé" description="Hệ thống đang đồng bộ dữ liệu đặt vé." spinning />
          ) : error ? (
            <EmptyState icon="search_off" title="Không thể hiển thị vé" description={error} tone="error" />
          ) : ticket ? (
            <TicketCard ticket={ticket} />
          ) : (
            <EmptyState icon="confirmation_number" title="Chưa có vé được chọn" description="Nhập mã đặt vé để xem thông tin hành trình và chỗ ngồi." />
          )}
        </section>
      </div>
    </div>
  );
}

function TicketCard({ ticket }: { ticket: BookingDetail }) {
  const status = bookingStatus[ticket.status];
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
              <InfoLine label="Loại chỗ" value={ticket.seat_type_name} />
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

        <div>
          <div className="flex items-center justify-between gap-3">
            <SectionTitle icon="route">Lịch trình chi tiết</SectionTitle>
            <span className={`rounded-full border px-2.5 py-1 text-[9px] font-black uppercase ${status.className}`}>{status.label}</span>
          </div>
          <div className="mt-4 space-y-0">
            {ticket.segments.map((segment, index) => (
              <div key={segment.segment_id} className="grid grid-cols-[1.5rem_1fr] gap-3">
                <div className="flex flex-col items-center">
                  <span className="mt-1 h-3 w-3 rounded-full border-2 border-primary bg-white" />
                  {index < ticket.segments.length - 1 ? <span className="min-h-12 w-px flex-1 bg-primary/25" /> : null}
                </div>
                <div className="pb-5">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <p className="text-xs font-black text-on-surface">
                      {segment.origin_name} → {segment.destination_name}
                    </p>
                    <span className="text-[10px] font-bold text-on-surface-variant">{segment.distance_km.toLocaleString("vi-VN")} km</span>
                  </div>
                  <p className="mt-1 text-[10px] font-semibold text-on-surface-variant">
                    {formatDateTime(segment.departure_at)} → {formatDateTime(segment.arrival_at)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-dashed border-outline-variant pt-5">
          <div className="text-[10px] font-semibold text-on-surface-variant">
            <p>ID đặt vé: #{ticket.booking_id} · ID chuyến: #{ticket.trip_id}</p>
            {ticket.status === "held" && ticket.expires_at ? <p>Giữ chỗ đến: {formatDateTime(ticket.expires_at)}</p> : null}
          </div>
          <span className="font-mono text-xs font-black tracking-widest text-primary">{ticket.booking_code}</span>
        </footer>
      </div>
    </article>
  );
}

function SectionTitle({ icon, children }: { icon: string; children: string }) {
  return (
    <h4 className="flex items-center gap-1.5 text-xs font-black uppercase tracking-wider text-on-surface">
      <span className="material-symbols-outlined text-sm text-primary">{icon}</span>
      {children}
    </h4>
  );
}

function InfoBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-outline-variant/60 bg-slate-50 px-4 py-3">
      <span className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant">{label}</span>
      <p className="mt-1 text-xs font-black text-on-surface">{value}</p>
    </div>
  );
}

function InfoLine({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div>
      <span className="block text-[9px] font-bold text-on-surface-variant">{label}</span>
      <span className={`mt-0.5 block text-xs font-black ${highlight ? "text-primary" : "text-on-surface"}`}>{value}</span>
    </div>
  );
}

function EmptyState({ icon, title, description, tone = "neutral", spinning }: { icon: string; title: string; description: string; tone?: "neutral" | "error"; spinning?: boolean }) {
  return (
    <div className="rounded-2xl border border-outline-variant bg-white p-12 text-center shadow-sm">
      <span className={`material-symbols-outlined text-5xl ${spinning ? "animate-spin" : ""} ${tone === "error" ? "text-red-500" : "text-slate-300"}`}>{icon}</span>
      <p className="mt-3 text-sm font-black text-on-surface">{title}</p>
      <p className="mt-1 text-xs font-medium text-on-surface-variant">{description}</p>
    </div>
  );
}
