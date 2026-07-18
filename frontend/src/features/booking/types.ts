export type BookingCreateRequest = {
  od_product_id: number;
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
