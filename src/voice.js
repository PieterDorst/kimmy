// Voice session with an ElevenLabs Agent over WebRTC.
// The API key never reaches the browser: /api/token returns a short-lived conversation token.
import { Conversation } from "@elevenlabs/client";

export async function startVoice({ onModeChange, onInterruption, onStatus, onMessage, clientTools }) {
  const res = await fetch("/api/token");
  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data.token) throw new Error(data.error || `Could not get a voice token (HTTP ${res.status}). Is the /api/token server running?`);
  const { token } = data;

  return Conversation.startSession({
    conversationToken: token,
    connectionType: "webrtc",
    clientTools,
    onModeChange: ({ mode }) => onModeChange?.(mode),
    onInterruption: (e) => onInterruption?.(e),
    onStatusChange: ({ status }) => onStatus?.(status),
    onMessage: (m) => onMessage?.(m),
    onError: (msg, err) => console.error("[voice]", msg, err),
  });
}

// The SDK keeps an AnalyserNode on Kimmy's output audio; lip sync taps it.
export function outputAnalyser(conversation) {
  try { return conversation.output?.getAnalyser?.() || null; } catch { return null; }
}
