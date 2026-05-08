"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ProtectedRoute } from "@/components/protected-route";
import {
  AdminStats,
  AdminUser,
  createAdminUser,
  deleteAdminUser,
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
  const [notice, setNotice] = useState("");
  const [savingUserId, setSavingUserId] = useState<number | null>(null);
  const [deletingUserId, setDeletingUserId] = useState<number | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState<UserRole>("student");

  const loadAdminData = useCallback(
    async (showLoading: boolean = true) => {
      if (!token) {
        return;
      }

      if (showLoading) {
        setIsLoading(true);
      }

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
        if (showLoading) {
          setIsLoading(false);
        }
      }
    },
    [token],
  );

  useEffect(() => {
    async function load() {
      setError("");
      await loadAdminData(true);
    }

    load();
  }, [loadAdminData]);

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
    setNotice("");

    try {
      const updatedUser = await updateAdminUserRole(token, userId, role);
      setUsers((previous) =>
        previous.map((user) => (user.id === updatedUser.id ? updatedUser : user)),
      );
      await loadAdminData(false);
      setNotice(`Updated role for ${updatedUser.email}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update user role");
    } finally {
      setSavingUserId(null);
    }
  }

  async function handleCreateUser(event: React.FormEvent) {
    event.preventDefault();
    if (!token) {
      return;
    }

    setIsCreating(true);
    setError("");
    setNotice("");

    try {
      const created = await createAdminUser(token, newEmail, newPassword, newRole);
      setNewEmail("");
      setNewPassword("");
      setNewRole("student");
      await loadAdminData(false);
      setNotice(`Created ${created.role} account: ${created.email}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create user");
    } finally {
      setIsCreating(false);
    }
  }

  async function handleDeleteUser(user: AdminUser) {
    if (!token) {
      return;
    }

    const confirmed = window.confirm(`Delete user ${user.email}? This cannot be undone.`);
    if (!confirmed) {
      return;
    }

    setDeletingUserId(user.id);
    setError("");
    setNotice("");

    try {
      const response = await deleteAdminUser(token, user.id);
      await loadAdminData(false);
      setNotice(response.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete user");
    } finally {
      setDeletingUserId(null);
    }
  }

  if (isLoading) {
    return <section className="py-12 text-text-beige">Loading admin data...</section>;
  }

  return (
    <section className="space-y-6">
      <h1 className="font-display text-4xl text-text-natural">Admin Console</h1>

      {error && <div className="card border-accent-orange/40 text-accent-yellow">{error}</div>}
      {notice && <div className="card border-accent-teal/40 text-accent-green">{notice}</div>}

      <form className="card space-y-4" onSubmit={handleCreateUser}>
        <h2 className="font-display text-2xl text-text-natural">Add User</h2>
        <p className="text-sm text-text-beige">
          Admin-only account creation. Admin accounts can only be created from this console.
        </p>
        <div className="grid gap-4 md:grid-cols-3">
          <input
            type="email"
            placeholder="Email"
            value={newEmail}
            onChange={(event) => setNewEmail(event.target.value)}
            className="w-full rounded-md border border-accent-orange/30 px-3 py-2"
            required
          />
          <input
            type="password"
            placeholder="Password (min 8)"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            className="w-full rounded-md border border-accent-orange/30 px-3 py-2"
            minLength={8}
            required
          />
          <select
            value={newRole}
            onChange={(event) => setNewRole(event.target.value as UserRole)}
            className="w-full rounded-md border border-accent-orange/30 px-3 py-2"
          >
            {ROLE_OPTIONS.map((roleOption) => (
              <option key={roleOption} value={roleOption}>
                {roleOption}
              </option>
            ))}
          </select>
        </div>
        <button className="btn-primary" type="submit" disabled={isCreating}>
          {isCreating ? "Creating..." : "Create User"}
        </button>
      </form>

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
        <table className="w-full min-w-[880px] text-left text-sm">
          <thead>
            <tr className="border-b border-accent-orange/30 text-text-beige">
              <th className="px-3 py-2">Email</th>
              <th className="px-3 py-2">Account ID</th>
              <th className="px-3 py-2">Role</th>
              <th className="px-3 py-2">Created</th>
              <th className="px-3 py-2">Update</th>
              <th className="px-3 py-2">Delete</th>
            </tr>
          </thead>
          <tbody>
            {sortedUsers.map((user) => (
              <tr key={user.id} className="border-b border-accent-orange/15">
                <td className="px-3 py-2 text-text-natural">{user.email}</td>
                <td className="px-3 py-2 font-mono text-xs text-text-beige">{user.user_id}</td>
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
                <td className="px-3 py-2">
                  <button
                    type="button"
                    onClick={() => handleDeleteUser(user)}
                    disabled={deletingUserId === user.id}
                    className="rounded-md border border-accent-orange/40 px-3 py-1 text-xs text-accent-yellow hover:bg-accent-orange/20 disabled:opacity-50"
                  >
                    {deletingUserId === user.id ? "Deleting..." : "Delete"}
                  </button>
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
