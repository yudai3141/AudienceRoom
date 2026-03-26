import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema.gen";

export type DashboardResponse = components["schemas"]["DashboardResponse"];
export type SessionListItem = components["schemas"]["SessionListItem"];

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: async (): Promise<DashboardResponse> => {
      const { data, error } = await api.GET("/users/me/dashboard");
      if (error) {
        throw new Error("ダッシュボードの取得に失敗しました");
      }
      return data;
    },
  });
}
