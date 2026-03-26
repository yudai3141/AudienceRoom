"use client";

import Link from "next/link";
import { SessionHistoryList } from "@/features/sessions/components/SessionHistoryList";
import { Button } from "@/components/ui";

export default function SessionsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            練習履歴
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            過去の練習セッションを確認できます
          </p>
        </div>
        <Link href="/sessions/new">
          <Button>新しい練習を開始</Button>
        </Link>
      </div>

      <SessionHistoryList />
    </div>
  );
}
