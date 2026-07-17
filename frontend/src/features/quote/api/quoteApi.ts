import { apiClient } from "@/lib/api/client";

import type { PricingQuoteRequest, PricingQuoteResponse } from "@/features/quote/types";

export function createPricingQuote(
  request: PricingQuoteRequest,
  signal?: AbortSignal,
): Promise<PricingQuoteResponse> {
  return apiClient.post<PricingQuoteResponse>("/api/v1/quote", request, { signal });
}
