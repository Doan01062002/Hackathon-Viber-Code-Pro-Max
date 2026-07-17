import { AppShell } from "@/features/rail-ui/components/AppShell";
import { SimulationScreen } from "@/features/rail-ui/screens/SimulationScreen";

export default function SimulationPage() {
  return (
    <AppShell eyebrow="Không gian Revenue Manager" title="Mô phỏng và phê duyệt">
      <SimulationScreen />
    </AppShell>
  );
}
