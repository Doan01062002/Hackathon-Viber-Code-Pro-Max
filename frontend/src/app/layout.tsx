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
        {/* eslint-disable-next-line @next/next/no-sync-scripts */}
        <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500&display=swap"
          rel="stylesheet"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              tailwind.config = {
                darkMode: "class",
                theme: {
                  extend: {
                    colors: {
                      "tertiary-fixed-dim": "#c4c7c9",
                      "surface-container-high": "#dce9ff",
                      "on-primary": "#ffffff",
                      secondary: "#565e74",
                      "error-container": "#ffdad6",
                      "on-primary-fixed": "#0f0069",
                      "surface-dim": "#cbdbf5",
                      "on-primary-fixed-variant": "#3323cc",
                      "tertiary-container": "#5e6163",
                      "on-background": "#0b1c30",
                      "outline-variant": "#c7c4d8",
                      tertiary: "#46494b",
                      "surface-bright": "#f8f9ff",
                      background: "#f8f9ff",
                      "tertiary-fixed": "#e0e3e5",
                      "on-error-container": "#93000a",
                      primary: "#3525cd",
                      "on-surface-variant": "#464555",
                      outline: "#777587",
                      "surface-container-lowest": "#ffffff",
                      "surface-container": "#e5eeff",
                      "surface-container-highest": "#d3e4fe",
                      "primary-container": "#4f46e5",
                      "secondary-fixed-dim": "#bec6e0",
                      "surface-container-low": "#eff4ff",
                      "inverse-surface": "#213145",
                      "secondary-fixed": "#dae2fd",
                      "primary-fixed-dim": "#c3c0ff",
                      "on-tertiary": "#ffffff",
                      "inverse-on-surface": "#eaf1ff",
                      "on-tertiary-container": "#dadcde",
                      "surface-tint": "#4d44e3",
                      "on-surface": "#0b1c30",
                      "on-secondary-fixed": "#131b2e",
                      "primary-fixed": "#e2dfff",
                      "secondary-container": "#dae2fd",
                      "on-primary-container": "#dad7ff",
                      "surface-variant": "#d3e4fe",
                      "on-error": "#ffffff",
                      "on-tertiary-fixed": "#191c1e",
                      "on-tertiary-fixed-variant": "#444749",
                      "inverse-primary": "#c3c0ff",
                      error: "#ba1a1a",
                      "on-secondary-fixed-variant": "#3f465c",
                      "on-secondary": "#ffffff",
                      surface: "#f8f9ff",
                      "on-secondary-container": "#5c647a",
                    },
                    borderRadius: {
                      DEFAULT: "0.125rem",
                      lg: "0.25rem",
                      xl: "0.5rem",
                      full: "0.75rem",
                    },
                    spacing: {
                      base: "4px",
                      "stack-md": "1rem",
                      "container-padding": "2rem",
                      gutter: "1.5rem",
                      "stack-lg": "2rem",
                      "stack-sm": "0.5rem",
                    },
                    fontFamily: {
                      "headline-lg-mobile": ["Inter"],
                      "body-md": ["Inter"],
                      "headline-md": ["Inter"],
                      "label-sm": ["JetBrains Mono"],
                      "headline-lg": ["Inter"],
                      "display-lg": ["Inter"],
                      "body-lg": ["Inter"],
                    },
                    fontSize: {
                      "headline-lg-mobile": ["26px", { lineHeight: "34px", fontWeight: "600" }],
                      "body-md": ["16px", { lineHeight: "22px", fontWeight: "400" }],
                      "headline-md": ["26px", { lineHeight: "34px", fontWeight: "600" }],
                      "label-sm": ["14px", { lineHeight: "18px", letterSpacing: "0.05em", fontWeight: "500" }],
                      "headline-lg": ["32px", { lineHeight: "38px", letterSpacing: "-0.01em", fontWeight: "600" }],
                      "display-lg": ["50px", { lineHeight: "1.2", letterSpacing: "-0.02em", fontWeight: "700" }],
                      "body-lg": ["20px", { lineHeight: "30px", fontWeight: "400" }],
                      
                      "xs": ["14px", { lineHeight: "18px" }],
                      "sm": ["16px", { lineHeight: "22px" }],
                      "base": ["18px", { lineHeight: "26px" }],
                      "lg": ["20px", { lineHeight: "28px" }],
                      "xl": ["22px", { lineHeight: "30px" }],
                      "2xl": ["26px", { lineHeight: "34px" }],
                      "3xl": ["32px", { lineHeight: "38px" }],
                    },
                  },
                },
              };
            `,
          }}
        />
      </head>
      <body className="font-body-md text-body-md bg-background text-on-surface select-none">
        {children}
      </body>
    </html>
  );
}
