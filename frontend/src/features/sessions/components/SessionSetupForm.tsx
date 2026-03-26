"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button, Input, Textarea, Card, Spinner } from "@/components/ui";
import { useAiCharacters } from "../hooks/useAiCharacters";
import { useCreateSession } from "../hooks/useCreateSession";
import { useCurrentUser } from "@/features/auth/hooks/useCurrentUser";

const sessionModes = [
  { value: "interview", label: "面接練習" },
  { value: "presentation", label: "プレゼン練習" },
] as const;

const participantCounts = [
  { value: 1, label: "1人" },
  { value: 2, label: "2人" },
  { value: 3, label: "3人" },
] as const;

const sessionSchema = z.object({
  mode: z.enum(["interview", "presentation"]),
  participantCount: z.number().min(1).max(3),
  theme: z.string().optional(),
  userGoal: z.string().optional(),
  userConcerns: z.string().optional(),
  feedbackEnabled: z.boolean(),
});

type SessionFormValues = z.infer<typeof sessionSchema>;

export function SessionSetupForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  const { data: user, isLoading: userLoading } = useCurrentUser();
  const { data: characters, isLoading: charactersLoading } = useAiCharacters();
  const createSession = useCreateSession();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<SessionFormValues>({
    resolver: zodResolver(sessionSchema),
    defaultValues: {
      mode: "interview",
      participantCount: 1,
      feedbackEnabled: true,
    },
  });

  const selectedMode = watch("mode");
  const selectedParticipantCount = watch("participantCount");

  const onSubmit = async (values: SessionFormValues) => {
    if (!user) {
      setError("ユーザー情報が取得できません");
      return;
    }

    setError(null);

    try {
      const session = await createSession.mutateAsync({
        user_id: user.id,
        mode: values.mode,
        participant_count: values.participantCount,
        feedback_enabled: values.feedbackEnabled,
        theme: values.theme || null,
        user_goal: values.userGoal || null,
        user_concerns: values.userConcerns || null,
      });

      router.push(`/sessions/${session.id}`);
    } catch {
      setError("セッションの作成に失敗しました");
    }
  };

  if (userLoading || charactersLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        ユーザー情報が取得できません。再度ログインしてください。
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <Card>
        <div className="p-6">
          <h2 className="text-lg font-semibold text-slate-900">練習モード</h2>
          <p className="mt-1 text-sm text-slate-500">
            どのような練習をしますか？
          </p>

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {sessionModes.map((mode) => (
              <label
                key={mode.value}
                className={`relative flex cursor-pointer rounded-lg border p-4 transition-colors ${
                  selectedMode === mode.value
                    ? "border-indigo-600 bg-indigo-50 ring-2 ring-indigo-600"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <input
                  type="radio"
                  value={mode.value}
                  {...register("mode")}
                  className="sr-only"
                />
                <div>
                  <span
                    className={`text-sm font-medium ${
                      selectedMode === mode.value
                        ? "text-indigo-900"
                        : "text-slate-900"
                    }`}
                  >
                    {mode.label}
                  </span>
                  <span className="mt-1 block text-xs text-slate-500">
                    {mode.value === "interview"
                      ? "模擬面接官と面接の練習"
                      : "聴衆の前でプレゼンの練習"}
                  </span>
                </div>
              </label>
            ))}
          </div>
          {errors.mode && (
            <p className="mt-2 text-sm text-red-600">{errors.mode.message}</p>
          )}
        </div>
      </Card>

      <Card>
        <div className="p-6">
          <h2 className="text-lg font-semibold text-slate-900">参加者数</h2>
          <p className="mt-1 text-sm text-slate-500">
            {selectedMode === "interview"
              ? "面接官の人数を選択"
              : "聴衆の人数を選択"}
          </p>

          <div className="mt-4 flex gap-4">
            {participantCounts.map((count) => (
              <label
                key={count.value}
                className={`relative flex cursor-pointer items-center justify-center rounded-lg border px-6 py-3 transition-colors ${
                  selectedParticipantCount === count.value
                    ? "border-indigo-600 bg-indigo-50 ring-2 ring-indigo-600"
                    : "border-slate-200 hover:border-slate-300"
                }`}
              >
                <input
                  type="radio"
                  value={count.value}
                  onChange={() => setValue("participantCount", count.value)}
                  checked={selectedParticipantCount === count.value}
                  className="sr-only"
                />
                <span
                  className={`text-sm font-medium ${
                    selectedParticipantCount === count.value
                      ? "text-indigo-900"
                      : "text-slate-900"
                  }`}
                >
                  {count.label}
                </span>
              </label>
            ))}
          </div>

          {characters && characters.length > 0 && (
            <div className="mt-4">
              <p className="text-sm text-slate-500">
                使用可能なAIキャラクター: {characters.length}人
              </p>
            </div>
          )}
        </div>
      </Card>

      <Card>
        <div className="p-6 space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              練習テーマ（任意）
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              {selectedMode === "interview"
                ? "例：エンジニア職の最終面接、志望動機について"
                : "例：新製品発表、チームへの進捗報告"}
            </p>
          </div>

          <Input
            placeholder="テーマを入力..."
            {...register("theme")}
            error={errors.theme?.message}
          />
        </div>
      </Card>

      <Card>
        <div className="p-6 space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              練習の目標（任意）
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              今日の練習で達成したいことは？
            </p>
          </div>

          <Textarea
            placeholder="例：緊張せずに話す、論理的に説明する..."
            rows={3}
            {...register("userGoal")}
          />
        </div>
      </Card>

      <Card>
        <div className="p-6 space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              不安な点・苦手な点（任意）
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              事前に伝えておきたいことがあれば
            </p>
          </div>

          <Textarea
            placeholder="例：想定外の質問に弱い、話が長くなりがち..."
            rows={3}
            {...register("userConcerns")}
          />
        </div>
      </Card>

      <Card>
        <div className="p-6">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              {...register("feedbackEnabled")}
              className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-600"
            />
            <div>
              <span className="text-sm font-medium text-slate-900">
                フィードバックを受け取る
              </span>
              <p className="text-xs text-slate-500">
                練習終了後にAIからのフィードバックを表示します
              </p>
            </div>
          </label>
        </div>
      </Card>

      <div className="flex justify-end gap-4">
        <Button
          type="button"
          variant="outline"
          onClick={() => router.back()}
        >
          キャンセル
        </Button>
        <Button type="submit" loading={createSession.isPending}>
          練習を開始
        </Button>
      </div>
    </form>
  );
}
