import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema.gen";

export type UserResponse = components["schemas"]["UserResponse"];

export async function loginToBackend(
  displayName?: string | null,
  photoUrl?: string | null,
): Promise<UserResponse> {
  const { data, error } = await api.POST("/auth/login", {
    body: {
      display_name: displayName,
      photo_url: photoUrl,
    },
  });

  if (error) {
    throw new Error("ログインに失敗しました");
  }

  return data;
}
