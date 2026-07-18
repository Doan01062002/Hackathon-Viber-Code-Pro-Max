import { apiClient } from "@/lib/api/client";
import type { RailCatalog } from "@/features/catalog/types";

export function getRailCatalog(signal?: AbortSignal): Promise<RailCatalog> {
  return apiClient.get<RailCatalog>("/api/v1/catalog", { signal });
}
