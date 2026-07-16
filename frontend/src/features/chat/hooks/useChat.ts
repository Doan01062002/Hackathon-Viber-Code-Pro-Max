"use client";

import { useCallback, useState } from "react";

import { ApiError } from "@/lib/api/client";
import type { AsyncStatus } from "@/types";

import { sendChatMessage } from "../api/chatApi";
import type { ChatMessage } from "../types";

let nextId = 0;
const makeId = () => `${Date.now()}-${nextId++}`;

/**
 * Toàn bộ logic của feature chat. Component chỉ render những gì hook trả về.
 * Muốn đổi sang streaming hay thêm lịch sử hội thoại — sửa ở đây, UI không đổi.
 */
export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<AsyncStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  const send = useCallback(async (content: string) => {
    const trimmed = content.trim();
    if (!trimmed) return;

    setMessages((prev) => [...prev, { id: makeId(), role: "user", content: trimmed }]);
    setStatus("loading");
    setError(null);

    try {
      const data = await sendChatMessage(trimmed);
      setMessages((prev) => [...prev, { id: makeId(), role: "agent", content: data.response }]);
      setStatus("success");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Đã có lỗi xảy ra");
      setStatus("error");
    }
  }, []);

  return { messages, status, error, send, isLoading: status === "loading" };
}
