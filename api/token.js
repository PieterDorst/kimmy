// Serverless function (Vercel style): exchanges the server-side API key for a
// short-lived WebRTC conversation token, so the key never reaches the browser.
// Also used by the Vite dev server (see vite.config.js).

export async function getConversationToken(env = process.env) {
  const key = env.ELEVENLABS_API_KEY;
  const agentId = env.ELEVENLABS_AGENT_ID;
  if (!key || !agentId) {
    return { status: 500, body: { error: "Set ELEVENLABS_API_KEY and ELEVENLABS_AGENT_ID on the server." } };
  }
  const url = `https://api.elevenlabs.io/v1/convai/conversation/token?agent_id=${encodeURIComponent(agentId)}`;
  const res = await fetch(url, { headers: { "xi-api-key": key } });
  if (!res.ok) return { status: 502, body: { error: `ElevenLabs returned ${res.status}` } };
  const { token } = await res.json();
  return { status: 200, body: { token } };
}

export default async function handler(req, res) {
  const { status, body } = await getConversationToken();
  res.setHeader("Cache-Control", "no-store");
  res.status(status).json(body);
}
