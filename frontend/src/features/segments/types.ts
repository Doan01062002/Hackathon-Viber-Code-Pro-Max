/** Type riêng của feature segments (Khối 1 - Dự báo: tải/tỉ lệ lấp đầy theo chặng). */

/** Khớp với LegHeatmapItem (backend/views/analytics_view.py). */
export type LegHeatmapItemDto = {
  segment_id: number;
  sequence_no: number;
  origin_station_code: string;
  destination_station_code: string;
  capacity: number;
  remaining: number;
  seat_type: string;
  bid_price: number;
  is_bottleneck: boolean;
};

/** Khớp với LegHeatmapResponse (backend/views/analytics_view.py). */
export type LegHeatmapResponseDto = {
  trip_id: number;
  legs: LegHeatmapItemDto[];
};
