import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";

export function useGenerateFeedback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (sessionId: number) => {
      const { data, error } = await api.POST(
        "/practice-sessions/{session_id}/generate-feedback",
        {
          params: {
            path: { session_id: sessionId },
          },
        },
      );

      if (error) {
        throw new Error("フィードバックの生成に失敗しました");
      }

      return data;
    },
    onSuccess: (_, sessionId) => {
      queryClient.invalidateQueries({
        queryKey: ["session-detail", sessionId],
      });
    },
  });
}
