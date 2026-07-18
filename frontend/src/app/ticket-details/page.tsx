import { Suspense } from "react";
import { AppShell } from "@/features/rail-ui/components/AppShell";
import { TicketDetailsScreen } from "@/features/rail-ui/screens/TicketDetailsScreen";

export default function TicketDetailsPage() {
  return (
    <AppShell eyebrow="Cổng hành khách" title="Chi tiết vé tàu & Hành trình">
      <Suspense fallback={<div className="rounded-2xl border border-outline-variant bg-white p-12 text-center text-xs font-semibold text-on-surface-variant shadow-sm">Đang tải trang chi tiết vé...</div>}>
        <TicketDetailsScreen />
      </Suspense>
    </AppShell>
  );
}
