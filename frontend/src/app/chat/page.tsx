import { AppShell } from "@/features/rail-ui/components/AppShell";
import { ChatWindow } from "@/features/chat";

/** Route chỉ lắp ráp feature — mọi logic nằm trong features/chat. */
export default function ChatPage() {
  return (
    <AppShell eyebrow="Trợ lý AI" title="Chat điều vận">
      <ChatWindow />
    </AppShell>
  );
}
