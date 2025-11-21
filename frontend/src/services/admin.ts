import { apiFetch } from "./api";
import type { User } from "../types"; // Import User type

export async function getPendingUsers(): Promise<User[]> {
  return apiFetch<User[]>("/admin/pending-users");
}

export async function approveUser(userId: number): Promise<User> {
  return apiFetch<User>(`/admin/approve-user/${userId}`, {
    method: "POST",
  });
}
