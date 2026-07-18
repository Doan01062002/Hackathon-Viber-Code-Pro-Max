import { AppShell } from "@/features/rail-ui/components/AppShell";
import { AuditScreen } from "@/features/rail-ui/screens/AuditScreen";

export default function AuditPage() {
  return (
    <AppShell eyebrow="Không gian IT / quản trị" title="Nhật ký kiểm toán">
      <AuditScreen />
    </AppShell>
  );
}
