import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema.gen";
import { useAuth } from "./useAuth";

export type UserResponse = components["schemas"]["UserResponse"];

export function useCurrentUser() {
  const { user, loading } = useAuth();

  return useQuery({
    queryKey: ["currentUser"],
    queryFn: async () => {
      const { data, error } = await api.GET("/users/me");
      if (error) {
        throw new Error("Failed to fetch current user");
      }
      return data;
    },
    enabled: !loading && !!user,
    retry: 2,
    staleTime: 1000 * 60 * 5,
  });
}
