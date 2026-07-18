import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "SRRM Enterprise AI",
  description: "Smart Rail Revenue Management System",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi" className="light">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-body-md text-body-md bg-background text-on-surface select-none">
        {children}
      </body>
    </html>
  );
}
