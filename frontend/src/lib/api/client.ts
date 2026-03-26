import createClient, { type Middleware } from "openapi-fetch";
import type { paths } from "./schema.gen";

const baseUrl =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

let tokenGetter: (() => Promise<string | null>) | null = null;

export function setTokenGetter(getter: () => Promise<string | null>) {
  tokenGetter = getter;
}

const authMiddleware: Middleware = {
  async onRequest({ request }) {
    if (tokenGetter) {
      const token = await tokenGetter();
      if (token) {
        request.headers.set("Authorization", `Bearer ${token}`);
      }
    }
    return request;
  },
};

export const api = createClient<paths>({ baseUrl });
api.use(authMiddleware);
