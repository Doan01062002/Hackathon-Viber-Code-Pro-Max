import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "SRRM UI Console",
  description: "Giao diện điều hành doanh thu đường sắt SRRM",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <main>{children}</main>
      </body>
    </html>
  );
}
