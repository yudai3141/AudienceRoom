import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";

type UpdateStatusParams = {
  sessionId: number;
  status: "in_progress" | "completed" | "cancelled";
};

export function useUpdateSessionStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ sessionId, status }: UpdateStatusParams) => {
      const { data, error } = await api.PATCH(
        "/practice-sessions/{session_id}/status",
        {
          params: {
            path: { session_id: sessionId },
          },
          body: {
            status,
          },
        },
      );

      if (error) {
        throw new Error("セッションステータスの更新に失敗しました");
      }

      return data;
    },
    onSuccess: (_, { sessionId }) => {
      queryClient.invalidateQueries({
        queryKey: ["session-detail", sessionId],
      });
    },
  });
}
