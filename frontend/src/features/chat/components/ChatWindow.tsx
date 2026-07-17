"use client";

import { useChat } from "../hooks/useChat";
import { MessageInput } from "./MessageInput";
import { MessageList } from "./MessageList";

/** Điểm vào của feature chat — page chỉ cần render component này. */
export function ChatWindow() {
  const { messages, error, send, isLoading } = useChat();

  return (
    <section className="flex flex-col bg-white border border-outline-variant rounded-xl overflow-hidden shadow-sm h-[calc(100vh-16rem)] max-w-4xl mx-auto">
      <div className="flex-1 overflow-y-auto p-6 bg-surface-container-low/20">
        <MessageList messages={messages} />
        {error && (
          <p className="p-3 bg-error-container/30 text-error border border-error/20 rounded-lg text-xs font-bold mt-4" role="alert">
            {error}
          </p>
        )}
      </div>
      <div className="p-4 border-t border-outline-variant bg-surface-container-low">
        <MessageInput onSend={send} disabled={isLoading} />
      </div>
    </section>
  );
}
