import "./style.css";
import { Avatar } from "./avatar.js";
import { Behavior } from "./behavior.js";
import { startVoice, outputAnalyser } from "./voice.js";

const $ = (id) => document.getElementById(id);
const ui = { stage: $("avatar"), button: $("talk"), view: $("view"), state: $("state"), info: $("info"), react: $("lat-react"), audio: $("lat-audio"), median: $("lat-median"), caption: $("caption") };

const avatar = new Avatar(ui.stage);
const behavior = new Behavior(avatar, {
  onState: (s) => { ui.state.textContent = s; document.body.dataset.state = s; },
  onLatency: ({ react, firstAudio, median, n }) => {
    if (react != null) ui.react.textContent = `${Math.round(react)} ms`;
    if (firstAudio != null) ui.audio.textContent = `${Math.round(firstAudio)} ms`;
    if (median != null) ui.median.textContent = `${Math.round(median)} ms (n=${n})`;
  },
});

let conversation = null;
window.kimmy = { avatar, behavior }; // for debugging in the console
let raf = 0;

function loop() {
  if (conversation) behavior.tick(conversation.getInputVolume());
  raf = requestAnimationFrame(loop);
}

async function connect() {
  ui.button.disabled = true;
  ui.button.textContent = "Verbinden…";
  try {
    avatar.start();
    conversation = await startVoice({
      clientTools: {
        set_mood: ({ mood }) => { avatar.setMood(mood); },
        gesture: ({ name }) => { avatar.gesture(name); },
      },
      onModeChange: (mode) => (mode === "speaking" ? behavior.agentSpeaking() : behavior.agentListening()),
      onInterruption: () => behavior.interrupted(),
      onStatus: (s) => { if (s === "disconnected") teardown(); },
      onMessage: ({ message, source }) => { ui.caption.textContent = source === "ai" ? message : ""; },
    });

    const analyser = outputAnalyser(conversation);
    if (analyser) await avatar.attachLipsync(analyser).catch((e) => {
      console.warn("HeadAudio unavailable, using volume lip sync", e);
      avatar.attachVolumeLipsync(() => conversation?.getOutputVolume() ?? 0);
    });
    else avatar.attachVolumeLipsync(() => conversation?.getOutputVolume() ?? 0);

    behavior.start();
    loop();
    ui.button.textContent = "Stop";
  } catch (e) {
    console.error(e);
    ui.info.textContent = e.message;
    ui.info.hidden = false;
    teardown();
  } finally {
    ui.button.disabled = false;
  }
}

function teardown() {
  cancelAnimationFrame(raf);
  avatar.detachLipsync();
  behavior.stop();
  const c = conversation;
  conversation = null;
  c?.endSession().catch(() => {});
  ui.button.textContent = "Praat met Kimmy";
}

let fullBody = true;
ui.view.addEventListener("click", () => {
  fullBody = !fullBody;
  avatar.setView(fullBody ? "full" : "upper");
  ui.view.textContent = fullBody ? "Close-up" : "Heel lichaam";
});

ui.button.addEventListener("click", () => (conversation ? teardown() : connect()));

document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") avatar.start(); else avatar.stop();
});

ui.info.textContent = "Kimmy laden…";
avatar.load((ev) => {
  if (ev?.lengthComputable) ui.info.textContent = `Kimmy laden… ${Math.round((ev.loaded / ev.total) * 100)}%`;
}).then(() => {
  ui.info.hidden = true;
  ui.button.disabled = false;
}).catch((e) => {
  ui.info.textContent = `Could not load avatar: ${e.message}`;
});
