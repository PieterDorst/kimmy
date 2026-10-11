// Client-side conversation state machine. Body language reacts here, on the
// device, without waiting for the network: idle → listening → thinking → speaking.
//
// It also measures the latency the user actually feels:
//   end of user speech → Kimmy visibly reacts (thinking pose)
//   end of user speech → first audio from Kimmy

const SPEECH_DB_ON = 0.06;   // input volume (0..1) that counts as the user talking
const SPEECH_DB_OFF = 0.03;
const MIN_SPEECH_MS = 250;   // ignore coughs and clicks
const END_SILENCE_MS = 120;  // silence after speech before we call it "user stopped"

export class Behavior {
  constructor(avatar, { onState, onLatency } = {}) {
    this.avatar = avatar;
    this.onState = onState || (() => {});
    this.onLatency = onLatency || (() => {});
    this.state = "idle";
    this.userTalking = false;
    this.userStart = 0;
    this.lastLoud = 0;
    this.userEndAt = 0;
    this.lastNod = 0;
    this.samples = [];
  }

  set(state) {
    if (state === this.state) return;
    this.state = state;
    this.onState(state);
  }

  // Called every animation frame with the mic level.
  tick(inputVolume, now = performance.now()) {
    if (this.state === "idle") return;
    const loud = inputVolume > (this.userTalking ? SPEECH_DB_OFF : SPEECH_DB_ON);

    if (loud) {
      if (!this.userTalking) { this.userTalking = true; this.userStart = now; }
      this.lastLoud = now;
      if (this.state !== "speaking") this.set("listening");
      return;
    }

    if (this.userTalking && now - this.lastLoud > END_SILENCE_MS) {
      this.userTalking = false;
      const spoke = this.lastLoud - this.userStart;
      if (spoke < MIN_SPEECH_MS || this.state === "speaking") return;
      // User just finished a turn: react instantly, before the server answers.
      this.userEndAt = this.lastLoud;
      this.set("thinking");
      this.avatar.think();
      this.onLatency({ react: now - this.userEndAt });
      return;
    }

    // Backchannel nod during longer user turns, at short pauses.
    if (this.userTalking && now - this.userStart > 2500 && now - this.lastLoud > 60 && now - this.lastNod > 3000) {
      this.lastNod = now;
      this.avatar.nod();
    }
  }

  // ElevenLabs mode changes.
  agentSpeaking(now = performance.now()) {
    if (this.state === "thinking" && this.userEndAt) {
      const firstAudio = now - this.userEndAt;
      this.samples.push(firstAudio);
      this.onLatency({ firstAudio, median: median(this.samples), n: this.samples.length });
      this.userEndAt = 0;
    }
    this.set("speaking");
  }

  agentListening() {
    if (this.state === "speaking") {
      this.set("listening");
      this.avatar.lookAtUser(1000);
    }
  }

  interrupted() {
    this.set("listening");
    this.avatar.lookAtUser(1000);
  }

  start() { this.set("listening"); }
  stop() { this.set("idle"); this.userTalking = false; this.userEndAt = 0; }
}

function median(xs) {
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}
