"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { cn } from "@/lib/utils";

export type StationOption = {
  code: string;
  name: string;
  region?: string;
};

type SearchableStationSelectProps = {
  label: string;
  options: StationOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
};

export function SearchableStationSelect({
  label,
  options,
  value,
  onChange,
  placeholder = "Tim theo ma ga, ten ga hoac khu vuc",
  className,
}: SearchableStationSelectProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const rootRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const selected = useMemo(
    () => options.find((option) => option.code === value) ?? null,
    [options, value],
  );

  const filteredOptions = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return options;

    return options.filter((option) =>
      `${option.code} ${option.name} ${option.region}`.toLowerCase().includes(normalized),
    );
  }, [options, query]);

  useEffect(() => {
    if (!open) return;

    function handlePointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, [open]);

  useEffect(() => {
    if (open) {
      inputRef.current?.focus();
    } else {
      setQuery("");
    }
  }, [open]);

  return (
    <div className={cn("space-y-1", className)} ref={rootRef}>
      <label className="text-[10px] uppercase font-bold tracking-wider text-on-surface-variant">
        {label}
      </label>

      <div className="relative">
        <button
          type="button"
          onClick={() => setOpen((current) => !current)}
          className={cn(
            "w-full bg-surface-container-low border border-outline-variant rounded-lg px-3 py-2 text-xs text-left",
            "focus:ring-1 focus:ring-primary outline-none transition-all min-h-11",
            "flex items-center justify-between gap-3",
          )}
        >
          <span className="min-w-0">
            {selected ? (
              <span className="block">
                <span className="block font-semibold text-on-surface">
                  {selected.name} ({selected.code})
                </span>
                {selected.region ? (
                  <span className="block text-[10px] text-on-surface-variant truncate">
                    {selected.region}
                  </span>
                ) : null}
              </span>
            ) : (
              <span className="text-outline">{placeholder}</span>
            )}
          </span>
          <span className="material-symbols-outlined text-sm text-on-surface-variant shrink-0">
            unfold_more
          </span>
        </button>

        {open ? (
          <div className="absolute left-0 right-0 top-[calc(100%+8px)] z-30 rounded-xl border border-outline-variant bg-white shadow-xl p-3 space-y-3">
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-sm text-on-surface-variant">
                search
              </span>
              <input
                ref={inputRef}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={placeholder}
                className="w-full rounded-lg border border-outline-variant bg-surface-container-low py-2 pl-10 pr-3 text-xs font-medium text-on-surface outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            <div className="max-h-64 overflow-y-auto custom-scrollbar space-y-2 pr-1">
              {filteredOptions.length > 0 ? (
                filteredOptions.map((option) => {
                  const isSelected = option.code === value;

                  return (
                    <button
                      key={option.code}
                      type="button"
                      onClick={() => {
                        onChange(option.code);
                        setOpen(false);
                      }}
                      className={cn(
                        "w-full rounded-lg border px-3 py-2 text-left transition-colors",
                        isSelected
                          ? "border-primary bg-primary/5"
                          : "border-outline-variant bg-surface-container-low hover:border-primary/40 hover:bg-primary/5",
                      )}
                    >
                      <span className="block text-xs font-semibold text-on-surface">
                        {option.name} ({option.code})
                      </span>
                      {option.region ? (
                        <span className="block text-[10px] text-on-surface-variant">
                          {option.region}
                        </span>
                      ) : null}
                    </button>
                  );
                })
              ) : (
                <div className="rounded-lg border border-dashed border-outline-variant px-3 py-4 text-center text-xs font-medium text-on-surface-variant">
                  Khong tim thay ga phu hop.
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
