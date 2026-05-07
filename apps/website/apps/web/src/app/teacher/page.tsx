"use client";

import { useEffect, useMemo, useState } from "react";
import { ProtectedRoute } from "@/components/protected-route";
import { useAuth } from "@/lib/auth-context";
import {
  deleteTeacherMaterial,
  getTeacherMaterials,
  TeacherMaterial,
  teacherChat,
  uploadTeacherMaterial,
} from "@/lib/api";

type ChatMessage = {
  id: number;
  role: "teacher" | "assistant";
  text: string;
};

function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function TeacherPanelContent() {
  const { token } = useAuth();

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      role: "assistant",
      text: "Analytics assistant stub ready. This will later summarize student progress, quiz outcomes, and classroom trends.",
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [isSending, setIsSending] = useState(false);

  const [materials, setMaterials] = useState<TeacherMaterial[]>([]);
  const [description, setDescription] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingMaterialId, setDeletingMaterialId] = useState<number | null>(null);

  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    async function load() {
      if (!token) return;
      try {
        const response = await getTeacherMaterials(token);
        setMaterials(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load study materials");
      }
    }

    load();
  }, [token]);

  const sortedMaterials = useMemo(
    () => [...materials].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()),
    [materials],
  );

  async function handleSendChat(event: React.FormEvent) {
    event.preventDefault();
    if (!token || !chatInput.trim()) {
      return;
    }

    setIsSending(true);
    setError("");
    setNotice("");

    const userMessage: ChatMessage = {
      id: Date.now(),
      role: "teacher",
      text: chatInput.trim(),
    };

    setMessages((previous) => [...previous, userMessage]);
    setChatInput("");

    try {
      const response = await teacherChat(token, userMessage.text);
      const assistantMessage: ChatMessage = {
        id: Date.now() + 1,
        role: "assistant",
        text: response.reply,
      };
      setMessages((previous) => [...previous, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
    } finally {
      setIsSending(false);
    }
  }

  async function handleUpload(event: React.FormEvent) {
    event.preventDefault();
    if (!token) return;
    if (!selectedFile) {
      setError("Please choose a .txt file first");
      return;
    }

    setIsUploading(true);
    setError("");
    setNotice("");

    try {
      const uploaded = await uploadTeacherMaterial(token, selectedFile, description);
      setMaterials((previous) => [uploaded, ...previous]);
      setSelectedFile(null);
      setDescription("");
      setNotice(`Uploaded ${uploaded.original_filename}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDeleteMaterial(material: TeacherMaterial) {
    if (!token) {
      return;
    }

    const confirmed = window.confirm(`Delete ${material.original_filename}? This cannot be undone.`);
    if (!confirmed) {
      return;
    }

    setDeletingMaterialId(material.id);
    setError("");
    setNotice("");

    try {
      const response = await deleteTeacherMaterial(token, material.id);
      setMaterials((previous) => previous.filter((item) => item.id !== material.id));
      setNotice(response.message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete material");
    } finally {
      setDeletingMaterialId(null);
    }
  }

  return (
    <section className="space-y-6">
      <h1 className="font-display text-4xl text-text-natural">Teacher Panel</h1>

      {error && <div className="card border-accent-orange/40 text-accent-yellow">{error}</div>}
      {notice && <div className="card border-accent-teal/40 text-accent-green">{notice}</div>}

      <div className="grid gap-6 lg:grid-cols-2">
        <article className="card space-y-4">
          <h2 className="font-display text-2xl text-text-natural">Analytics Assistant</h2>
          <p className="text-sm text-text-beige">
            Use this chat to review student progress, performance trends, and analytics summaries.
          </p>

          <div className="max-h-80 space-y-3 overflow-y-auto rounded-md border border-accent-orange/30 p-3">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`rounded-md px-3 py-2 text-sm ${
                  message.role === "teacher"
                    ? "bg-accent-orange/20 text-text-natural"
                    : "bg-accent-teal/20 text-text-beige"
                }`}
              >
                <p className="mb-1 text-xs uppercase tracking-wide opacity-80">{message.role}</p>
                <p>{message.text}</p>
              </div>
            ))}
          </div>

          <form className="space-y-3" onSubmit={handleSendChat}>
            <textarea
              value={chatInput}
              onChange={(event) => setChatInput(event.target.value)}
              placeholder="Ask for an analytics summary, e.g. Show recent student progress trends"
              className="w-full rounded-md border border-accent-orange/30 px-3 py-2"
              rows={3}
            />
            <button className="btn-primary" type="submit" disabled={isSending}>
              {isSending ? "Sending..." : "Send"}
            </button>
          </form>
        </article>

        <article className="card space-y-4">
          <h2 className="font-display text-2xl text-text-natural">Study Materials</h2>
          <p className="text-sm text-text-beige">
            Upload TXT materials for later analytics and agent processing. Files are stored first and processed later.
          </p>

          <form className="space-y-3" onSubmit={handleUpload}>
            <input
              type="file"
              accept=".txt,text/plain"
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
              className="w-full rounded-md border border-accent-orange/30 px-3 py-2"
            />
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Optional note about this material"
              className="w-full rounded-md border border-accent-orange/30 px-3 py-2"
              rows={2}
            />
            <button className="btn-primary" type="submit" disabled={isUploading}>
              {isUploading ? "Uploading..." : "Upload Material"}
            </button>
          </form>

          <div className="space-y-2">
            <h3 className="font-display text-xl text-text-natural">Uploaded Files</h3>
            {sortedMaterials.length === 0 ? (
              <p className="text-sm text-text-beige">No materials uploaded yet.</p>
            ) : (
              <ul className="space-y-2">
                {sortedMaterials.map((item) => (
                  <li key={item.id} className="rounded-md border border-accent-orange/20 px-3 py-2">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm text-text-natural">{item.original_filename}</p>
                      <button
                        type="button"
                        onClick={() => handleDeleteMaterial(item)}
                        disabled={deletingMaterialId === item.id}
                        className="rounded-md border border-accent-orange/40 px-2 py-1 text-xs text-accent-yellow hover:bg-accent-orange/20 disabled:opacity-50"
                      >
                        {deletingMaterialId === item.id ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                    {item.description && (
                      <p className="mt-1 text-xs text-text-beige">{item.description}</p>
                    )}
                    <p className="text-xs text-text-beige">
                      {formatBytes(item.size_bytes)} · uploaded {new Date(item.created_at).toLocaleString()}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </article>
      </div>
    </section>
  );
}

export default function TeacherPage() {
  return (
    <ProtectedRoute requiredRoles={["teacher", "admin"]}>
      <TeacherPanelContent />
    </ProtectedRoute>
  );
}
