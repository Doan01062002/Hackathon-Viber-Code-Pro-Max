import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "outline" | "ghost";
  size?: "default" | "sm";
};

export function Button({ variant = "primary", size = "default", className, ...props }: ButtonProps) {
  const baseStyle = "inline-flex items-center justify-center font-bold transition-all rounded-lg active:scale-95 disabled:opacity-50 disabled:pointer-events-none cursor-pointer";
  const variantStyles = {
    primary: "bg-primary text-on-primary hover:brightness-110 shadow-sm",
    outline: "border border-outline-variant text-on-surface hover:bg-surface-container",
    ghost: "text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface"
  };
  const sizeStyles = {
    default: "px-4 py-2 text-sm",
    sm: "px-3 py-1.5 text-xs"
  };
  return (
    <button
      className={cn(baseStyle, variantStyles[variant], sizeStyles[size], className)}
      {...props}
    />
  );
}
