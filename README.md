# Kimmy

Kimmy is a 3D AI sparring partner who talks back fast, in voice and in body language.

This is prototype **P0**: a web page where you talk to a 3D character. She answers in Kimmy's personality, her mouth follows her voice, and on-screen numbers show how fast she responds. It runs in desktop and mobile browsers.

## How it works

| Part | What it does |
|---|---|
| **ElevenLabs Agents** (WebRTC) | Speech recognition, the LLM, turn-taking, barge-in, and Kimmy's voice (Flash v2), all in one session |
| `api/token.js` | Swaps the server-side API key for a short-lived conversation token, so the key never reaches the browser |
| **TalkingHead** (Three.js) | Renders the avatar, with idle motion, blinking, eye contact, moods and hand gestures |
| **HeadAudio** | Audio-driven lip sync: reads Kimmy's output audio in the browser and drives the Oculus viseme blendshapes |
| `src/behavior.js` | A client-side state machine (`listening → thinking → speaking`), so she reacts the moment you stop talking without waiting for the server. It also measures latency. |
| `src/kimmy.js` | Persona prompt plus the `set_mood` / `gesture` client tools. It's the single source for both the app and the agent setup script. |

The avatar is `public/kimmy.glb`, built from Pieter's Tripo model by `scripts/rig/build.py`: it adds a Mixamo-style skeleton (axes copied from TalkingHead's `avatars/brunette-t.glb`), skin weights, a lip cut with a mouth interior, and procedural ARKit + Oculus viseme blendshapes. Her eyes are painted, so blinks squash the eye and gaze doesn't move the pupils. Rebuild with `python3 scripts/rig/build.py <tripo.glb> public/kimmy.glb kimmy2` (needs numpy, put TalkingHead's `brunette-t.glb` next to the script). The last argument picks the measured joint and face profile: `kimmy2` (current T-pose model, `models/Kimmy2.glb`) or `kimmy1` (first A-pose model). Tripo's own rig in Kimmy2.glb is not used: its bones have no rest pose and every vertex is weighted to the root. Load another avatar with `?avatar=<url-to-glb>` or `VITE_AVATAR_URL`.

## Setup

```bash
npm install
cp .env.example .env              # add ELEVENLABS_API_KEY
npm run create-agent              # creates the "Kimmy" agent and saves ELEVENLABS_AGENT_ID in .env
npm run dev                       # http://localhost:5173 (also on your LAN, for testing on a phone)
```

Run `npm run create-agent` again with `ELEVENLABS_AGENT_ID` set to push persona changes to the existing agent. To give Kimmy her own voice, design one in ElevenLabs (Voice Design), then set `KIMMY_VOICE_ID` and run the script again.

Phones need HTTPS for microphone access. Deploy to Vercel, which picks up `api/token.js` automatically, and set `ELEVENLABS_API_KEY` and `ELEVENLABS_AGENT_ID` there.

## The on-screen numbers

- **reacts**: time from the end of your speech to Kimmy's visible "thinking" reaction. This is local; the target is under 150 ms.
- **first audio**: time from the end of your speech to the start of her voice. The target is under 800 ms.
- **median**: the median first-audio time over the session.

## Known limits (P0)

- Lip sync taps the SDK's output analyser, so it can't be delayed to cancel HeadAudio's 50–100 ms processing lag. If the mouth looks late, the next step is to play the audio through TalkingHead with a matching delay.
- HeadAudio's viseme model is trained on English, but it works on any speech audio, Dutch included, with somewhat less accuracy.
- The agent language is set to English. Kimmy is told to answer in Dutch when the user speaks Dutch; set up proper language detection in the agent if needed.
