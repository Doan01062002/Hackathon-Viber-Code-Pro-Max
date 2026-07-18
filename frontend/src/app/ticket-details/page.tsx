import { AppShell } from "@/features/rail-ui/components/AppShell";
import { TicketDetailsScreen } from "@/features/rail-ui/screens/TicketDetailsScreen";

export default function TicketDetailsPage() {
  return (
    <AppShell eyebrow="Cổng hành khách" title="Chi tiết vé tàu & Hành trình">
      <TicketDetailsScreen />
    </AppShell>
  );
}
