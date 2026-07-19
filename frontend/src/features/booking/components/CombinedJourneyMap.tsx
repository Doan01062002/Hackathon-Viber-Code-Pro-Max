"use client";

import { formatClock, formatLegWindow, formatMoney } from "@/features/booking/format";
import { isSeatChange } from "@/features/booking/hooks/combinedState";
import type { CombinedJourneyLegOption } from "@/features/booking/types";

/**
 * Sơ đồ hành trình ghép chặng — mỗi chặng một thẻ toa, chỗ được giữ được đánh dấu.
 * Toàn bộ số liệu lấy từ phương án backend trả về.
 */

export type CombinedJourneyMapLeg = Pick<
  CombinedJourneyLegOption,
  | "sequence_no"
  | "origin_name"
  | "destination_name"
  | "departure_at"
  | "arrival_at"
  | "coach_no"
  | "seat_no"
  | "seat_type_name"
  | "keep_previous_seat"
>;

function LegCard({ leg }: { leg: CombinedJourneyMapLeg }) {
  return (
    <div className="relative rounded-xl border border-outline-variant/65 bg-white p-3 shadow-sm">
      <div className="mb-2 border-b border-purple-100 pb-1.5 text-center text-[10px] font-black uppercase tracking-wider text-purple-700">
        Toa {leg.coach_no} (Chặng {leg.sequence_no}: {leg.origin_name} → {leg.destination_name})
      </div>

      <div className="flex items-center justify-center rounded border bg-slate-50 p-3">
        <div className="relative flex h-9 min-w-[3rem] items-center justify-center rounded bg-purple-600 px-3 text-[11px] font-black text-white shadow-sm ring-2 ring-purple-600 ring-offset-1">
          {leg.seat_no}
        </div>
      </div>

      <p className="mt-2 text-center text-[9px] font-bold text-on-surface-variant">
        {leg.seat_type_name} • {formatLegWindow(leg.departure_at, leg.arrival_at)}
      </p>
    </div>
  );
}

function TransferMarker({ leg }: { leg: CombinedJourneyMapLeg }) {
  if (!isSeatChange(leg)) {
    return (
      <p className="text-center text-[9.5px] font-bold text-emerald-700">
        ↓ Giữ nguyên chỗ tại ga {leg.origin_name} ({formatClock(leg.departure_at)})
      </p>
    );
  }
  return (
    <p className="text-center text-[9.5px] font-bold italic text-amber-700">
      ↓ Đổi sang Toa {leg.coach_no} chỗ {leg.seat_no} tại ga {leg.origin_name} (
      {formatClock(leg.departure_at)})
    </p>
  );
}

export type CombinedJourneyMapProps = {
  legs: CombinedJourneyMapLeg[];
  totalPrice: number | null;
  /** Hiện khi user chưa chọn phương án nào. */
  emptyHint?: string;
};

export function CombinedJourneyMap({ legs, totalPrice, emptyHint }: CombinedJourneyMapProps) {
  if (legs.length === 0) {
    return (
      <div className="flex h-36 items-center justify-center rounded-xl border border-dashed border-outline-variant text-xs font-semibold text-on-surface-variant">
        {emptyHint ?? "Chọn một phương án ghép chặng để xem sơ đồ hành trình."}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="mx-auto max-w-4xl space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-6">
        {legs.map((leg, index) => (
          <div key={leg.sequence_no} className="space-y-3">
            {index > 0 ? <TransferMarker leg={leg} /> : null}
            <LegCard leg={leg} />
          </div>
        ))}
      </div>

      <div className="overflow-hidden rounded-xl border border-outline-variant/65 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-outline-variant/45 bg-slate-50 px-4 py-2">
          <span className="text-[10px] font-black uppercase tracking-wider text-slate-500">
            Chi tiết từng chặng
          </span>
          {totalPrice != null ? (
            <span className="font-mono text-[10px] font-black text-primary">{formatMoney(totalPrice)}</span>
          ) : null}
        </div>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-xs">
            <thead>
              <tr className="border-b border-outline-variant/20 bg-slate-50/20 text-[10px] font-bold uppercase text-slate-400">
                <th className="px-4 py-2.5 font-black">Chặng</th>
                <th className="px-4 py-2.5 font-black">Phân đoạn hành trình</th>
                <th className="px-4 py-2.5 font-black">Thời gian chạy</th>
                <th className="px-4 py-2.5 font-black">Vị trí chỗ</th>
                <th className="px-4 py-2.5 font-black">Chuyển chỗ</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/20 font-semibold text-slate-700">
              {legs.map((leg) => (
                <tr key={leg.sequence_no} className="hover:bg-slate-50/40">
                  <td className="px-4 py-2.5 font-black text-purple-700">Chặng {leg.sequence_no}</td>
                  <td className="px-4 py-2.5">
                    {leg.origin_name} → {leg.destination_name}
                  </td>
                  <td className="px-4 py-2.5 font-mono">
                    {formatLegWindow(leg.departure_at, leg.arrival_at)}
                  </td>
                  <td className="px-4 py-2.5">
                    Toa {leg.coach_no} • <span className="font-black text-purple-700">{leg.seat_no}</span>
                  </td>
                  <td className="px-4 py-2.5">
                    {!isSeatChange(leg) ? (
                      <span className="font-bold text-emerald-700">Giữ nguyên chỗ</span>
                    ) : (
                      <span className="font-bold text-amber-700">Đổi tại {leg.origin_name}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
