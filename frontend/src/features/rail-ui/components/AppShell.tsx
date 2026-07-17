"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { navItems } from "@/features/rail-ui/mockData";

type AppShellProps = {
  title: string;
  eyebrow: string;
  children: ReactNode;
};

function getIconName(icon: string) {
  switch (icon) {
    case "confirmation_number": return "confirmation_number";
    case "dashboard": return "dashboard";
    case "price": return "payments";
    case "simulation": return "analytics";
    case "alert": return "notifications";
    case "audit": return "history";
    case "train": return "train";
    default: return "menu";
  }
}

export function AppShell({ title, eyebrow, children }: AppShellProps) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-background text-on-surface">
      {/* SideNavBar Shell */}
      <aside
        className="h-screen w-64 fixed left-0 top-0 bg-surface-container-low border-r border-outline-variant flex flex-col py-8 z-50 select-none"
      >
        <div className="px-6 mb-8">
          <h1 className="text-2xl font-extrabold text-primary">SRRM AI</h1>
          <p className="text-[10px] uppercase font-bold tracking-widest text-on-surface-variant opacity-70 mt-1">
            Rail Revenue Management
          </p>
        </div>

        <nav className="flex-grow space-y-6">
          {/* Passenger Section */}
          <div className="px-3">
            <p className="px-4 text-[9px] font-bold text-on-surface-variant/50 uppercase tracking-widest mb-2">
              Cổng Hành Khách (Portal)
            </p>
            {navItems
              .filter((item) => item.group === "passenger")
              .map((item) => {
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-200 ease-in-out cursor-pointer ${
                      active
                        ? "text-primary font-extrabold border-r-4 border-primary bg-surface-container-high"
                        : "text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface"
                    }`}
                    href={item.href}
                  >
                    <span className="material-symbols-outlined">{getIconName(item.icon)}</span>
                    <span className="text-sm font-semibold">{item.label}</span>
                  </Link>
                );
              })}
          </div>

          {/* Admin Section */}
          <div className="px-3">
            <p className="px-4 text-[9px] font-bold text-on-surface-variant/50 uppercase tracking-widest mb-2">
              Điều Hành Doanh Thu (Control Tower)
            </p>
            {navItems
              .filter((item) => item.group === "admin")
              .map((item) => {
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-200 ease-in-out cursor-pointer ${
                      active
                        ? "text-primary font-extrabold border-r-4 border-primary bg-surface-container-high"
                        : "text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface"
                    }`}
                    href={item.href}
                  >
                    <span className="material-symbols-outlined">{getIconName(item.icon)}</span>
                    <span className="text-sm font-semibold">{item.label}</span>
                  </Link>
                );
              })}
          </div>
        </nav>

        <div className="px-4 mt-auto space-y-2">
          <button
            className="w-full py-3 bg-primary text-on-primary rounded-xl font-bold text-xs shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all"
          >
            Generate Report
          </button>
          <div className="pt-4 border-t border-outline-variant">
            <a
              className="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container-high rounded-lg transition-colors"
              href="#"
            >
              <span className="material-symbols-outlined">settings</span>
              <span className="text-sm">Settings</span>
            </a>
            <a
              className="flex items-center gap-3 px-4 py-3 text-on-surface-variant hover:bg-surface-container-high rounded-lg transition-colors"
              href="#"
            >
              <span className="material-symbols-outlined">help_outline</span>
              <span className="text-sm">Support</span>
            </a>
          </div>
          <div className="flex items-center gap-3 px-4 py-4 mt-2">
            <img
              className="w-8 h-8 rounded-full bg-surface-container-highest object-cover"
              alt="Admin Profile"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuCcaWGkMGSlfdSbZpcl7uvv_GMlm-69Dc8roJ9Mu4gxrm3kekOE1Fuod-yisy0jt6nLjqGMLkC6qEPmtyWJdu8YP4c-ogy74ljysoAYRJmM1uzMpj0kyxTLH4i7RpHix3mI25ilCn1lV82r3WykYOsUt8o7MPvk72_GQBc0PZ4_C3vocTpESy54l0fLLxuj1Rv-pNkOxlHNAgxvrLiu0A-dZT4ycszZ7mWP2pPSUc9QidKUJwYJ86MOtPKGRCI-sMq4SKPNwhVbqXaw"
            />
            <div className="overflow-hidden">
              <p className="font-bold text-on-surface truncate text-xs">Admin User</p>
              <p className="text-[10px] text-on-surface-variant truncate">Administrator</p>
            </div>
          </div>
        </div>
      </aside>

      {/* TopNavBar Shell */}
      <header
        className="flex justify-between items-center h-16 px-8 w-[calc(100%-16rem)] ml-64 bg-surface border-b border-outline-variant fixed top-0 z-40"
      >
        <div className="flex items-center gap-8">
          <span className="text-lg font-black text-on-surface">SRRM Enterprise AI</span>
          <nav className="flex gap-6">
            <a className="text-on-surface-variant text-xs font-semibold hover:text-primary transition-all" href="#">Network</a>
            <a className="text-primary border-b-2 border-primary font-bold pb-1 text-xs" href="#">Inventory</a>
            <a className="text-on-surface-variant text-xs font-semibold hover:text-primary transition-all" href="#">Analytics</a>
          </nav>
        </div>
        <div className="flex items-center gap-6">
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-outline text-sm">search</span>
            <input
              className="pl-10 pr-4 py-1.5 bg-surface-container-low border border-outline-variant rounded-full text-xs w-64 focus:w-80 focus:border-primary transition-all focus:outline-none"
              placeholder="Search routes or inventory..."
              type="text"
            />
          </div>
          <div className="h-6 w-px bg-outline-variant"></div>
          <div className="flex items-center gap-4">
            <button
              className="flex items-center gap-2 px-4 py-1.5 bg-primary-container text-on-primary-container rounded-lg font-bold text-xs hover:brightness-110 transition-all scale-95 active:scale-90"
            >
              <span className="material-symbols-outlined text-sm">filter_alt</span>
              Apply Filters
            </button>
            <div className="flex gap-2">
              <span className="material-symbols-outlined p-2 hover:bg-surface-container-high rounded-full cursor-pointer transition-colors text-on-surface-variant text-base">notifications</span>
              <span className="material-symbols-outlined p-2 hover:bg-surface-container-high rounded-full cursor-pointer transition-colors text-on-surface-variant text-base">history</span>
              <span className="material-symbols-outlined p-2 hover:bg-surface-container-high rounded-full cursor-pointer transition-colors text-on-surface-variant text-base">account_circle</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="ml-64 mt-16 p-8">
        <div>
          {/* Section Breadcrumbs */}
          <div className="mb-6">
            <p className="text-xs text-on-surface-variant opacity-70">
              {pathname.startsWith("/booking") ? "Passenger Portal" : "Revenue Manager"} / {title}
            </p>
            <p className="text-[10px] text-primary font-bold uppercase mt-1">
              {eyebrow}
            </p>
          </div>
          <div className="rail-content">{children}</div>
        </div>
      </main>
    </div>
  );
}
