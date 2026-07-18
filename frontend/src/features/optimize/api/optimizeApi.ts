import { apiClient } from "@/lib/api/client";

export interface OptimizeVersionDto {
  run_version: string;
  calculated_at: string | null;
  is_active: boolean;
}

export interface OptimizeRollbackDto {
  status: string;
  trip_id: number;
  rolled_back_to: string;
  message: string;
}

export const optimizeApi = {
  async getVersions(tripId: number): Promise<OptimizeVersionDto[]> {
    return apiClient.get<OptimizeVersionDto[]>(`/api/v1/optimize/resolve/versions?trip_id=${tripId}`);
  },

  async rollbackVersion(tripId: number, targetVersion: string): Promise<OptimizeRollbackDto> {
    return apiClient.post<OptimizeRollbackDto>("/api/v1/optimize/resolve/rollback", {
      trip_id: tripId,
      target_version: targetVersion,
    });
  },

  async resolveOptimization(tripId: number): Promise<{ job_id: string; status: string; message: string }> {
    return apiClient.post("/api/v1/optimize/resolve", {
      trip_id: tripId,
    });
  },
};
