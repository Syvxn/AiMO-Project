"use client";

import { useEffect, useMemo, useState } from "react";
import { ProtectedRoute } from "@/components/protected-route";
import { useAuth } from "@/lib/auth-context";

const GAME_ENTRY_PATH = "/game/index.html";

type AssetStatus = "checking" | "available" | "missing" | "error";

function PlayContent() {
  const { email, role } = useAuth();
  const [assetStatus, setAssetStatus] = useState<AssetStatus>("checking");
  const [hasLaunched, setHasLaunched] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function checkGameAsset() {
      setAssetStatus("checking");
      try {
        const response = await fetch(GAME_ENTRY_PATH, {
          method: "HEAD",
          cache: "no-store",
        });

        if (!isMounted) {
          return;
        }

        setAssetStatus(response.ok ? "available" : "missing");
      } catch {
        if (isMounted) {
          setAssetStatus("error");
        }
      }
    }

    checkGameAsset();

    return () => {
      isMounted = false;
    };
  }, []);

  const statusMessage = useMemo(() => {
    if (assetStatus === "checking") {
      return "Checking for game web export...";
    }
    if (assetStatus === "available") {
      return "Game export detected. You can launch it in-page or in a new tab.";
    }
    if (assetStatus === "missing") {
      return "No game export found at /game/index.html yet.";
    }
    return "Could not verify game files. Confirm the web export exists under public/game/.";
  }, [assetStatus]);

  const canLaunch = assetStatus === "available";

  function openInNewTab() {
    window.open(GAME_ENTRY_PATH, "_blank", "noopener,noreferrer");
  }

  return (
    <section className="space-y-6">
      <h1 className="font-display text-4xl text-text-natural">Play</h1>
      <p className="max-w-3xl text-text-beige">
        Launch the Godot web client directly from the website. This page checks for a web export at
        <span className="mx-1 rounded bg-bg-darkest/50 px-2 py-1 text-text-natural">
          {GAME_ENTRY_PATH}
        </span>
        and provides quick launch controls.
      </p>

      <div className="card space-y-3">
        <h2 className="font-display text-2xl text-text-natural">Game Launcher</h2>
        <p className="text-text-beige">Signed in as {email ?? "unknown"} ({role ?? "unknown"})</p>
        <p className="text-text-beige">{statusMessage}</p>

        <div className="flex flex-wrap gap-3">
          <button
            className="btn-primary"
            type="button"
            onClick={() => setHasLaunched(true)}
            disabled={!canLaunch}
          >
            Launch In Page
          </button>
          <button className="btn-secondary" type="button" onClick={openInNewTab} disabled={!canLaunch}>
            Open In New Tab
          </button>
        </div>

        {!canLaunch && (
          <p className="text-sm text-accent-yellow">
            Add the Godot web export to apps/web/public/game with an index.html entry file.
          </p>
        )}
      </div>

      {hasLaunched && canLaunch && (
        <div className="card p-2">
          <iframe
            title="AiMO Game Web Client"
            src={GAME_ENTRY_PATH}
            className="h-[70vh] w-full rounded-xl border border-accent-teal/40 bg-black"
            allow="fullscreen; autoplay; clipboard-read; clipboard-write"
          />
        </div>
      )}

      <div className="card">
        <h3 className="font-display text-xl text-text-natural">Next Integration Step</h3>
        <p className="mt-2 text-text-beige">
          Once the game export loads reliably, we can add a token/session bridge so the game can
          receive the logged-in user context from the website.
        </p>
      </div>
    </section>
  );
}

export default function PlayPage() {
  return (
    <ProtectedRoute>
      <PlayContent />
    </ProtectedRoute>
  );
}
