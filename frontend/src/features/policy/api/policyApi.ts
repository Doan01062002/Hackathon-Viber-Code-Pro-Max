import { apiClient } from "@/lib/api/client";

export interface PolicyDto {
  id: number;
  od_product_id: number | null;
  name: string;
  min_price: number;
  max_price: number;
  max_step_change: number;
  valid_from: string | null;
  valid_to: string | null;
  status: string;
  created_by: string | null;
  approved_by: string | null;
}

export interface PolicyUpdateDto {
  name?: string;
  min_price?: number;
  max_price?: number;
  max_step_change?: number;
  status?: string;
}

export const policyApi = {
  getPolicies: async (od_product_id?: number, status?: string): Promise<PolicyDto[]> => {
    const params = new URLSearchParams();
    if (od_product_id !== undefined) params.append("od_product_id", od_product_id.toString());
    if (status) params.append("status", status);

    const queryStr = params.toString() ? `?${params.toString()}` : "";
    return apiClient.get<PolicyDto[]>(`/api/v1/policy/limits${queryStr}`, {
      headers: { "X-User-Role": "revenue_manager" },
    });
  },

  updatePolicy: async (policy_id: number, body: PolicyUpdateDto): Promise<PolicyDto> => {
    return apiClient.put<PolicyDto>(`/api/v1/policy/limits/${policy_id}`, body, {
      headers: { "X-User-Role": "revenue_manager" },
    });
  },
};
