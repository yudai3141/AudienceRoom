import createClient from "openapi-fetch";
import type { paths } from "./schema.gen";

const baseUrl =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = createClient<paths>({ baseUrl });
