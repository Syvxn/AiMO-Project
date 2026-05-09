from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.npc_chat import (
    ChatSession,
    resolve_profile,
    route_turn,
    stream_conversation_events,
    stream_task_events,
    trim_memory,
)

router = APIRouter(tags=["npc-chat"])


@router.websocket("/ws/npc-chat")
async def npc_chat_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    sessions: dict[str, ChatSession] = {}

    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                payload = json.loads(raw_message)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"type": "error", "message": "Invalid JSON payload."}
                )
                continue

            if payload.get("type") != "client_message":
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": "Unsupported message type. Use type=client_message.",
                    }
                )
                continue

            session_id = str(payload.get("session_id") or "").strip()
            user_text = str(payload.get("text") or "").strip()
            npc_id = str(payload.get("npc_id") or "quiz_llehc").strip()
            player_id = str(payload.get("player_id") or "unknown-player").strip()

            if not session_id:
                await websocket.send_json(
                    {"type": "error", "message": "Missing session_id."}
                )
                continue

            if not user_text:
                await websocket.send_json({"type": "error", "message": "Missing text."})
                continue

            session = sessions.get(session_id)
            if session is None:
                session = ChatSession(session_id=session_id, npc_id=npc_id)
                sessions[session_id] = session

            profile = resolve_profile(session.npc_id)
            session.memory.append({"role": "user", "text": user_text})
            session.memory = trim_memory(session.memory)

            route = route_turn(profile, user_text)
            if route == "task_quiz":
                session.mode = "task"
                await websocket.send_json(
                    {
                        "type": "mode_changed",
                        "mode": "task",
                        "npc_id": profile.npc_id,
                        "player_id": player_id,
                    }
                )

                async for event in stream_task_events(profile, user_text):
                    await websocket.send_json(event)

                session.mode = "conversation"
                await websocket.send_json(
                    {
                        "type": "mode_changed",
                        "mode": "conversation",
                        "npc_id": profile.npc_id,
                        "player_id": player_id,
                    }
                )
                continue

            session.mode = "conversation"
            await websocket.send_json(
                {
                    "type": "mode_changed",
                    "mode": "conversation",
                    "npc_id": profile.npc_id,
                    "player_id": player_id,
                }
            )

            assistant_buffer = ""
            async for event in stream_conversation_events(profile, user_text, session.memory):
                if event.get("type") == "typing_token":
                    assistant_buffer += str(event.get("text") or "")
                await websocket.send_json(event)

            if assistant_buffer:
                session.memory.append({"role": "assistant", "text": assistant_buffer})
                session.memory = trim_memory(session.memory)

    except WebSocketDisconnect:
        return
