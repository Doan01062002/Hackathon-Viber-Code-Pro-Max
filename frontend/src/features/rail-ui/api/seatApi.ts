import { apiClient } from "@/lib/api/client";

export interface CoachDto {
  name: string;
  type: string;
  occupancy: string;
  coach_no: string;
}

export interface SeatLegendItem {
  tone: string;
  label: string;
}

export interface SeatPlanDto {
  route: string;
  coach: string;
  seat_type: string;
  seats: string[][];
  seatLegend: SeatLegendItem[];
}

export interface GapSuggestionDto {
  route: string;
  seatType: string;
  benefit: string;
  priority: string;
  reason: string;
}

export interface TripOptionDto {
  trip_id: number;
  train_code: string;
  service_date: string;
}

export const seatApi = {
  getTrips: (): Promise<TripOptionDto[]> =>
    apiClient.get<TripOptionDto[]>("/api/v1/seats/trips"),

  getCoaches: (tripId: number): Promise<CoachDto[]> =>
    apiClient.get<CoachDto[]>(`/api/v1/seats/coaches?trip_id=${tripId}`),

  getSeatLayout: (tripId: number, coachNo: string): Promise<SeatPlanDto> =>
    apiClient.get<SeatPlanDto>(`/api/v1/seats/layout?trip_id=${tripId}&coach_no=${coachNo}`),

  getGapSuggestions: (tripId: number): Promise<GapSuggestionDto[]> =>
    apiClient.get<GapSuggestionDto[]>(`/api/v1/seats/gap-suggestions?trip_id=${tripId}`),
};
