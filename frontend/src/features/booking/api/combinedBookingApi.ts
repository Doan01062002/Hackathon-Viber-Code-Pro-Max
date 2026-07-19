import { apiClient } from "@/lib/api/client";

import type {
  CombinedBooking,
  CombinedBookingCreateRequest,
  CombinedJourneyOptions,
} from "@/features/booking/types";

/** Tìm các phương án ghép chặng cho một hành trình. */
export function searchCombinedOptions(
  params: {
    origin: string;
    destination: string;
    serviceDate: string;
    seatType?: string;
    maxTransfers?: number;
  },
  signal?: AbortSignal,
): Promise<CombinedJourneyOptions> {
  const query = new URLSearchParams({
    origin: params.origin,
    destination: params.destination,
    service_date: params.serviceDate,
  });
  if (params.seatType) query.set("seat_type", params.seatType);
  if (params.maxTransfers != null) query.set("max_transfers", String(params.maxTransfers));

  return apiClient.get<CombinedJourneyOptions>(`/api/v1/booking/combined-options?${query}`, { signal });
}

/** Giữ chỗ cả nhóm chặng. Backend trả về expires_at — hạn giữ chỗ thật. */
export function createCombinedHold(
  request: CombinedBookingCreateRequest,
  signal?: AbortSignal,
): Promise<CombinedBooking> {
  return apiClient.post<CombinedBooking>("/api/v1/booking/combined", request, { signal });
}

/** Tra cứu nhóm vé ghép theo group_code. */
export function getCombinedBooking(
  groupCode: string,
  signal?: AbortSignal,
): Promise<CombinedBooking> {
  return apiClient.get<CombinedBooking>(
    `/api/v1/booking/combined/${encodeURIComponent(groupCode)}`,
    { signal },
  );
}

/** Xác nhận nhóm vé đang giữ chỗ. */
export function confirmCombinedBooking(
  groupCode: string,
  signal?: AbortSignal,
): Promise<CombinedBooking> {
  return apiClient.post<CombinedBooking>(
    `/api/v1/booking/combined/${encodeURIComponent(groupCode)}/confirm`,
    {},
    { signal },
  );
}
