"use client";

/** Các mảnh dùng chung giữa thẻ vé thường và thẻ vé ghép chặng. */

export function SectionTitle({ icon, children }: { icon: string; children: string }) {
  return (
    <h4 className="flex items-center gap-1.5 text-xs font-black uppercase tracking-wider text-on-surface">
      <span className="material-symbols-outlined text-sm text-primary">{icon}</span>
      {children}
    </h4>
  );
}

export function InfoBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-outline-variant/60 bg-slate-50 px-4 py-3">
      <span className="text-[9px] font-bold uppercase tracking-wider text-on-surface-variant">{label}</span>
      <p className="mt-1 text-xs font-black text-on-surface">{value}</p>
    </div>
  );
}

export function InfoLine({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div>
      <span className="block text-[9px] font-bold text-on-surface-variant">{label}</span>
      <span className={`mt-0.5 block text-xs font-black ${highlight ? "text-primary" : "text-on-surface"}`}>
        {value}
      </span>
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
  tone = "neutral",
  spinning,
}: {
  icon: string;
  title: string;
  description: string;
  tone?: "neutral" | "error";
  spinning?: boolean;
}) {
  return (
    <div className="rounded-2xl border border-outline-variant bg-white p-12 text-center shadow-sm">
      <span
        className={`material-symbols-outlined text-5xl ${spinning ? "animate-spin" : ""} ${
          tone === "error" ? "text-red-500" : "text-slate-300"
        }`}
      >
        {icon}
      </span>
      <p className="mt-3 text-sm font-black text-on-surface">{title}</p>
      <p className="mt-1 text-xs font-medium text-on-surface-variant">{description}</p>
    </div>
  );
}

export const ticketStatusStyles = {
  held: { label: "Đang giữ chỗ", className: "border-amber-200 bg-amber-50 text-amber-700" },
  confirmed: { label: "Đã xác nhận", className: "border-emerald-200 bg-emerald-50 text-emerald-700" },
  cancelled: { label: "Đã hủy", className: "border-red-200 bg-red-50 text-red-700" },
  refunded: { label: "Đã hoàn tiền", className: "border-sky-200 bg-sky-50 text-sky-700" },
} as const;
