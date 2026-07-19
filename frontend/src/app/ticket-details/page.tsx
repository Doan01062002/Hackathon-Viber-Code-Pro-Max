import { Suspense } from "react";
import { AppShell } from "@/features/rail-ui/components/AppShell";
import { TicketDetailsScreen } from "@/features/rail-ui/screens/TicketDetailsScreen";

export default function TicketDetailsPage() {
  return (
    <AppShell eyebrow="Cổng hành khách" title="Chi tiết vé tàu & Hành trình">
      <Suspense fallback={<div className="text-xs text-on-surface-variant font-medium">Đang tải chi tiết hành trình...</div>}>
        <TicketDetailsScreen />
      </Suspense>
    </AppShell>
  );
}
