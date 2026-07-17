export type PricingQuoteRequest = {
  origin: string;
  destination: string;
  service_date: string;
  seat_type: string;
  trip_id?: number;
};

export type PricingExplanation = {
  base_opportunity_cost: number;
  markup_factor: number;
  applied_policies: string[];
  bottleneck_segment_id: number | null;
  bottleneck_segment: string | null;
  segment_bid_prices: Record<string, number>;
};

export type PricingQuoteResponse = {
  quote_id: number;
  od_product_id: number;
  policy_id: number | null;
  opportunity_cost: number;
  proposed_price: number;
  final_price: number;
  decision: "accepted" | "rejected" | "blocked";
  explanation: PricingExplanation;
  expires_at: string;
  origin: string | null;
  destination: string | null;
  service_date: string | null;
  seat_type: string | null;
  availability: number | null;
};
