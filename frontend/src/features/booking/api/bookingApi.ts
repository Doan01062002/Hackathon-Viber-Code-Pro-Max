import { apiClient } from "@/lib/api/client";

import type {
  BookingConfirmResponse,
  BookingCreateRequest,
  BookingOptions,
  BookingResponse,
  BookingSearchItem,
  BookingSeatPlan,
} from "@/features/booking/types";

export function getBookingOptions(
  origin: string,
  destination?: string,
  signal?: AbortSignal,
): Promise<BookingOptions> {
  const params = new URLSearchParams({ origin });
  if (destination) params.set("destination", destination);
  return apiClient.get<BookingOptions>(`/api/v1/booking/options?${params}`, { signal });
}

export function searchBookingProducts(
  origin: string,
  destination: string,
  serviceDate: string,
  signal?: AbortSignal,
): Promise<BookingSearchItem[]> {
  const params = new URLSearchParams({
    origin,
    destination,
    service_date: serviceDate,
  });
  return apiClient.get<BookingSearchItem[]>(`/api/v1/booking/search?${params}`, { signal });
}

export function getBookingSeatPlan(
  odProductId: number,
  signal?: AbortSignal,
): Promise<BookingSeatPlan> {
  return apiClient.get<BookingSeatPlan>(`/api/v1/booking/products/${odProductId}/seats`, { signal });
}

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
