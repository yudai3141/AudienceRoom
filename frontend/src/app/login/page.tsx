"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { Spinner } from "@/components/ui";

export default function LoginPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.replace("/dashboard");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="flex flex-1 items-center justify-center">
      <div className="w-full max-w-sm space-y-6 text-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            AudienceRoom
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            人前で話す練習を、もっとリアルに。
          </p>
        </div>
        <p className="text-slate-400">Phase 6-1 で LoginForm を実装予定</p>
      </div>
    </div>
  );
}
