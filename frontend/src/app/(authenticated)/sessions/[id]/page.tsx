"use client";

import { use } from "react";
import { SessionRoom } from "@/features/sessions/components/SessionRoom";

type Props = {
  params: Promise<{ id: string }>;
};

export default function SessionDetailPage({ params }: Props) {
  const { id } = use(params);
  const sessionId = parseInt(id, 10);

  return (
    <div className="flex h-[calc(100vh-theme(spacing.16))] flex-col">
      <SessionRoom sessionId={sessionId} />
    </div>
  );
}
