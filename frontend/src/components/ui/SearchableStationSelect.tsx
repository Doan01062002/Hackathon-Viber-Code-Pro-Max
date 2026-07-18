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
  align?: "left" | "right";
  className?: string;
};

export function SearchableStationSelect({
  label,
  options,
  value,
  onChange,
  placeholder = "Tìm theo mã ga, tên ga hoặc khu vực",
  align = "left",
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
    <div className={cn("space-y-1 w-full", className)} ref={rootRef}>
      <label className="text-[10px] uppercase font-black tracking-wider text-slate-400">
        {label}
      </label>

      <div className="relative w-full">
        {/* Select Button - Fixed Height 64px to ensure perfect alignment */}
        <button
          type="button"
          onClick={() => setOpen((current) => !current)}
          className={cn(
            "w-full bg-surface-container-low border border-outline-variant rounded-lg px-3 py-2 text-xs text-left",
            "focus:ring-1 focus:ring-primary outline-none transition-all h-[64px]",
            "flex items-center justify-between gap-2.5 shadow-sm hover:bg-slate-50/50 cursor-pointer",
            open ? "ring-1 ring-primary border-primary" : ""
          )}
        >
          <span className="min-w-0 flex-grow flex flex-col justify-center">
            {selected ? (
              <span className="block leading-tight">
                <span className="block font-black text-on-surface text-xs truncate">
                  {selected.name}
                </span>
                <span className="flex items-center gap-1.5 mt-0.5">
                  <span className="px-1 py-0.2 bg-primary/10 text-primary text-[8px] font-black rounded uppercase tracking-wider font-mono">
                    {selected.code}
                  </span>
                  {selected.region ? (
                    <span className="text-[10px] text-on-surface-variant font-medium truncate">
                      {selected.region}
                    </span>
                  ) : null}
                </span>
              </span>
            ) : (
              <span className="text-outline text-xs truncate font-medium">{placeholder}</span>
            )}
          </span>
          <span className="material-symbols-outlined text-sm text-on-surface-variant shrink-0">
            unfold_more
          </span>
        </button>

        {/* Dropdown Overlay - Custom Width to prevent name truncation and aligned based on prop */}
        {open ? (
          <div
            className={cn(
              "absolute top-[calc(100%+8px)] z-30 rounded-xl border border-outline-variant bg-white shadow-xl p-3 space-y-3 w-[280px] sm:w-[320px]",
              align === "right" ? "right-0" : "left-0"
            )}
          >
            <div className="relative">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-sm text-on-surface-variant">
                search
              </span>
              <input
                ref={inputRef}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Nhập tên ga hoặc mã ga..."
                className="w-full rounded-lg border border-outline-variant bg-surface-container-low py-2 pl-10 pr-3 text-xs font-semibold text-on-surface outline-none focus:ring-1 focus:ring-primary"
              />
            </div>

            {/* List options with list style instead of card style - No text truncation */}
            <div className="max-h-60 overflow-y-auto custom-scrollbar divide-y divide-slate-100 pr-1">
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
                        "w-full px-3 py-2.5 text-left transition-all duration-150 flex items-center justify-between cursor-pointer first:rounded-t-lg last:rounded-b-lg",
                        isSelected
                          ? "bg-primary/10 text-primary font-bold"
                          : "hover:bg-slate-50 text-on-surface"
                      )}
                    >
                      <div className="min-w-0 flex-grow pr-2">
                        <span className={cn(
                          "block text-xs",
                          isSelected ? "font-black text-primary" : "font-bold text-on-surface"
                        )}>
                          {option.name}
                        </span>
                        {option.region ? (
                          <span className="block text-[10px] text-on-surface-variant/80 font-medium mt-0.5">
                            {option.region}
                          </span>
                        ) : null}
                      </div>
                      
                      <div className="flex items-center gap-2 shrink-0 ml-2">
                        <span className={cn(
                          "px-1.5 py-0.5 rounded text-[9px] font-black uppercase font-mono tracking-wider",
                          isSelected ? "bg-primary text-white" : "bg-slate-100 text-slate-500"
                        )}>
                          {option.code}
                        </span>
                        {isSelected && (
                          <span className="material-symbols-outlined text-primary text-sm font-bold">
                            check
                          </span>
                        )}
                      </div>
                    </button>
                  );
                })
              ) : (
                <div className="rounded-lg border border-dashed border-outline-variant px-3 py-4 text-center text-xs font-semibold text-on-surface-variant">
                  Không tìm thấy ga phù hợp.
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
