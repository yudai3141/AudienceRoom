import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema.gen";

export type Topic = components["schemas"]["TopicResponse"];

/** ユーザーのトピック一覧を取得する。 */
export function useTopics(userId: number | undefined) {
  return useQuery({
    queryKey: ["topics", userId],
    enabled: userId != null,
    queryFn: async () => {
      const { data, error } = await api.GET("/topics", {
        params: { query: { user_id: userId! } },
      });
      if (error) {
        throw new Error("Failed to fetch topics");
      }
      return data;
    },
  });
}
