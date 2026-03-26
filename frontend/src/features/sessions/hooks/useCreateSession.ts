import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema.gen";

export type PracticeSessionCreateRequest =
  components["schemas"]["PracticeSessionCreateRequest"];
export type PracticeSessionResponse =
  components["schemas"]["PracticeSessionResponse"];

export function useCreateSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: PracticeSessionCreateRequest) => {
      const { data: response, error } = await api.POST("/practice-sessions", {
        body: data,
      });
      if (error) {
        throw new Error("Failed to create session");
      }
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
    },
  });
}
