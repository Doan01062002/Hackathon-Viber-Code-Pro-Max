import { AppShell } from "@/features/rail-ui/components/AppShell";
import { SimulationScreen } from "@/features/rail-ui/screens/SimulationScreen";

export default function SimulationPage() {
  return (
    <AppShell eyebrow="Tính toán & Thử nghiệm" title="Mô phỏng & Phê duyệt chính sách">
      <SimulationScreen />
    </AppShell>
  );
}
