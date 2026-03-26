"use client";

import { SessionSetupForm } from "@/features/sessions/components/SessionSetupForm";

export default function NewSessionPage() {
  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          練習設定
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          練習の内容を設定して開始しましょう
        </p>
      </div>

      <SessionSetupForm />
    </div>
  );
}
