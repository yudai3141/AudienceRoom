import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema.gen";

export type PracticeSessionDetailResponse =
  components["schemas"]["PracticeSessionDetailResponse"];
export type SessionFeedbackNested =
  components["schemas"]["SessionFeedbackNested"];
export type FeedbackMetricResponse =
  components["schemas"]["FeedbackMetricResponse"];

export function useSessionDetail(sessionId: number) {
  return useQuery({
    queryKey: ["session-detail", sessionId],
    queryFn: async () => {
      const { data, error } = await api.GET(
        "/practice-sessions/{session_id}/detail",
        {
          params: {
            path: { session_id: sessionId },
          },
        },
      );

      if (error) {
        throw new Error("Failed to fetch session detail");
      }

      return data;
    },
    enabled: sessionId > 0,
  });
}
