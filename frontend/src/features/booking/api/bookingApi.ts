import { apiClient } from "@/lib/api/client";

import type { BookingConfirmResponse, BookingCreateRequest, BookingResponse } from "@/features/booking/types";

/** Tạo giữ chỗ (hold) cho một sản phẩm OD. */
export function createBookingHold(
  request: BookingCreateRequest,
  signal?: AbortSignal,
): Promise<BookingResponse> {
  return apiClient.post<BookingResponse>("/api/v1/booking", request, { signal });
}

/** Xác nhận giữ chỗ -> backend tự gán ghế vật lý và trả về toa/ghế. */
export function confirmBooking(
  bookingId: number,
  signal?: AbortSignal,
): Promise<BookingConfirmResponse> {
  return apiClient.post<BookingConfirmResponse>(`/api/v1/booking/${bookingId}/confirm`, {}, { signal });
}
