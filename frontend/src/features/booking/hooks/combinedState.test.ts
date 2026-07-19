import { describe, expect, it } from "vitest";

import {
  combinedReducer,
  findSelectedOption,
  formatCountdown,
  initialCombinedState,
  isSeatChange,
  remainingSeconds,
  type CombinedState,
} from "./combinedState";
import type { CombinedBooking, CombinedJourneyOption } from "@/features/booking/types";

function option(optionKey: string, transfers = 1): CombinedJourneyOption {
  return {
    option_key: optionKey,
    trip_id: 1,
    train_code: "SE1",
    service_date: "2026-08-01",
    origin_code: "HN",
    origin_name: "Hà Nội",
    destination_code: "SG",
    destination_name: "Sài Gòn",
    transfer_count: transfers,
    seat_change_count: transfers,
    estimated_total_price: 1_200_000,
    legs: [],
  };
}

function booking(expiresAt: string | null): CombinedBooking {
  return {
    booking_group_id: 7,
    group_code: "GRP123",
    status: "held",
    channel: "web",
    trip_id: 1,
    train_code: "SE1",
    service_date: "2026-08-01",
    origin_code: "HN",
    origin_name: "Hà Nội",
    destination_code: "SG",
    destination_name: "Sài Gòn",
    transfer_count: 2,
    total_price: 1_200_000,
    booked_at: "2026-08-01T10:00:00Z",
    expires_at: expiresAt,
    legs: [],
  };
}

function stateAt(phase: CombinedState["phase"], patch: Partial<CombinedState> = {}): CombinedState {
  return { ...initialCombinedState, phase, ...patch };
}

describe("combinedReducer — tìm phương án", () => {
  it("SEARCH_START xoá kết quả cũ", () => {
    const dirty = stateAt("options", { options: [option("a")], selectedKey: "a", error: "cũ" });
    expect(combinedReducer(dirty, { type: "SEARCH_START" })).toEqual({
      ...initialCombinedState,
      phase: "searching",
    });
  });

  it("một phương án duy nhất thì được chọn sẵn", () => {
    const next = combinedReducer(stateAt("searching"), {
      type: "SEARCH_SUCCESS",
      options: [option("only")],
    });
    expect(next.phase).toBe("options");
    expect(next.selectedKey).toBe("only");
  });

  it("nhiều phương án thì bắt user tự chọn", () => {
    const next = combinedReducer(stateAt("searching"), {
      type: "SEARCH_SUCCESS",
      options: [option("a"), option("b")],
    });
    expect(next.selectedKey).toBeNull();
  });

  it("không có phương án nào — vẫn vào phase options để hiện empty state", () => {
    const next = combinedReducer(stateAt("searching"), { type: "SEARCH_SUCCESS", options: [] });
    expect(next.phase).toBe("options");
    expect(next.options).toEqual([]);
  });

  it("SEARCH_FAILURE giữ lại thông báo lỗi", () => {
    const next = combinedReducer(stateAt("searching"), {
      type: "SEARCH_FAILURE",
      message: "Mất kết nối",
    });
    expect(next.phase).toBe("idle");
    expect(next.error).toBe("Mất kết nối");
  });
});

describe("combinedReducer — giữ chỗ", () => {
  it("không giữ chỗ được khi chưa chọn phương án", () => {
    const noSelection = stateAt("options", { options: [option("a")] });
    expect(combinedReducer(noSelection, { type: "HOLD_START" })).toBe(noSelection);
  });

  it("giữ chỗ hỏng thì quay lại danh sách kèm lỗi, không mất options", () => {
    const holding = stateAt("holding", { options: [option("a")], selectedKey: "a" });
    const next = combinedReducer(holding, {
      type: "HOLD_FAILURE",
      message: "Ghế vừa bị người khác đặt",
    });
    expect(next.phase).toBe("options");
    expect(next.options).toHaveLength(1);
    expect(next.error).toBe("Ghế vừa bị người khác đặt");
  });

  it("đã giữ chỗ rồi thì không đổi phương án ngầm được", () => {
    const held = stateAt("held", { options: [option("a"), option("b")], selectedKey: "a" });
    expect(combinedReducer(held, { type: "SELECT_OPTION", optionKey: "b" })).toBe(held);
  });
});

describe("combinedReducer — xác nhận và hết hạn", () => {
  it("xác nhận hỏng thì quay về held để thử lại", () => {
    const confirming = stateAt("confirming", { booking: booking(null) });
    const next = combinedReducer(confirming, { type: "CONFIRM_FAILURE", message: "Hết hạn giữ chỗ" });
    expect(next.phase).toBe("held");
    expect(next.error).toBe("Hết hạn giữ chỗ");
  });

  it("vé đã xác nhận thì không bị đánh dấu hết hạn", () => {
    const confirmed = stateAt("confirmed", { booking: booking(null) });
    expect(combinedReducer(confirmed, { type: "EXPIRE" })).toBe(confirmed);
  });

  it("vé đang giữ thì hết hạn được", () => {
    const held = stateAt("held", { booking: booking("2026-08-01T10:15:00Z") });
    expect(combinedReducer(held, { type: "EXPIRE" }).phase).toBe("expired");
  });
});

describe("findSelectedOption", () => {
  it("trả null khi chưa chọn", () => {
    expect(findSelectedOption(stateAt("options", { options: [option("a")] }))).toBeNull();
  });

  it("tìm đúng phương án theo option_key", () => {
    const state = stateAt("options", { options: [option("a"), option("b")], selectedKey: "b" });
    expect(findSelectedOption(state)?.option_key).toBe("b");
  });
});

describe("isSeatChange", () => {
  it("chặng đầu không tính là đổi chỗ dù keep_previous_seat = false", () => {
    // Dữ liệu thật từ RDS: chặng 1 luôn có keep_previous_seat = false.
    expect(isSeatChange({ sequence_no: 1, keep_previous_seat: false })).toBe(false);
  });

  it("chặng sau mà không giữ chỗ cũ thì là đổi chỗ", () => {
    expect(isSeatChange({ sequence_no: 2, keep_previous_seat: false })).toBe(true);
  });

  it("chặng sau mà giữ được chỗ cũ thì không phải đổi", () => {
    expect(isSeatChange({ sequence_no: 3, keep_previous_seat: true })).toBe(false);
  });
});

describe("remainingSeconds", () => {
  const now = Date.parse("2026-08-01T10:00:00Z");

  it("tính đúng số giây còn lại", () => {
    expect(remainingSeconds("2026-08-01T10:15:00Z", now)).toBe(900);
  });

  it("quá hạn thì trả 0 chứ không âm", () => {
    expect(remainingSeconds("2026-08-01T09:59:00Z", now)).toBe(0);
  });

  it("không có expires_at thì coi như hết giờ", () => {
    expect(remainingSeconds(null, now)).toBe(0);
  });

  it("expires_at rác thì trả 0 thay vì NaN", () => {
    expect(remainingSeconds("khong-phai-ngay", now)).toBe(0);
  });
});

describe("formatCountdown", () => {
  it("định dạng mm:ss", () => {
    expect(formatCountdown(900)).toBe("15:00");
    expect(formatCountdown(65)).toBe("01:05");
    expect(formatCountdown(0)).toBe("00:00");
  });

  it("số âm vẫn ra 00:00", () => {
    expect(formatCountdown(-10)).toBe("00:00");
  });
});
