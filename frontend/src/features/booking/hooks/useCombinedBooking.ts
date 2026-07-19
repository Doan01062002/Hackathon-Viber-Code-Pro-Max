"use client";

import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";

import {
  confirmCombinedBooking,
  createCombinedHold,
  searchCombinedOptions,
} from "@/features/booking/api/combinedBookingApi";
import {
  combinedReducer,
  findSelectedOption,
  initialCombinedState,
  remainingSeconds,
} from "@/features/booking/hooks/combinedState";
import type { CombinedBooking } from "@/features/booking/types";

export type CombinedSearchParams = {
  origin: string;
  destination: string;
  serviceDate: string;
  seatType?: string;
  maxTransfers?: number;
};

function messageOf(caught: unknown, fallback: string): string {
  if (caught instanceof Error) return caught.message;
  return fallback;
}

function isAbort(caught: unknown): boolean {
  return caught instanceof DOMException && caught.name === "AbortError";
}

/**
 * Điều phối luồng vé ghép: tìm phương án → giữ chỗ → xác nhận.
 *
 * Logic chuyển trạng thái nằm ở combinedState.ts (thuần, có test riêng);
 * hook này chỉ lo gọi API, huỷ request khi unmount, và chạy đồng hồ đếm ngược.
 */
export function useCombinedBooking() {
  const [state, dispatch] = useReducer(combinedReducer, initialCombinedState);
  const abortRef = useRef<AbortController | null>(null);
  const [now, setNow] = useState(() => Date.now());

  // Huỷ request đang bay khi component unmount.
  useEffect(() => () => abortRef.current?.abort(), []);

  const nextSignal = useCallback(() => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    return controller.signal;
  }, []);

  const search = useCallback(
    async (params: CombinedSearchParams) => {
      const signal = nextSignal();
      dispatch({ type: "SEARCH_START" });
      try {
        const result = await searchCombinedOptions(params, signal);
        dispatch({ type: "SEARCH_SUCCESS", options: result.options });
      } catch (caught) {
        if (isAbort(caught)) return;
        dispatch({ type: "SEARCH_FAILURE", message: messageOf(caught, "Không tìm được phương án ghép chặng.") });
      }
    },
    [nextSignal],
  );

  const selectOption = useCallback((optionKey: string) => {
    dispatch({ type: "SELECT_OPTION", optionKey });
  }, []);

  const hold = useCallback(async () => {
    const option = findSelectedOption(state);
    if (!option) return;

    const signal = nextSignal();
    dispatch({ type: "HOLD_START" });
    try {
      const booking = await createCombinedHold(
        {
          gap_combination_ids: option.legs.map((leg) => leg.gap_combination_id),
          channel: "web",
        },
        signal,
      );
      dispatch({ type: "HOLD_SUCCESS", booking });
    } catch (caught) {
      if (isAbort(caught)) return;
      dispatch({ type: "HOLD_FAILURE", message: messageOf(caught, "Không giữ được chỗ cho hành trình này.") });
    }
  }, [nextSignal, state]);

  /** Trả về nhóm vé đã xác nhận để caller điều hướng sang trang chi tiết. */
  const confirm = useCallback(async (): Promise<CombinedBooking | null> => {
    if (state.phase !== "held" || !state.booking) return null;

    const signal = nextSignal();
    const groupCode = state.booking.group_code;
    dispatch({ type: "CONFIRM_START" });
    try {
      const booking = await confirmCombinedBooking(groupCode, signal);
      dispatch({ type: "CONFIRM_SUCCESS", booking });
      return booking;
    } catch (caught) {
      if (isAbort(caught)) return null;
      dispatch({ type: "CONFIRM_FAILURE", message: messageOf(caught, "Không xác nhận được vé ghép.") });
      return null;
    }
  }, [nextSignal, state.booking, state.phase]);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    dispatch({ type: "RESET" });
  }, []);

  // Đồng hồ chỉ chạy khi thật sự đang giữ chỗ.
  const isHolding = state.phase === "held" || state.phase === "confirming";
  useEffect(() => {
    if (!isHolding || !state.booking?.expires_at) return;
    setNow(Date.now());
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [isHolding, state.booking?.expires_at]);

  const secondsLeft = useMemo(
    () => (isHolding ? remainingSeconds(state.booking?.expires_at ?? null, now) : 0),
    [isHolding, state.booking?.expires_at, now],
  );

  // Hết giờ giữ chỗ — chuyển sang trạng thái expired, không tự confirm.
  useEffect(() => {
    if (isHolding && state.booking?.expires_at && secondsLeft === 0) {
      dispatch({ type: "EXPIRE" });
    }
  }, [isHolding, secondsLeft, state.booking?.expires_at]);

  return {
    state,
    selectedOption: findSelectedOption(state),
    secondsLeft,
    search,
    selectOption,
    hold,
    confirm,
    reset,
  };
}
