/**
 * Máy trạng thái cho luồng đặt vé ghép chặng.
 *
 * Tách riêng khỏi React để test được bằng vitest mà không cần dựng DOM.
 * Reducer thuần: cùng (state, action) luôn ra cùng kết quả.
 */

import type { CombinedBooking, CombinedJourneyOption } from "@/features/booking/types";

export type CombinedPhase =
  | "idle"
  | "searching"
  | "options"
  | "holding"
  | "held"
  | "confirming"
  | "confirmed"
  | "expired";

export type CombinedState = {
  phase: CombinedPhase;
  options: CombinedJourneyOption[];
  /** option_key của phương án user đang chọn. */
  selectedKey: string | null;
  /** Nhóm vé sau khi giữ chỗ thành công. */
  booking: CombinedBooking | null;
  error: string | null;
};

export type CombinedAction =
  | { type: "SEARCH_START" }
  | { type: "SEARCH_SUCCESS"; options: CombinedJourneyOption[] }
  | { type: "SEARCH_FAILURE"; message: string }
  | { type: "SELECT_OPTION"; optionKey: string }
  | { type: "HOLD_START" }
  | { type: "HOLD_SUCCESS"; booking: CombinedBooking }
  | { type: "HOLD_FAILURE"; message: string }
  | { type: "CONFIRM_START" }
  | { type: "CONFIRM_SUCCESS"; booking: CombinedBooking }
  | { type: "CONFIRM_FAILURE"; message: string }
  | { type: "EXPIRE" }
  | { type: "RESET" };

export const initialCombinedState: CombinedState = {
  phase: "idle",
  options: [],
  selectedKey: null,
  booking: null,
  error: null,
};

export function combinedReducer(state: CombinedState, action: CombinedAction): CombinedState {
  switch (action.type) {
    case "SEARCH_START":
      // Tìm lại thì bỏ hết kết quả cũ — tránh hiện phương án đã hết hạn.
      return { ...initialCombinedState, phase: "searching" };

    case "SEARCH_SUCCESS":
      return {
        ...state,
        phase: "options",
        options: action.options,
        // Chỉ 1 phương án thì chọn sẵn, khỏi bắt user bấm thừa một lần.
        selectedKey: action.options.length === 1 ? action.options[0].option_key : null,
        error: null,
      };

    case "SEARCH_FAILURE":
      return { ...initialCombinedState, phase: "idle", error: action.message };

    case "SELECT_OPTION":
      // Đã giữ chỗ rồi thì không cho đổi phương án ngầm.
      if (state.phase !== "options") return state;
      return { ...state, selectedKey: action.optionKey, error: null };

    case "HOLD_START":
      if (state.phase !== "options" || !state.selectedKey) return state;
      return { ...state, phase: "holding", error: null };

    case "HOLD_SUCCESS":
      return { ...state, phase: "held", booking: action.booking, error: null };

    case "HOLD_FAILURE":
      // Giữ chỗ hỏng (ghế vừa bị người khác đặt) — quay lại danh sách để chọn lại.
      return { ...state, phase: "options", error: action.message };

    case "CONFIRM_START":
      if (state.phase !== "held") return state;
      return { ...state, phase: "confirming", error: null };

    case "CONFIRM_SUCCESS":
      return { ...state, phase: "confirmed", booking: action.booking, error: null };

    case "CONFIRM_FAILURE":
      return { ...state, phase: "held", error: action.message };

    case "EXPIRE":
      // Chỉ vé đang giữ mới hết hạn được; vé đã xác nhận thì không.
      if (state.phase !== "held" && state.phase !== "confirming") return state;
      return { ...state, phase: "expired", error: null };

    case "RESET":
      return initialCombinedState;

    default:
      return state;
  }
}

export function findSelectedOption(state: CombinedState): CombinedJourneyOption | null {
  if (!state.selectedKey) return null;
  return state.options.find((option) => option.option_key === state.selectedKey) ?? null;
}

/**
 * Số giây còn lại của hạn giữ chỗ.
 *
 * Mốc luôn lấy từ expires_at của server (backend tính bằng MIN(booking.expires_at)),
 * không tự đếm 15:00 ở client — nếu không hai bên sẽ lệch nhau.
 */
export function remainingSeconds(expiresAt: string | null, now: number): number {
  if (!expiresAt) return 0;
  const deadline = new Date(expiresAt).getTime();
  if (Number.isNaN(deadline)) return 0;
  return Math.max(0, Math.ceil((deadline - now) / 1000));
}

/**
 * Chặng này có phải đổi chỗ tại ga chuyển không?
 *
 * Backend đặt keep_previous_seat = false cho chặng ĐẦU vì không có chặng trước
 * để giữ chỗ — đó không phải một lần đổi chỗ. Chỉ từ chặng thứ 2 trở đi mới tính.
 */
export function isSeatChange(leg: { sequence_no: number; keep_previous_seat: boolean }): boolean {
  return leg.sequence_no > 1 && !leg.keep_previous_seat;
}

/** Định dạng mm:ss cho đồng hồ đếm ngược. */
export function formatCountdown(totalSeconds: number): string {
  const safe = Math.max(0, Math.floor(totalSeconds));
  const minutes = Math.floor(safe / 60);
  const seconds = safe % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}
