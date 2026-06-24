import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema.gen";

export type TopicCreateRequest =
  components["schemas"]["TopicCreateRequest"];
export type TopicResponse = components["schemas"]["TopicResponse"];

/** 新しいトピックを作成する。 */
export function useCreateTopic() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: TopicCreateRequest) => {
      const { data: response, error } = await api.POST("/topics", {
        body: data,
      });
      if (error) {
        throw new Error("Failed to create topic");
      }
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["topics"] });
    },
  });
}
