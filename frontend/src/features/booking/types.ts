export type BookingCreateRequest = {
  od_product_id: number;
  seat_id?: number | null;
  quote_id?: number | null;
  channel?: string;
};

export type BookingResponse = {
  booking_id: number;
  booking_code: string;
  od_product_id: number;
  seat_id: number | null;
  status: string;
  booked_price: number;
  booked_at: string;
  expires_at: string | null;
};

export type BookingConfirmResponse = {
  booking_id: number;
  booking_code: string;
  status: string;
  seat_id: number;
  coach_no: string;
  seat_no: string;
};

export type BookingSearchItem = {
  od_product_id: number;
  trip_id: number;
  train_code: string;
  origin_code: string;
  origin_name: string;
  destination_code: string;
  destination_name: string;
  service_date: string;
  departure_at: string;
  arrival_at: string;
  seat_type: string;
  seat_type_name: string;
  base_price: number;
  availability: number;
};

export type BookingOptions = {
  destinations: Array<{ code: string; name: string }>;
  departure_dates: string[];
  return_dates: string[];
};

export type BookingSeat = {
  seat_id: number;
  seat_no: string;
  status: "available" | "held" | "confirmed" | "blocked";
};

export type BookingCoach = {
  coach_no: string;
  seat_type: string;
  total_seats: number;
  available_seats: number;
  seats: BookingSeat[];
};

export type BookingSegment = {
  segment_id: number;
  sequence_no: number;
  origin_code: string;
  origin_name: string;
  destination_code: string;
  destination_name: string;
  departure_at: string;
  arrival_at: string;
  distance_km: number;
  capacity: number;
  remaining: number;
  load_pct: number;
};

export type BookingSeatPlan = {
  od_product_id: number;
  trip_id: number;
  train_code: string;
  origin_code: string;
  origin_name: string;
  destination_code: string;
  destination_name: string;
  service_date: string;
  seat_type: string;
  coaches: BookingCoach[];
  segments: BookingSegment[];
};

export type BookingDetailSegment = {
  segment_id: number;
  sequence_no: number;
  origin_code: string;
  origin_name: string;
  destination_code: string;
  destination_name: string;
  departure_at: string;
  arrival_at: string;
  distance_km: number;
};

/**
 * Vé ghép chặng — các type dưới đây bám sát
 * backend/src/backend/views/combined_booking_view.py.
 */

export type CombinedJourneyLegOption = {
  sequence_no: number;
  gap_combination_id: number;
  od_product_id: number;
  origin_code: string;
  origin_name: string;
  destination_code: string;
  destination_name: string;
  departure_at: string;
  arrival_at: string;
  seat_id: number;
  coach_no: string;
  seat_no: string;
  seat_type: string;
  seat_type_name: string;
  estimated_price: number;
  /** true = giữ nguyên chỗ của chặng trước; false = phải đổi chỗ tại ga chuyển. */
  keep_previous_seat: boolean;
};

export type CombinedJourneyOption = {
  option_key: string;
  trip_id: number;
  train_code: string;
  service_date: string;
  origin_code: string;
  origin_name: string;
  destination_code: string;
  destination_name: string;
  transfer_count: number;
  seat_change_count: number;
  estimated_total_price: number;
  legs: CombinedJourneyLegOption[];
};

export type CombinedJourneyOptions = {
  origin_code: string;
  destination_code: string;
  service_date: string;
  options: CombinedJourneyOption[];
};

export type CombinedBookingCreateRequest = {
  gap_combination_ids: number[];
  channel?: string;
};

export type CombinedBookingLeg = {
  sequence_no: number;
  gap_combination_id: number;
  booking_id: number;
  booking_code: string;
  od_product_id: number;
  status: string;
  origin_code: string;
  origin_name: string;
  destination_code: string;
  destination_name: string;
  departure_at: string;
  arrival_at: string;
  seat_id: number;
  coach_no: string;
  seat_no: string;
  seat_type: string;
  seat_type_name: string;
  booked_price: number;
  keep_previous_seat: boolean;
};

export type CombinedBooking = {
  booking_group_id: number;
  group_code: string;
  status: "held" | "confirmed" | "cancelled" | "refunded";
  channel: string | null;
  trip_id: number;
  train_code: string;
  service_date: string;
  origin_code: string;
  origin_name: string;
  destination_code: string;
  destination_name: string;
  transfer_count: number;
  total_price: number;
  booked_at: string;
  expires_at: string | null;
  legs: CombinedBookingLeg[];
};

export type BookingDetail = {
  booking_id: number;
  booking_code: string;
  od_product_id: number;
  status: "held" | "confirmed" | "cancelled" | "refunded";
  channel: string | null;
  booked_price: number;
  booked_at: string;
  expires_at: string | null;
  trip_id: number;
  train_code: string;
  train_name: string | null;
  trip_status: "scheduled" | "boarding" | "departed" | "completed" | "cancelled";
  service_date: string;
  departure_at: string;
  arrival_at: string;
  origin_code: string;
  origin_name: string;
  destination_code: string;
  destination_name: string;
  seat_type: string;
  seat_type_name: string;
  fare_class: string;
  distance_km: number;
  coach_no: string | null;
  seat_no: string | null;
  segments: BookingDetailSegment[];
};
