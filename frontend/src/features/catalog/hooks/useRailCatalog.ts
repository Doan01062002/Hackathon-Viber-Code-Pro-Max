"use client";

import { useEffect, useState } from "react";
import { getRailCatalog } from "@/features/catalog/api/catalogApi";
import type { RailCatalog } from "@/features/catalog/types";

let cachedCatalog: RailCatalog | null = null;
let catalogRequest: Promise<RailCatalog> | null = null;

export function useRailCatalog() {
  const [catalog, setCatalog] = useState<RailCatalog | null>(cachedCatalog);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const load = () => {
      catalogRequest ??= getRailCatalog();
      return catalogRequest
      .then((result) => {
        cachedCatalog = result;
        if (active) setCatalog(result);
      })
      .catch((caught: unknown) => {
        catalogRequest = null;
        if (active) setError(caught instanceof Error ? caught.message : "Khong tai duoc danh muc");
      });
    };

    void load();
    const interval = window.setInterval(() => {
      catalogRequest = null;
      void load();
    }, 300_000);
    const handleFocus = () => {
      catalogRequest = null;
      void load();
    };
    window.addEventListener("focus", handleFocus);

    return () => {
      active = false;
      window.clearInterval(interval);
      window.removeEventListener("focus", handleFocus);
    };
  }, []);

  return { catalog, error };
}
