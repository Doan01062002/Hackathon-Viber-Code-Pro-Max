import { apiClient } from "@/lib/api/client";

import type { ChatRequestDto, ChatResponseDto } from "../types";

/** Endpoint của feature chat. Component không biết đường dẫn API là gì. */
export function sendChatMessage(message: string, signal?: AbortSignal) {
  const body: ChatRequestDto = { message };
  return apiClient.post<ChatResponseDto>("/api/v1/chat", body, { signal });
}
