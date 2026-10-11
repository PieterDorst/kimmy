// Voice session with an ElevenLabs Agent over WebRTC.
// The API key never reaches the browser: /api/token returns a short-lived conversation token.
import { Conversation } from "@elevenlabs/client";

export async function startVoice({ onModeChange, onInterruption, onStatus, onMessage, clientTools }) {
  const data = await fetchToken();
  if (!data.token) throw new Error(data.error || "Could not get a voice token. Is the /api/token server running?");
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

// Asks for the password once when the server is locked, then remembers it on this device.
async function fetchToken() {
  let password = "";
  try { password = localStorage.getItem("kimmy-password") || ""; } catch {}
  for (let attempt = 0; attempt < 3; attempt++) {
    const res = await fetch("/api/token", { headers: { "x-kimmy-password": password } });
    const data = await res.json().catch(() => ({}));
    if (res.status !== 401) return res.ok ? data : { error: data.error || `HTTP ${res.status}` };
    password = prompt(attempt ? "Dat wachtwoord klopt niet. Probeer opnieuw:" : "Wachtwoord voor Kimmy:") || "";
    if (!password) break;
    try { localStorage.setItem("kimmy-password", password); } catch {}
  }
  return { error: "Kimmy is vergrendeld met een wachtwoord." };
}

// The SDK keeps an AnalyserNode on Kimmy's output audio; lip sync taps it.
export function outputAnalyser(conversation) {
  try { return conversation.output?.getAnalyser?.() || null; } catch { return null; }
}
