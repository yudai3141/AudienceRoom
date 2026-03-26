"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { Button } from "@/components/ui";

const navItems = [
  { href: "/dashboard", label: "ダッシュボード" },
  { href: "/sessions", label: "練習履歴" },
];

export function Header() {
  const pathname = usePathname();
  const { user, signOut } = useAuth();

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <div className="flex items-center gap-8">
          <Link
            href="/dashboard"
            className="text-lg font-bold tracking-tight text-slate-900"
          >
            AudienceRoom
          </Link>

          {user && (
            <nav className="hidden items-center gap-1 sm:flex">
              {navItems.map((item) => {
                const isActive = pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-indigo-50 text-indigo-700"
                        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          )}
        </div>

        {user && (
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-slate-500 sm:block">
              {user.displayName ?? user.email}
            </span>
            <Button variant="ghost" size="sm" onClick={signOut}>
              ログアウト
            </Button>
          </div>
        )}
      </div>
    </header>
  );
}
