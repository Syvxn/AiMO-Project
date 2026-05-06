"use client";

import { useEffect, useMemo, useState } from "react";
import { ProtectedRoute } from "@/components/protected-route";
import {
  AdminStats,
  AdminUser,
  getAdminStats,
  getAdminUsers,
  updateAdminUserRole,
  UserRole,
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const ROLE_OPTIONS: UserRole[] = ["student", "teacher", "admin"];

function AdminContent() {
  const { token } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [savingUserId, setSavingUserId] = useState<number | null>(null);

  useEffect(() => {
    async function loadAdminData() {
      if (!token) {
        return;
      }

      setIsLoading(true);
      setError("");

      try {
        const [usersResponse, statsResponse] = await Promise.all([
          getAdminUsers(token),
          getAdminStats(token),
        ]);
        setUsers(usersResponse);
        setStats(statsResponse);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load admin data");
      } finally {
        setIsLoading(false);
      }
    }

    loadAdminData();
  }, [token]);

  const sortedUsers = useMemo(
    () => [...users].sort((a, b) => a.email.localeCompare(b.email)),
    [users],
  );

  async function handleRoleChange(userId: number, role: UserRole) {
    if (!token) {
      return;
    }

    setSavingUserId(userId);
    setError("");

    try {
      const updatedUser = await updateAdminUserRole(token, userId, role);
      setUsers((previous) =>
        previous.map((user) => (user.id === updatedUser.id ? updatedUser : user)),
      );

      const refreshedStats = await getAdminStats(token);
      setStats(refreshedStats);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update user role");
    } finally {
      setSavingUserId(null);
    }
  }

  if (isLoading) {
    return <section className="py-12 text-text-beige">Loading admin data...</section>;
  }

  return (
    <section className="space-y-6">
      <h1 className="font-display text-4xl text-text-natural">Admin Console</h1>

      {error && <div className="card border-accent-orange/40 text-accent-yellow">{error}</div>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <article className="card">
          <h2 className="font-display text-xl text-text-natural">Total Users</h2>
          <p className="mt-2 text-3xl text-accent-yellow">{stats?.total_users ?? 0}</p>
        </article>
        <article className="card">
          <h2 className="font-display text-xl text-text-natural">Admins</h2>
          <p className="mt-2 text-3xl text-accent-light">{stats?.admins ?? 0}</p>
        </article>
        <article className="card">
          <h2 className="font-display text-xl text-text-natural">Teachers</h2>
          <p className="mt-2 text-3xl text-accent-teal">{stats?.teachers ?? 0}</p>
        </article>
        <article className="card">
          <h2 className="font-display text-xl text-text-natural">Students</h2>
          <p className="mt-2 text-3xl text-accent-green">{stats?.students ?? 0}</p>
        </article>
      </div>

      <div className="card overflow-x-auto">
        <h2 className="mb-4 font-display text-2xl text-text-natural">User Management</h2>
        <table className="w-full min-w-[680px] text-left text-sm">
          <thead>
            <tr className="border-b border-accent-orange/30 text-text-beige">
              <th className="px-3 py-2">Email</th>
              <th className="px-3 py-2">Role</th>
              <th className="px-3 py-2">Created</th>
              <th className="px-3 py-2">Update</th>
            </tr>
          </thead>
          <tbody>
            {sortedUsers.map((user) => (
              <tr key={user.id} className="border-b border-accent-orange/15">
                <td className="px-3 py-2 text-text-natural">{user.email}</td>
                <td className="px-3 py-2">
                  <select
                    value={user.role}
                    onChange={(event) => handleRoleChange(user.id, event.target.value as UserRole)}
                    disabled={savingUserId === user.id}
                    className="rounded-md border border-accent-orange/30 bg-bg-darkest/60 px-2 py-1 text-text-natural"
                  >
                    {ROLE_OPTIONS.map((roleOption) => (
                      <option key={roleOption} value={roleOption}>
                        {roleOption}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="px-3 py-2 text-text-beige">
                  {new Date(user.created_at).toLocaleString()}
                </td>
                <td className="px-3 py-2 text-text-beige">
                  {savingUserId === user.id ? "Saving..." : "Ready"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default function AdminPage() {
  return (
    <ProtectedRoute requiredRole="admin">
      <AdminContent />
    </ProtectedRoute>
  );
}
