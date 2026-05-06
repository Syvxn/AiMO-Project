const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

export interface AuthResponse {
  access_token: string;
  token_type: string;
  role: string;
}

export type UserRole = "admin" | "teacher" | "student";

export interface AdminUser {
  id: number;
  email: string;
  role: UserRole;
  created_at: string;
}

export interface AdminStats {
  total_users: number;
  admins: number;
  teachers: number;
  students: number;
}

export interface DeleteUserResponse {
  status: string;
  message: string;
}

function authHeaders(token: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export async function registerUser(
  email: string,
  password: string,
  role: "student" | "teacher",
): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, role }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Registration failed");
  }

  return res.json();
}

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Login failed");
  }

  return res.json();
}

export async function getAdminUsers(token: string): Promise<AdminUser[]> {
  const res = await fetch(`${API_BASE}/admin/users`, {
    method: "GET",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to load users");
  }

  return res.json();
}

export async function getAdminStats(token: string): Promise<AdminStats> {
  const res = await fetch(`${API_BASE}/admin/stats`, {
    method: "GET",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to load admin stats");
  }

  return res.json();
}

export async function updateAdminUserRole(
  token: string,
  userId: number,
  role: UserRole,
): Promise<AdminUser> {
  const res = await fetch(`${API_BASE}/admin/users/${userId}/role`, {
    method: "PATCH",
    headers: authHeaders(token),
    body: JSON.stringify({ role }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to update user role");
  }

  return res.json();
}

export async function createAdminUser(
  token: string,
  email: string,
  password: string,
  role: UserRole,
): Promise<AdminUser> {
  const res = await fetch(`${API_BASE}/admin/users`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ email, password, role }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to create user");
  }

  return res.json();
}

export async function deleteAdminUser(token: string, userId: number): Promise<DeleteUserResponse> {
  const res = await fetch(`${API_BASE}/admin/users/${userId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to delete user");
  }

  return res.json();
}
