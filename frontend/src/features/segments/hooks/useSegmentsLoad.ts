"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/lib/api/client";
import type { AsyncStatus } from "@/types";

import { getSegmentsLoad } from "../api/segmentsApi";
import type { LegHeatmapResponseDto } from "../types";

/**
 * Toàn bộ logic lấy dữ liệu tải chặng (Khối 1) cho một chuyến tàu.
 * Cùng khuôn với useForecast — component chỉ render những gì hook trả về.
 */
export function useSegmentsLoad(tripId: number) {
  const [data, setData] = useState<LegHeatmapResponseDto | null>(null);
  const [status, setStatus] = useState<AsyncStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  const fetchSegments = useCallback(
    async (signal?: AbortSignal) => {
      setStatus("loading");
      setError(null);
      try {
        const result = await getSegmentsLoad(tripId, signal);
        if (signal?.aborted) return;
        setData(result);
        setStatus("success");
      } catch (e) {
        if (e instanceof DOMException && e.name === "AbortError") return;
        setError(e instanceof ApiError ? e.message : "Đã có lỗi xảy ra");
        setStatus("error");
      }
    },
    [tripId],
  );

  useEffect(() => {
    const controller = new AbortController();
    fetchSegments(controller.signal);
    return () => controller.abort();
  }, [fetchSegments]);

  const refetch = useCallback(() => fetchSegments(), [fetchSegments]);

  return { data, status, error, refetch, isLoading: status === "loading" };
}
