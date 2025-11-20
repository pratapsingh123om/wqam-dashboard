import { apiFetch } from "./api";

export async function login(username: string, password: string) {
  return apiFetch<{
    access_token: string;
    token_type: string;
    role: string;
  }>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}
