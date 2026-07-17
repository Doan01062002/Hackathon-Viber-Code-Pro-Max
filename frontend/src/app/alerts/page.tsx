import { AppShell } from "@/features/rail-ui/components/AppShell";
import { AlertsScreen } from "@/features/rail-ui/screens/AlertsScreen";

export default function AlertsPage() {
  return (
    <AppShell eyebrow="Không gian Revenue Manager" title="Cảnh báo vận hành">
      <AlertsScreen />
    </AppShell>
  );
}
