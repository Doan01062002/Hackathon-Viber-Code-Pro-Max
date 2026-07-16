import { ChatWindow } from "@/features/chat";

/** Route chỉ lắp ráp feature — mọi logic nằm trong features/chat. */
export default function ChatPage() {
  return (
    <>
      <h1>Chat với Agent</h1>
      <ChatWindow />
    </>
  );
}
