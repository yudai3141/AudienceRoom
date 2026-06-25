import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema.gen";

export type TopicDetail = components["schemas"]["TopicDetailResponse"];
export type TopicNode = components["schemas"]["TopicNodeResponse"];
export type TopicEdge = components["schemas"]["TopicEdgeResponse"];

/** トピック詳細（nodes / edges 込み）を取得する。 */
export function useTopicDetail(topicId: number | undefined) {
  return useQuery({
    queryKey: ["topic", topicId],
    enabled: topicId != null,
    queryFn: async () => {
      const { data, error } = await api.GET("/topics/{topic_id}", {
        params: { path: { topic_id: topicId! } },
      });
      if (error) {
        throw new Error("Failed to fetch topic");
      }
      return data;
    },
  });
}
