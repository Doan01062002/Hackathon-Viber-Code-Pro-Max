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
