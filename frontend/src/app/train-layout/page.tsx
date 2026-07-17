import { AppShell } from "@/features/rail-ui/components/AppShell";
import { TrainLayoutScreen } from "@/features/rail-ui/screens/TrainLayoutScreen";

export default function TrainLayoutPage() {
  return (
    <AppShell eyebrow="Không gian điều độ" title="Sơ đồ toa tàu và chọn ghế">
      <TrainLayoutScreen />
    </AppShell>
  );
}
