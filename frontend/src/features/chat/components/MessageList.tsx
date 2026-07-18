import type { ChatMessage } from "../types";

type MessageListProps = {
  messages: ChatMessage[];
};

export function MessageList({ messages }: MessageListProps) {
  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8 opacity-60">
        <span className="material-symbols-outlined text-4xl text-primary animate-pulse mb-3">chat_bubble</span>
        <p className="text-xs font-bold text-on-surface-variant">Gõ gì đó để bắt đầu trò chuyện với agent.</p>
      </div>
    );
  }

  return (
    <ul className="space-y-4 flex flex-col">
      {messages.map((m) => {
        const isUser = m.role === "user";
        return (
          <li
            key={m.id}
            className={`flex flex-col max-w-[80%] rounded-xl p-4 shadow-sm text-sm leading-relaxed ${
              isUser
                ? "self-end bg-primary text-on-primary rounded-tr-none"
                : "self-start bg-white text-on-surface border border-outline-variant rounded-tl-none border-l-4 border-l-primary"
            }`}
          >
            <span className={`text-[10px] uppercase font-bold tracking-wider mb-1 ${isUser ? "text-primary-fixed" : "text-primary"}`}>
              {isUser ? "Bạn" : "Agent"}
            </span>
            <p className="font-semibold whitespace-pre-wrap">{m.content}</p>
          </li>
        );
      })}
    </ul>
  );
}
