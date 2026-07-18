import { AppShell } from "@/features/rail-ui/components/AppShell";
import { AvailabilityScreen } from "@/features/rail-ui/screens/AvailabilityScreen";

export default function AvailabilityPage() {
  return (
    <AppShell eyebrow="Tối ưu năng lực" title="Ghép chặng trống & Khả dụng chỗ">
      <AvailabilityScreen />
    </AppShell>
  );
}
