/** Type riêng của feature chat. */

export type ChatRole = "user" | "agent";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
};

/** Khớp với ChatRequest của backend. */
export type ChatRequestDto = {
  message: string;
};

/** Khớp với ChatResponse (backend/views/chat_view.py). */
export type ChatResponseDto = {
  response: string;
  analysis: string;
};
