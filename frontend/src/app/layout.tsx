import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Viber Coding Pro Max",
  description: "AI Agent built with LangGraph",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <main className="container">{children}</main>
      </body>
    </html>
  );
}
