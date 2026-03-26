import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema.gen";
import { useCurrentUser } from "@/features/auth/hooks/useCurrentUser";

export type SessionListItem = components["schemas"]["SessionListItem"];
export type PaginatedSessionListResponse =
  components["schemas"]["PaginatedSessionListResponse"];

type UseSessionsOptions = {
  limit?: number;
  offset?: number;
};

export function useSessions(options: UseSessionsOptions = {}) {
  const { limit = 20, offset = 0 } = options;
  const { data: user } = useCurrentUser();

  return useQuery({
    queryKey: ["sessions", user?.id, limit, offset],
    queryFn: async () => {
      if (!user) throw new Error("User not found");

      const { data, error } = await api.GET("/practice-sessions", {
        params: {
          query: {
            user_id: user.id,
            limit,
            offset,
          },
        },
      });

      if (error) {
        throw new Error("Failed to fetch sessions");
      }

      return data;
    },
    enabled: !!user,
  });
}
