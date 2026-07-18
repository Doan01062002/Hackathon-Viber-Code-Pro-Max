import { useState, useEffect, useCallback } from "react";
import { apiClient } from "./client";

export function useQuery<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiClient.get<T>(url);
      setData(res);
    } catch (err: any) {
      setError(err.message || "Không thể kết nối tới server");
    } finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}
