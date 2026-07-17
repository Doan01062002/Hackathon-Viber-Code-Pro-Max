"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/lib/api/client";
import type { AsyncStatus } from "@/types";

import { getForecast } from "../api/forecastApi";
import type { ForecastResponseDto } from "../types";

/**
 * Toàn bộ logic lấy dữ liệu dự báo (Khối 1) cho một chuyến tàu.
 * Component chỉ render những gì hook trả về — muốn đổi cách fetch, thêm cache
 * hay polling thì sửa ở đây, UI không đổi.
 */
export function useForecast(tripId: number, seatType?: string) {
  const [data, setData] = useState<ForecastResponseDto | null>(null);
  const [status, setStatus] = useState<AsyncStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  const fetchForecast = useCallback(
    async (signal?: AbortSignal) => {
      setStatus("loading");
      setError(null);
      try {
        const result = await getForecast(tripId, seatType, signal);
        if (signal?.aborted) return;
        setData(result);
        setStatus("success");
      } catch (e) {
        if (e instanceof DOMException && e.name === "AbortError") return;
        setError(e instanceof ApiError ? e.message : "Đã có lỗi xảy ra");
        setStatus("error");
      }
    },
    [tripId, seatType],
  );

  useEffect(() => {
    const controller = new AbortController();
    fetchForecast(controller.signal);
    return () => controller.abort();
  }, [fetchForecast]);

  const refetch = useCallback(() => fetchForecast(), [fetchForecast]);

  return { data, status, error, refetch, isLoading: status === "loading" };
}
