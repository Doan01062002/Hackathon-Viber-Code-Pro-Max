/** Type riêng của feature forecast (Khối 1 - Dự báo). */

/** Khớp với ForecastItem (backend/views/analytics_view.py). */
export type ForecastItemDto = {
  od_product_id: number;
  origin_station_code: string;
  destination_station_code: string;
  seat_type: string;
  lead_days: number;
  demand_point: number;
  demand_p10: number | null;
  demand_p50: number | null;
  demand_p90: number | null;
};

/** Khớp với BookingCurvePoint (backend/views/analytics_view.py). */
export type BookingCurvePointDto = {
  lead_days: number;
  cumulative_bookings: number;
  forecast_demand_point: number;
};

/** Khớp với ForecastResponse (backend/views/analytics_view.py). */
export type ForecastResponseDto = {
  trip_id: number;
  service_date: string;
  forecasts: ForecastItemDto[];
  booking_curve: BookingCurvePointDto[];
};
