"use client";

import { useChat } from "../hooks/useChat";
import { MessageInput } from "./MessageInput";
import { MessageList } from "./MessageList";

/** Điểm vào của feature chat — page chỉ cần render component này. */
export function ChatWindow() {
  const { messages, error, send, isLoading } = useChat();

  return (
    <section className="chat-window">
      <MessageList messages={messages} />
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <MessageInput onSend={send} disabled={isLoading} />
    </section>
  );
}
