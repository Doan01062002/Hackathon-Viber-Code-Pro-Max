import { apiClient } from "@/lib/api/client";

import type { LegHeatmapResponseDto } from "../types";

/**
 * Endpoint tải/tỉ lệ lấp đầy theo chặng của Khối 1.
 * Component không biết đường dẫn API là gì.
 *
 * Backend: GET /api/v1/segments/load?trip_id=
 * (alias của /analytics/legs-heatmap — backend/controllers/analytics_controller.py)
 */
export function getSegmentsLoad(tripId: number, signal?: AbortSignal) {
  const params = new URLSearchParams({ trip_id: String(tripId) });
  return apiClient.get<LegHeatmapResponseDto>(`/api/v1/segments/load?${params.toString()}`, {
    signal,
  });
}
