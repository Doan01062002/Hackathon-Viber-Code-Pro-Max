import { AppShell } from "@/features/rail-ui/components/AppShell";
import { QuoteScreen } from "@/features/rail-ui/screens/QuoteScreen";

export default function QuotePage() {
  return (
    <AppShell eyebrow="Không gian Revenue Manager" title="Báo giá và phương án thay thế">
      <QuoteScreen />
    </AppShell>
  );
}
