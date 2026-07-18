import { apiClient } from "@/lib/api/client";

import type { ForecastResponseDto } from "../types";

/**
 * Endpoint dự báo của Khối 1. Component không biết đường dẫn API là gì.
 *
 * Backend: GET /api/v1/forecast?trip_id=&seat_type=
 * (backend/controllers/analytics_controller.py)
 */
export function getForecast(tripId: number, seatType?: string, signal?: AbortSignal) {
  const params = new URLSearchParams({ trip_id: String(tripId) });
  if (seatType) params.set("seat_type", seatType);
  return apiClient.get<ForecastResponseDto>(`/api/v1/forecast?${params.toString()}`, { signal });
}
