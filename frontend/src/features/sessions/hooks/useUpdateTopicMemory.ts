import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema.gen";

export type TopicUpdateResult = components["schemas"]["TopicUpdateResponse"];

/** 練習後にトピックグラフ・完成度・要約をまとめて更新する。 */
export function useUpdateTopicMemory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (sessionId: number) => {
      const { data, error } = await api.POST(
        "/practice-sessions/{session_id}/update-topic",
        { params: { path: { session_id: sessionId } } },
      );
      if (error) {
        throw new Error("トピックの更新に失敗しました");
      }
      return data;
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["topics"] });
      if (result?.topic_id != null) {
        queryClient.invalidateQueries({ queryKey: ["topic", result.topic_id] });
      }
    },
  });
}
