import type { ChatMessage } from "../types";

type MessageListProps = {
  messages: ChatMessage[];
};

export function MessageList({ messages }: MessageListProps) {
  if (messages.length === 0) {
    return <p className="empty">Gõ gì đó để bắt đầu trò chuyện với agent.</p>;
  }

  return (
    <ul className="message-list">
      {messages.map((m) => (
        <li key={m.id} className={`message message-${m.role}`}>
          <span className="message-role">{m.role === "user" ? "Bạn" : "Agent"}</span>
          <p className="message-content">{m.content}</p>
        </li>
      ))}
    </ul>
  );
}
