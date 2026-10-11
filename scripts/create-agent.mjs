// Creates (or updates) the Kimmy agent in ElevenLabs from src/kimmy.js.
// Usage: npm run create-agent   (reads ELEVENLABS_API_KEY from .env)
//        (set ELEVENLABS_AGENT_ID to update an existing agent instead of creating one)
import { readFileSync, writeFileSync } from "node:fs";
import { PERSONA, FIRST_MESSAGE, CLIENT_TOOLS } from "../src/kimmy.js";

const key = process.env.ELEVENLABS_API_KEY;
if (!key) { console.error("No ElevenLabs key found. Open the .env file and paste your key right after ELEVENLABS_API_KEY= (no spaces), then save."); process.exit(1); }

const agentId = process.env.ELEVENLABS_AGENT_ID;
const config = {
  name: "Kimmy",
  conversation_config: {
    agent: {
      first_message: FIRST_MESSAGE,
      language: "en",
      prompt: {
        prompt: PERSONA,
        llm: process.env.KIMMY_LLM || "claude-haiku-4-5",
        tools: CLIENT_TOOLS,
      },
    },
    tts: {
      // Stock young female voice until Kimmy's own voice is designed.
      voice_id: process.env.KIMMY_VOICE_ID || "cgSgspJ2msm6clMCkdW9",
      model_id: "eleven_flash_v2_5",
    },
    turn: {
      turn_eagerness: "eager",
      speculative_turn: true,
    },
    conversation: {
      client_events: ["audio", "interruption", "agent_response", "user_transcript", "client_tool_call", "vad_score"],
    },
  },
};

const url = agentId
  ? `https://api.elevenlabs.io/v1/convai/agents/${agentId}`
  : "https://api.elevenlabs.io/v1/convai/agents/create";
const res = await fetch(url, {
  method: agentId ? "PATCH" : "POST",
  headers: { "xi-api-key": key, "Content-Type": "application/json" },
  body: JSON.stringify(config),
});
const body = await res.json().catch(() => ({}));
if (!res.ok) { console.error(res.status, JSON.stringify(body, null, 2)); process.exit(1); }
if (agentId) {
  console.log(`Updated agent ${agentId}`);
} else {
  // Save the new agent id into .env so the app can find it.
  const env = readFileSync(".env", "utf8");
  const line = `ELEVENLABS_AGENT_ID=${body.agent_id}`;
  writeFileSync(".env", /^ELEVENLABS_AGENT_ID=.*$/m.test(env) ? env.replace(/^ELEVENLABS_AGENT_ID=.*$/m, line) : `${env.trimEnd()}\n${line}\n`);
  console.log(`Created Kimmy (${body.agent_id}) and saved the id in .env`);
}
