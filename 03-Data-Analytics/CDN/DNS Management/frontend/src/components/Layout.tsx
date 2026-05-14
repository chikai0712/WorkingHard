import Link from "next/link";
import { ReactNode } from "react";

const links = [
  { href: "/", label: "儀表板" },
  { href: "/accounts", label: "帳號管理" },
  { href: "/domains", label: "域名列表" },
  { href: "/sync-history", label: "同步歷史" }
];

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white shadow">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <h1 className="text-xl font-semibold text-slate-900">CDN/DNS 控制台</h1>
          <nav className="flex gap-4 text-sm text-slate-600">
            {links.map((link) => (
              <Link key={link.href} href={link.href} className="hover:text-indigo-600">
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  );
}

