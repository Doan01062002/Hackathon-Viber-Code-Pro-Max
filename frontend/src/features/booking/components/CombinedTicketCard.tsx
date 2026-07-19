"use client";

import { formatMoney } from "@/features/booking/format";
import {
  InfoBox,
  InfoLine,
  SectionTitle,
  ticketStatusStyles,
} from "@/features/booking/components/TicketPrimitives";
import type { CombinedBooking, CombinedBookingLeg } from "@/features/booking/types";
import { getSeatTypeName } from "@/lib/utils";

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

function formatDate(value: string) {
  return dateFormatter.format(new Date(`${value}T00:00:00+07:00`));
}

function formatDateTime(value: string) {
  return dateTimeFormatter.format(new Date(value));
}

/** Ga chuyển tàu = ga đến của chặng trước, cũng là ga đi của chặng sau. */
function transferStations(legs: CombinedBookingLeg[]): string[] {
  return legs.slice(0, -1).map((leg) => leg.destination_name);
}

function LegBlock({ leg, isLast }: { leg: CombinedBookingLeg; isLast: boolean }) {
  return (
    <div className="grid grid-cols-[1.5rem_1fr] gap-3">
      <div className="flex flex-col items-center">
        <span className="mt-1 flex h-5 w-5 items-center justify-center rounded-full border-2 border-primary bg-white text-[9px] font-black text-primary">
          {leg.sequence_no}
        </span>
        {!isLast ? <span className="min-h-16 w-px flex-1 bg-primary/25" /> : null}
      </div>

      <div className="pb-5">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <p className="text-xs font-black text-on-surface">
            {leg.origin_name} → {leg.destination_name}
          </p>
          <span className="font-mono text-[10px] font-black text-primary">
            {formatMoney(leg.booked_price)}
          </span>
        </div>

        <p className="mt-1 text-[10px] font-semibold text-on-surface-variant">
          {formatDateTime(leg.departure_at)} → {formatDateTime(leg.arrival_at)}
        </p>

        <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px] font-bold">
          <span className="rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-on-surface">
            Toa {leg.coach_no} · Chỗ {leg.seat_no}
          </span>
          <span className="rounded-md border border-slate-200 bg-slate-50 px-2 py-1 text-on-surface-variant">
            {getSeatTypeName(leg.seat_type_name)}
          </span>
          <span className="rounded-md border border-slate-200 bg-slate-50 px-2 py-1 font-mono text-on-surface-variant">
            {leg.booking_code}
          </span>
          {!leg.keep_previous_seat && leg.sequence_no > 1 ? (
            <span className="rounded-md border border-amber-200 bg-amber-50 px-2 py-1 text-amber-700">
              Đổi chỗ tại {leg.origin_name}
            </span>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export function CombinedTicketCard({ booking }: { booking: CombinedBooking }) {
  const status = ticketStatusStyles[booking.status];
  const transfers = transferStations(booking.legs);

  return (
    <article className="animate-fade-in overflow-hidden rounded-2xl border border-outline-variant bg-white shadow-sm">
      <header className="flex flex-col gap-5 bg-primary p-6 text-white sm:flex-row sm:items-start sm:justify-between">
        <div>
          <span className="rounded-full bg-white/20 px-2.5 py-1 text-[9px] font-black uppercase tracking-wider">
            Vé ghép chặng · {booking.legs.length} chặng
          </span>
          <h3 className="mt-3 text-xl font-black">
            {booking.origin_name} <span className="opacity-60">→</span> {booking.destination_name}
          </h3>
          <p className="mt-1 text-xs font-semibold text-white/80">
            {booking.origin_code} → {booking.destination_code}
            {transfers.length > 0 ? ` · Chuyển tại ${transfers.join(", ")}` : ""}
          </p>
        </div>
        <div className="sm:text-right">
          <span className="text-[10px] font-bold uppercase tracking-widest text-white/65">Mã nhóm vé</span>
          <p className="font-mono text-xl font-black tracking-wider">{booking.group_code}</p>
        </div>
      </header>

      <div className="space-y-6 p-6">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <InfoBox label="Tàu" value={booking.train_code} />
          <InfoBox label="Ngày chạy" value={formatDate(booking.service_date)} />
          <InfoBox label="Số chặng" value={`${booking.legs.length} chặng`} />
          <InfoBox
            label="Số lần chuyển"
            value={transfers.length === 0 ? "Không chuyển" : `${transfers.length} lần`}
          />
        </div>

        <div className="grid gap-5 border-y border-outline-variant/35 py-5 md:grid-cols-2">
          <div>
            <SectionTitle icon="payments">Tổng chi phí</SectionTitle>
            <div className="mt-3 grid grid-cols-2 gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <InfoLine label="Tổng tiền" value={formatMoney(booking.total_price)} highlight />
              <InfoLine label="Kênh đặt" value={booking.channel ?? "Không xác định"} />
            </div>
          </div>

          <div>
            <SectionTitle icon="receipt_long">Thông tin đặt vé</SectionTitle>
            <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <InfoLine label="Thời điểm đặt" value={formatDateTime(booking.booked_at)} />
              <InfoLine
                label="Hạn giữ chỗ"
                value={booking.expires_at ? formatDateTime(booking.expires_at) : "Không còn giữ chỗ"}
              />
            </div>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between gap-3">
            <SectionTitle icon="route">Chi tiết từng chặng</SectionTitle>
            <span className={`rounded-full border px-2.5 py-1 text-[9px] font-black uppercase ${status.className}`}>
              {status.label}
            </span>
          </div>
          <div className="mt-4 space-y-0">
            {booking.legs.map((leg, index) => (
              <LegBlock key={leg.booking_id} leg={leg} isLast={index === booking.legs.length - 1} />
            ))}
          </div>
        </div>

        <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-dashed border-outline-variant pt-5">
          <div className="text-[10px] font-semibold text-on-surface-variant">
            <p>
              ID nhóm vé: #{booking.booking_group_id} · ID chuyến: #{booking.trip_id}
            </p>
            <p>Mỗi chặng có mã vé riêng, dùng khi lên tàu từng chặng.</p>
          </div>
          <span className="font-mono text-xs font-black tracking-widest text-primary">
            {booking.group_code}
          </span>
        </footer>
      </div>
    </article>
  );
}
