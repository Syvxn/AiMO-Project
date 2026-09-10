const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

export interface AuthResponse {
  user_id: string;
  access_token: string;
  token_type: string;
  role: UserRole;
}

export type UserRole = "admin" | "teacher" | "student";

export interface AdminUser {
  id: number;
  user_id: string;
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

export interface TeacherChatResponse {
  reply: string;
  status: string;
}

export interface TeacherMaterial {
  id: number;
  original_filename: string;
  description: string;
  content_type: string;
  size_bytes: number;
  uploaded_by_user_id: number;
  created_at: string;
}

export interface TeacherDeleteMaterialResponse {
  status: string;
  message: string;
}

export interface TeacherMaterialPreview {
  id: number;
  original_filename: string;
  content: string;
}

export interface TeacherQuizQuestion {
  question: string;
  options: string[];
  answer: string;
}

export interface TeacherQuiz {
  quiz_title: string;
  questions: TeacherQuizQuestion[];
}

function authHeaders(token: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

function authOnlyHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
  };
}

async function readErrorMessage(response: Response, fallbackMessage: string): Promise<string> {
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    const error = await response.json();
    return error.detail || fallbackMessage;
  }

  const text = await response.text();
  return text.trim() || fallbackMessage;
}

async function readJsonResponse<T>(response: Response, fallbackMessage: string): Promise<T> {
  const contentType = response.headers.get("content-type") || "";

  if (!response.ok) {
    throw new Error(await readErrorMessage(response, fallbackMessage));
  }

  if (!contentType.includes("application/json")) {
    throw new Error(fallbackMessage);
  }

  return response.json() as Promise<T>;
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

  return readJsonResponse<AuthResponse>(res, "Registration failed");
}

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  return readJsonResponse<AuthResponse>(res, "Login failed");
}

export async function getAdminUsers(token: string): Promise<AdminUser[]> {
  const res = await fetch(`${API_BASE}/admin/users`, {
    method: "GET",
    headers: authHeaders(token),
  });

  return readJsonResponse<AdminUser[]>(res, "Failed to load users");
}

export async function getAdminStats(token: string): Promise<AdminStats> {
  const res = await fetch(`${API_BASE}/admin/stats`, {
    method: "GET",
    headers: authHeaders(token),
  });

  return readJsonResponse<AdminStats>(res, "Failed to load admin stats");
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

  return readJsonResponse<AdminUser>(res, "Failed to update user role");
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

  return readJsonResponse<AdminUser>(res, "Failed to create user");
}

export async function deleteAdminUser(token: string, userId: number): Promise<DeleteUserResponse> {
  const res = await fetch(`${API_BASE}/admin/users/${userId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });

  return readJsonResponse<DeleteUserResponse>(res, "Failed to delete user");
}

export async function teacherChat(token: string, message: string): Promise<TeacherChatResponse> {
  const res = await fetch(`${API_BASE}/teacher/chat`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ message }),
  });

  return readJsonResponse<TeacherChatResponse>(res, "Teacher chat failed");
}

export async function uploadTeacherMaterial(
  token: string,
  file: File,
  description: string,
): Promise<TeacherMaterial> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("description", description);

  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 120_000);

  try {
    const res = await fetch(`${API_BASE}/teacher/materials/upload`, {
      method: "POST",
      headers: authOnlyHeaders(token),
      body: formData,
      signal: controller.signal,
    });

    return await readJsonResponse<TeacherMaterial>(res, "Upload failed");
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("Upload timed out. The file may have been saved; refresh the material list before retrying.");
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

export async function getTeacherMaterials(token: string): Promise<TeacherMaterial[]> {
  const res = await fetch(`${API_BASE}/teacher/materials`, {
    method: "GET",
    headers: authOnlyHeaders(token),
  });

  return readJsonResponse<TeacherMaterial[]>(res, "Failed to load materials");
}

export async function deleteTeacherMaterial(
  token: string,
  materialId: number,
): Promise<TeacherDeleteMaterialResponse> {
  const res = await fetch(`${API_BASE}/teacher/materials/${materialId}`, {
    method: "DELETE",
    headers: authOnlyHeaders(token),
  });

  return readJsonResponse<TeacherDeleteMaterialResponse>(res, "Failed to delete material");
}

export async function previewTeacherMaterial(
  token: string,
  materialId: number,
): Promise<TeacherMaterialPreview> {
  const res = await fetch(`${API_BASE}/teacher/materials/${materialId}/preview`, {
    method: "GET",
    headers: authOnlyHeaders(token),
  });

  return readJsonResponse<TeacherMaterialPreview>(res, "Failed to preview material");
}

export async function getTeacherMaterialFile(token: string, materialId: number): Promise<Blob> {
  const res = await fetch(`${API_BASE}/teacher/materials/${materialId}/file`, {
    method: "GET",
    headers: authOnlyHeaders(token),
  });

  if (!res.ok) {
    throw new Error(await readErrorMessage(res, "Failed to open material"));
  }
  return res.blob();
}

export async function generateTeacherQuiz(
  token: string,
  topic: string,
  questionCount: number,
): Promise<{ quiz: TeacherQuiz }> {
  const res = await fetch(`${API_BASE}/teacher/quiz/generate`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ topic, question_count: questionCount }),
  });

  return readJsonResponse<{ quiz: TeacherQuiz }>(res, "Quiz generation failed");
}
