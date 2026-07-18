import { AppShell } from "@/features/rail-ui/components/AppShell";
import { DashboardScreen } from "@/features/rail-ui/screens/DashboardScreen";

export default function DashboardPage() {
  return (
    <AppShell eyebrow="Không gian Revenue Manager" title="Dashboard tải chặng">
      <DashboardScreen />
    </AppShell>
  );
}
