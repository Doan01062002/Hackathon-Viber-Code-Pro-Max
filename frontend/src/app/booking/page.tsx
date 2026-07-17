import { AppShell } from "@/features/rail-ui/components/AppShell";
import { BookingScreen } from "@/features/rail-ui/screens/BookingScreen";

export default function BookingPage() {
  return (
    <AppShell eyebrow="Cổng Hành Khách" title="Đặt vé tàu trực tuyến">
      <BookingScreen />
    </AppShell>
  );
}
