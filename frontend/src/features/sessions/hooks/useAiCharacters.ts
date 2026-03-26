import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema.gen";

export type AiCharacter = components["schemas"]["AiCharacterResponse"];

export function useAiCharacters() {
  return useQuery({
    queryKey: ["ai-characters"],
    queryFn: async () => {
      const { data, error } = await api.GET("/ai-characters");
      if (error) {
        throw new Error("Failed to fetch AI characters");
      }
      return data;
    },
  });
}
