"use client";

import { use } from "react";
import { FeedbackDisplay } from "@/features/sessions/components/FeedbackDisplay";

type Props = {
  params: Promise<{ id: string }>;
};

export default function SessionResultPage({ params }: Props) {
  const { id } = use(params);
  const sessionId = parseInt(id, 10);

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          練習結果
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          お疲れ様でした！フィードバックを確認しましょう
        </p>
      </div>

      <FeedbackDisplay sessionId={sessionId} />
    </div>
  );
}
