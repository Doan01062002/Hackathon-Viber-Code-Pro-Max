"use client";

import { type FormEvent, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

type MessageInputProps = {
  onSend: (message: string) => void;
  disabled?: boolean;
};

export function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [value, setValue] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSend(value);
    setValue("");
  }

  return (
    <form className="message-input" onSubmit={handleSubmit}>
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Nhập tin nhắn…"
        disabled={disabled}
        aria-label="Tin nhắn"
      />
      <Button type="submit" disabled={disabled || !value.trim()}>
        {disabled ? "Đang gửi…" : "Gửi"}
      </Button>
    </form>
  );
}
