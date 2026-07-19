"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { CombinedHoldPanel } from "@/features/booking/components/CombinedHoldPanel";
import { CombinedOptionList } from "@/features/booking/components/CombinedOptionList";
import type { useCombinedBooking } from "@/features/booking/hooks/useCombinedBooking";

export type CombinedBookingPanelProps = {
  /**
   * Hook được gọi ở BookingScreen rồi truyền xuống, vì sơ đồ hành trình ở khu
   * vực chính cũng cần đọc cùng một phương án đang chọn.
   */
  combined: ReturnType<typeof useCombinedBooking>;
  origin: string;
  destination: string;
  serviceDate: string;
  seatType?: string;
  /** Đóng chế độ vé ghép, quay lại chọn ghế thường. */
  onExit: () => void;
};

/** Luồng vé ghép chặng ở cột phải: tìm phương án → giữ chỗ → xác nhận. */
export function CombinedBookingPanel({
  combined,
  origin,
  destination,
  serviceDate,
  seatType,
  onExit,
}: CombinedBookingPanelProps) {
  const router = useRouter();
  const { state, selectedOption, secondsLeft, search, selectOption, hold, confirm, reset } = combined;

  // Tìm phương án khi mở, và tìm lại nếu hành trình đổi.
  useEffect(() => {
    if (!origin || !destination || !serviceDate) return;
    void search({ origin, destination, serviceDate, seatType });
  }, [origin, destination, serviceDate, seatType, search]);

  const runSearch = () => void search({ origin, destination, serviceDate, seatType });

  async function handleConfirm() {
    const booking = await confirm();
    if (booking) {
      router.push(`/ticket-details?groupCode=${encodeURIComponent(booking.group_code)}`);
    }
  }

  const { phase, options, selectedKey, booking, error } = state;
  const searching = phase === "searching";
  const choosing = phase === "idle" || searching || phase === "options" || phase === "holding";

  return (
    <div className="space-y-3">
      {choosing ? (
        <>
          <CombinedOptionList
            options={options}
            selectedKey={selectedKey}
            loading={searching}
            error={phase === "idle" ? error : null}
            onSelect={selectOption}
            onRetry={runSearch}
          />

          {/* Lỗi giữ chỗ hiện riêng — danh sách phương án vẫn còn để chọn lại. */}
          {phase === "options" && error ? (
            <p className="rounded-lg border border-red-200 bg-red-50 p-2 text-[10.5px] font-bold text-red-700">
              {error}
            </p>
          ) : null}

          {options.length > 0 ? (
            <Button
              className="w-full py-2.5"
              disabled={!selectedOption || phase === "holding"}
              onClick={() => void hold()}
            >
              {phase === "holding"
                ? "Đang giữ chỗ..."
                : selectedOption
                  ? "Giữ chỗ hành trình này"
                  : "Chọn một phương án"}
            </Button>
          ) : null}
        </>
      ) : null}

      {booking && !choosing ? (
        <CombinedHoldPanel
          booking={booking}
          secondsLeft={secondsLeft}
          expired={phase === "expired"}
          confirming={phase === "confirming"}
          error={error}
          onConfirm={() => void handleConfirm()}
          onRestart={() => {
            reset();
            runSearch();
          }}
        />
      ) : null}

      <button
        type="button"
        onClick={() => {
          reset();
          onExit();
        }}
        className="w-full cursor-pointer rounded-lg border border-outline-variant/35 bg-slate-100 py-1.5 text-[10.5px] font-extrabold text-slate-700 transition-all hover:bg-slate-200/80"
      >
        ✕ Hủy chế độ vé ghép chặng
      </button>
    </div>
  );
}
