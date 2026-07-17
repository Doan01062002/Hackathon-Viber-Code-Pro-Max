import type { InputHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type InputProps = InputHTMLAttributes<HTMLInputElement>;

export function Input({ className, ...props }: InputProps) {
  return (
    <input
      className={cn(
        "bg-surface-container-low border border-outline-variant rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-primary focus:outline-none transition-all placeholder:text-outline w-full",
        className
      )}
      {...props}
    />
  );
}
