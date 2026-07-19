"use client";

import { formatLegWindow, formatMoney } from "@/features/booking/format";
import { isSeatChange } from "@/features/booking/hooks/combinedState";
import type { CombinedJourneyLegOption, CombinedJourneyOption } from "@/features/booking/types";

/**
 * Ghi chú đổi chỗ tại ga chuyển — thay cho chuỗi hardcode trước đây.
 *
 * Chặng đầu luôn có keep_previous_seat = false vì không có chặng trước để giữ,
 * nên không coi đó là một lần đổi chỗ.
 */
function transferNote(leg: CombinedJourneyLegOption): string | null {
  if (!isSeatChange(leg)) return null;
  return `Đổi sang Toa ${leg.coach_no} chỗ ${leg.seat_no} tại ga ${leg.origin_name}.`;
}

function LegRow({ leg }: { leg: CombinedJourneyLegOption }) {
  const note = transferNote(leg);
  return (
    <div className="space-y-0.5 border-b border-purple-100/60 pb-1.5 last:border-0 last:pb-0">
      <p className="text-xs font-black text-on-surface">
        {leg.origin_name} → {leg.destination_name}{" "}
        <span className="font-bold text-on-surface-variant">
          ({formatLegWindow(leg.departure_at, leg.arrival_at)})
        </span>
      </p>
      <p className="font-semibold text-on-surface-variant">
        Toa {leg.coach_no} • Chỗ <span className="font-extrabold text-purple-700">{leg.seat_no}</span> •{" "}
        {leg.seat_type_name}
      </p>
      {note ? <p className="mt-0.5 text-[9.5px] font-bold italic text-amber-700">{note}</p> : null}
    </div>
  );
}

function OptionCard({
  option,
  selected,
  onSelect,
}: {
  option: CombinedJourneyOption;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={`w-full rounded-xl border p-3 text-left transition-all ${
        selected
          ? "border-purple-400 bg-purple-50 shadow-sm ring-1 ring-purple-300"
          : "border-outline-variant bg-white hover:border-purple-200 hover:bg-purple-50/40"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-0.5">
          {/* transfer_count là SỐ LẦN CHUYỂN, không phải số chặng — số chặng = legs.length. */}
          <p className="text-[11px] font-black text-on-surface">
            Tàu {option.train_code} • {option.legs.length} chặng
          </p>
          <p className="text-[10px] font-semibold text-on-surface-variant">
            {option.transfer_count === 0 ? "Đi thẳng" : `Chuyển ${option.transfer_count} lần`}
            {" • "}
            {option.seat_change_count === 0
              ? "giữ nguyên chỗ"
              : `đổi chỗ ${option.seat_change_count} lần`}
          </p>
        </div>
        <span className="whitespace-nowrap font-mono text-sm font-black text-primary">
          {formatMoney(option.estimated_total_price)}
        </span>
      </div>

      <div className="mt-2.5 space-y-2 rounded-lg bg-white/70 p-2.5 text-[11px]">
        {option.legs.map((leg) => (
          <LegRow key={leg.sequence_no} leg={leg} />
        ))}
      </div>
    </button>
  );
}

export type CombinedOptionListProps = {
  options: CombinedJourneyOption[];
  selectedKey: string | null;
  loading: boolean;
  error: string | null;
  onSelect: (optionKey: string) => void;
  onRetry: () => void;
};

export function CombinedOptionList({
  options,
  selectedKey,
  loading,
  error,
  onSelect,
  onRetry,
}: CombinedOptionListProps) {
  if (loading) {
    return (
      <div className="space-y-2" role="status" aria-live="polite">
        <p className="text-[10px] font-black uppercase tracking-wider text-purple-700">
          Đang tìm phương án ghép chặng...
        </p>
        {[0, 1].map((index) => (
          <div key={index} className="h-24 animate-pulse rounded-xl border border-outline-variant bg-slate-100" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-2 rounded-xl border border-red-200 bg-red-50 p-3">
        <p className="text-[11px] font-bold text-red-700">{error}</p>
        <button
          type="button"
          onClick={onRetry}
          className="w-full rounded-lg border border-red-200 bg-white py-1.5 text-[10.5px] font-extrabold text-red-700 transition-all hover:bg-red-100"
        >
          Thử lại
        </button>
      </div>
    );
  }

  if (options.length === 0) {
    return (
      <div className="rounded-xl border border-outline-variant bg-slate-50 p-4 text-center">
        <p className="text-[11px] font-bold text-on-surface-variant">
          Không tìm được phương án ghép chặng cho hành trình này.
        </p>
        <p className="mt-1 text-[10px] font-medium text-on-surface-variant">
          Thử đổi ngày đi hoặc chọn loại chỗ khác.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-[10px] font-black uppercase tracking-wider text-purple-700">
        {options.length} phương án ghép chặng
      </p>
      {options.map((option) => (
        <OptionCard
          key={option.option_key}
          option={option}
          selected={option.option_key === selectedKey}
          onSelect={() => onSelect(option.option_key)}
        />
      ))}
    </div>
  );
}
