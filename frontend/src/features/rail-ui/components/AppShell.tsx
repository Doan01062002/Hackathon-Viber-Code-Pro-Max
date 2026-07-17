"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import type { ReactNode } from "react";

import { navItems } from "@/features/rail-ui/mockData";

type AppShellProps = {
  title: string;
  eyebrow: string;
  children: ReactNode;
};

function NavIcon({ icon }: { icon: (typeof navItems)[number]["icon"] }) {
  switch (icon) {
    case "dashboard":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path d="M4 4h7v7H4zM13 4h7v5h-7zM13 11h7v9h-7zM4 13h7v7H4z" />
        </svg>
      );
    case "price":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path d="M5 6h9l5 5-8 8-5-5zM8.5 9.5h.01" />
        </svg>
      );
    case "simulation":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path d="M5 7h8M5 12h14M5 17h10M15 5v4M11 10v4M17 15v4" />
        </svg>
      );
    case "alert":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path d="M12 4 3 20h18zM12 9v4M12 17h.01" />
        </svg>
      );
    case "audit":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path d="M8 4h8v3h3v13H5V7h3zM8 12h8M8 16h6" />
        </svg>
      );
    case "train":
      return (
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path d="M7 4h10a3 3 0 0 1 3 3v7a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4V7a3 3 0 0 1 3-3zM8 8h3M13 8h3M9 18l-2 2M15 18l2 2" />
        </svg>
      );
    default:
      return null;
  }
}

export function AppShell({ title, eyebrow, children }: AppShellProps) {
  const pathname = usePathname();
  const [accountOpen, setAccountOpen] = useState(false);

  return (
    <div className="rail-shell">
      <a className="skip-link" href="#main-content">
        Bỏ qua điều hướng
      </a>

      <aside className="rail-sidebar" aria-label="Thanh điều hướng chính">
        <div className="rail-sidebar-top">
          <div className="rail-brand">
            <div className="rail-brand-mark" aria-hidden="true">
              SR
            </div>
            <div className="rail-brand-copy">
              <strong>SRRM Console</strong>
              <span>Revenue Control Tower</span>
            </div>
          </div>
        </div>

        <nav className="rail-nav">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                aria-current={active ? "page" : undefined}
                className={`rail-nav-link${active ? " rail-nav-link-active" : ""}`}
                href={item.href}
              >
                <span className="rail-nav-icon">
                  <NavIcon icon={item.icon} />
                </span>
                <span className="rail-nav-copy">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-actions">
          <button className="rail-nav-link rail-nav-link-utility" type="button">
            <span className="rail-nav-icon">
              <svg aria-hidden="true" viewBox="0 0 24 24">
                <path d="M12 8.5A3.5 3.5 0 1 0 12 15.5A3.5 3.5 0 1 0 12 8.5Z" />
                <path d="M19 12a7.46 7.46 0 0 0-.08-1l2.08-1.62-2-3.46-2.48 1a7.9 7.9 0 0 0-1.72-1l-.4-2.62H10.4L10 5.92a7.9 7.9 0 0 0-1.72 1l-2.48-1-2 3.46L5.88 11a7.92 7.92 0 0 0 0 2l-2.08 1.62 2 3.46 2.48-1a7.9 7.9 0 0 0 1.72 1l.4 2.62h4l.4-2.62a7.9 7.9 0 0 0 1.72-1l2.48 1 2-3.46L18.92 13c.05-.33.08-.66.08-1Z" />
              </svg>
            </span>
            <span className="rail-nav-copy">Cài đặt</span>
          </button>
        </div>
      </aside>

      <main className="rail-main" id="main-content">
        <div className="rail-main-inner">
          <header className="topbar">
            <div className="topbar-main">
              <div className="topbar-title-block">
                <div className="topbar-crumbs">
                  <p className="breadcrumb">Revenue Manager / {title}</p>
                  <p className="eyebrow">{eyebrow}</p>
                </div>
                <h1>{title}</h1>
                <p className="topbar-subtitle">Bảng điều hành dành cho đội vận hành doanh thu và điều phối chặng.</p>
                <div className="topbar-status">
                  <span className="topbar-status-item">Tuyến Bắc - Nam</span>
                  <span className="topbar-status-item">Tàu SE3</span>
                  <span className="topbar-status-item">Cập nhật 5 phút trước</span>
                </div>
              </div>

              <div className="topbar-actions">
                <button className="btn btn-ghost" type="button">
                  Hôm nay, 17/07/2026
                </button>
                <button className="btn btn-primary" type="button">
                  Xuất báo cáo
                </button>

                <div className={`account-menu${accountOpen ? " account-menu-open" : ""}`}>
                  <button
                    aria-expanded={accountOpen}
                    className="topbar-user-chip"
                    onClick={() => setAccountOpen((value) => !value)}
                    type="button"
                  >
                    <span className="topbar-user-avatar" aria-hidden="true">
                      TN
                    </span>
                    <span className="topbar-user-copy">
                      <strong>Thu Nga</strong>
                      <small>Revenue Manager</small>
                    </span>
                  </button>

                  {accountOpen ? (
                    <div className="account-dropdown">
                      <button className="account-dropdown-item" type="button">
                        Cài đặt tài khoản
                      </button>
                      <button className="account-dropdown-item" type="button">
                        Tùy chọn giao diện
                      </button>
                      <button className="account-dropdown-item account-dropdown-item-danger" type="button">
                        Đăng xuất
                      </button>
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          </header>

          <div className="rail-content">{children}</div>
        </div>
      </main>
    </div>
  );
}
