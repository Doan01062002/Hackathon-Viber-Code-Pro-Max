"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode, useState } from "react";
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
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  return (
    <div className="min-h-screen bg-background text-on-surface">
      {/* SideNavBar Shell */}
      <aside
        className="h-screen w-56 fixed left-0 top-0 bg-surface-container-low border-r border-outline-variant flex flex-col py-4 z-50 select-none"
      >
        <div className="px-6 mb-5 flex items-center gap-2.5">
          <span className="material-symbols-outlined text-primary text-2xl bg-primary/10 p-1.5 rounded-xl select-none">train</span>
          <div>
            <h1 className="text-xl font-black text-primary leading-none">SRRM AI</h1>
            <p className="text-[10px] uppercase font-bold tracking-widest text-on-surface-variant opacity-70 mt-1">
              Quản lý Doanh thu
            </p>
          </div>
        </div>

        <nav className="flex-grow space-y-4 overflow-y-auto custom-scrollbar pr-1">
          {/* Passenger Section */}
          <div className="px-3">
            <p className="px-4 text-[11px] font-black text-on-surface-variant/60 uppercase tracking-widest mb-2">
              Cổng Hành Khách
            </p>
            {navItems
              .filter((item) => item.group === "passenger")
              .map((item) => {
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-all duration-200 ease-in-out cursor-pointer ${
                      active
                        ? "text-primary font-extrabold border-r-4 border-primary bg-surface-container-high"
                        : "text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface"
                    }`}
                    href={item.href}
                  >
                    <span className="material-symbols-outlined text-base">{getIconName(item.icon)}</span>
                    <span className="text-xs font-semibold">{item.label}</span>
                  </Link>
                );
              })}
          </div>

          {/* Admin Section */}
          <div className="px-3">
            <p className="px-4 text-[11px] font-black text-on-surface-variant/60 uppercase tracking-widest mb-2">
              Điều Hành Doanh Thu
            </p>
            {navItems
              .filter((item) => item.group === "admin")
              .map((item) => {
                const active = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-all duration-200 ease-in-out cursor-pointer ${
                      active
                        ? "text-primary font-extrabold border-r-4 border-primary bg-surface-container-high"
                        : "text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface"
                    }`}
                    href={item.href}
                  >
                    <span className="material-symbols-outlined text-base">{getIconName(item.icon)}</span>
                    <span className="text-xs font-semibold">{item.label}</span>
                  </Link>
                );
              })}
          </div>
        </nav>

        <div className="px-3 mt-auto pt-2 border-t border-outline-variant">
          <button
            className="w-full py-2 bg-primary text-on-primary rounded-xl font-bold text-xs shadow-lg shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all cursor-pointer"
            onClick={() => window.alert("Đang chuẩn bị xuất báo cáo doanh thu động...")}
          >
            Xuất báo cáo
          </button>
        </div>
      </aside>

      {/* TopNavBar Shell */}
      <header
        className="flex justify-between items-center h-16 px-8 w-[calc(100%-14rem)] ml-56 bg-surface border-b border-outline-variant fixed top-0 z-40"
      >
        <div className="flex items-center gap-8">
          <span className="text-lg font-black text-on-surface">{title}</span>
        </div>
        <div className="flex items-center gap-6">
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-outline text-sm">search</span>
            <input
              className="pl-10 pr-4 py-1.5 bg-surface-container-low border border-outline-variant rounded-full text-xs w-[400px] focus:w-[480px] focus:border-primary transition-all focus:outline-none"
              placeholder="Tìm kiếm chặng hoặc tồn kho ghế..."
              type="text"
            />
          </div>
          <div className="h-6 w-px bg-outline-variant"></div>
          <div className="flex items-center gap-4">
            <div className="flex gap-2 items-center">
              <span className="material-symbols-outlined p-2 hover:bg-surface-container-high rounded-full cursor-pointer transition-colors text-on-surface-variant text-base leading-none">notifications</span>
              <span className="material-symbols-outlined p-2 hover:bg-surface-container-high rounded-full cursor-pointer transition-colors text-on-surface-variant text-base leading-none">history</span>
              
              {/* Interactive Profile Avatar & Popup */}
              <div className="relative ml-2">
                <button
                  onClick={() => setShowProfileMenu(!showProfileMenu)}
                  className="flex items-center gap-2 px-2.5 py-1 hover:bg-surface-container-high rounded-lg cursor-pointer transition-colors text-on-surface-variant focus:outline-none select-none border border-outline-variant/35"
                >
                  <img
                    className="w-6 h-6 rounded-full object-cover bg-surface-container-highest"
                    alt="User Avatar"
                    src="https://lh3.googleusercontent.com/aida-public/AB6AXuCcaWGkMGSlfdSbZpcl7uvv_GMlm-69Dc8roJ9Mu4gxrm3kekOE1Fuod-yisy0jt6nLjqGMLkC6qEPmtyWJdu8YP4c-ogy74ljysoAYRJmM1uzMpj0kyxTLH4i7RpHix3mI25ilCn1lV82r3WykYOsUt8o7MPvk72_GQBc0PZ4_C3vocTpESy54l0fLLxuj1Rv-pNkOxlHNAgxvrLiu0A-dZT4ycszZ7mWP2pPSUc9QidKUJwYJ86MOtPKGRCI-sMq4SKPNwhVbqXaw"
                  />
                  <span className="text-xs font-bold text-on-surface truncate max-w-[80px]">Quản trị viên</span>
                  <span className="material-symbols-outlined text-xs leading-none">arrow_drop_down</span>
                </button>

                {showProfileMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-white border border-outline-variant rounded-xl shadow-lg py-2 z-50">
                    <div className="px-4 py-2 border-b border-outline-variant/30">
                      <p className="font-bold text-xs text-on-surface">Quản trị viên</p>
                      <p className="text-[10px] text-on-surface-variant font-medium mt-0.5">administrator@srrm.vn</p>
                    </div>
                    <div className="py-1">
                      <a href="#" className="flex items-center gap-3 px-4 py-2 text-xs text-on-surface-variant hover:bg-surface-container-low transition-colors">
                        <span className="material-symbols-outlined text-sm leading-none">person</span>
                        Thông tin cá nhân
                      </a>
                      <a href="#" className="flex items-center gap-3 px-4 py-2 text-xs text-on-surface-variant hover:bg-surface-container-low transition-colors">
                        <span className="material-symbols-outlined text-sm leading-none">settings</span>
                        Cài đặt hệ thống
                      </a>
                      <a href="#" className="flex items-center gap-3 px-4 py-2 text-xs text-on-surface-variant hover:bg-surface-container-low transition-colors">
                        <span className="material-symbols-outlined text-sm leading-none">security</span>
                        Bảo mật & Token
                      </a>
                    </div>
                    <div className="border-t border-outline-variant/30 mt-1 pt-1">
                      <a href="#" className="flex items-center gap-3 px-4 py-2 text-xs text-red-600 hover:bg-red-50 transition-colors font-bold">
                        <span className="material-symbols-outlined text-sm leading-none">logout</span>
                        Đăng xuất
                      </a>
                    </div>
                  </div>
                )}
              </div>

            </div>
          </div>
        </div>
      </header>
      {/* Main Content Area */}
      <main className="ml-56 mt-16 p-8">
        <div>
          <div className="rail-content">{children}</div>
        </div>
      </main>
    </div>
  );
}
