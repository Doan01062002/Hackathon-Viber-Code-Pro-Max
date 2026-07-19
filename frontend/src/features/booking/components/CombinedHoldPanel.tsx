"use client";

import { Button } from "@/components/ui/Button";
import { formatLegWindow, formatMoney } from "@/features/booking/format";
import { formatCountdown, isSeatChange } from "@/features/booking/hooks/combinedState";
import type { CombinedBooking } from "@/features/booking/types";

/** Đồng hồ đếm ngược hạn giữ chỗ. Mốc do server trả về, client chỉ hiển thị lại. */
function HoldCountdown({ secondsLeft }: { secondsLeft: number }) {
  const urgent = secondsLeft <= 60;
  return (
    <div
      className={`flex items-center justify-between rounded-xl border px-3 py-2 ${
        urgent ? "border-red-200 bg-red-50" : "border-amber-200 bg-amber-50"
      }`}
    >
      <span className={`text-[10.5px] font-black ${urgent ? "text-red-700" : "text-amber-700"}`}>
        Thời gian giữ chỗ còn lại
      </span>
      <span
        className={`font-mono text-base font-black tabular-nums ${urgent ? "text-red-700" : "text-amber-700"}`}
        role="timer"
        aria-live={urgent ? "assertive" : "off"}
      >
        {formatCountdown(secondsLeft)}
      </span>
    </div>
  );
}

export type CombinedHoldPanelProps = {
  booking: CombinedBooking;
  secondsLeft: number;
  expired: boolean;
  confirming: boolean;
  error: string | null;
  onConfirm: () => void;
  onRestart: () => void;
};

export function CombinedHoldPanel({
  booking,
  secondsLeft,
  expired,
  confirming,
  error,
  onConfirm,
  onRestart,
}: CombinedHoldPanelProps) {
  if (expired) {
    return (
      <div className="space-y-2.5 rounded-xl border border-red-200 bg-red-50 p-3">
        <p className="text-[11px] font-black text-red-700">Đã hết thời gian giữ chỗ</p>
        <p className="text-[10.5px] font-semibold text-red-700/90">
          Nhóm vé {booking.group_code} đã được giải phóng. Vui lòng tìm lại phương án ghép chặng.
        </p>
        <button
          type="button"
          onClick={onRestart}
          className="w-full rounded-lg border border-red-200 bg-white py-1.5 text-[10.5px] font-extrabold text-red-700 transition-all hover:bg-red-100"
        >
          Tìm lại phương án
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-2.5">
      <HoldCountdown secondsLeft={secondsLeft} />

      <div className="space-y-2.5 rounded-xl border border-purple-200 bg-purple-50/70 p-3 text-[11px] font-semibold text-slate-700">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-black uppercase tracking-wider text-purple-700">
            Hành trình ghép chặng
          </span>
          <span className="font-mono text-[10px] font-black text-purple-700">{booking.group_code}</span>
        </div>

        {booking.legs.map((leg) => (
          <div key={leg.sequence_no} className="space-y-0.5 border-b border-purple-100/60 pb-1.5 last:border-0 last:pb-0">
            <p className="text-xs font-black text-on-surface">
              {leg.origin_name} → {leg.destination_name}{" "}
              <span className="font-bold text-on-surface-variant">
                ({formatLegWindow(leg.departure_at, leg.arrival_at)})
              </span>
            </p>
            <p className="text-on-surface-variant">
              Toa {leg.coach_no} • Chỗ <span className="font-extrabold text-purple-700">{leg.seat_no}</span> •{" "}
              <span className="font-mono">{leg.booking_code}</span>
            </p>
            {isSeatChange(leg) ? (
              <p className="mt-0.5 text-[9.5px] font-bold italic text-amber-700">
                Đổi sang Toa {leg.coach_no} chỗ {leg.seat_no} tại ga {leg.origin_name}.
              </p>
            ) : null}
          </div>
        ))}
      </div>

      <div className="flex items-end justify-between pt-1">
        <span className="font-bold text-on-surface-variant">Tổng tiền vé ghép</span>
        <span className="font-mono text-lg font-black text-primary">{formatMoney(booking.total_price)}</span>
      </div>

      {error ? (
        <p className="rounded-lg border border-red-200 bg-red-50 p-2 text-[10.5px] font-bold text-red-700">
          {error}
        </p>
      ) : null}

      <Button className="w-full py-2.5" disabled={confirming} onClick={onConfirm}>
        {confirming ? "Đang xác nhận..." : "Xác nhận thanh toán"}
      </Button>
    </div>
  );
}
