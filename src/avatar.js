// 3D avatar: TalkingHead rendering, Kimmy's expressions and audio-driven lip sync.
import { TalkingHead } from "@met4citizen/talkinghead";
import { HeadAudio } from "@met4citizen/headaudio/dist/headaudio.min.mjs";
import headworkletUrl from "@met4citizen/headaudio/dist/headworklet.min.mjs?url";
import visemeModelUrl from "@met4citizen/headaudio/dist/model-en-mixed.bin?url";

// Stand-in avatar until the real Kimmy GLB exists (VRoid sample from TalkingHead, non-commercial).
const STANDIN_URL =
  "https://cdn.jsdelivr.net/gh/met4citizen/TalkingHead@b3e277b3b46f88e557bf28a2c5612a5b04e075c3/avatars/vroid.glb";

export const AVATAR = {
  url: new URLSearchParams(location.search).get("avatar") || import.meta.env.VITE_AVATAR_URL || STANDIN_URL,
  body: "F",
  avatarMood: "happy",
  baseline: { headRotateX: -0.1, eyeBlinkLeft: 0.05, eyeBlinkRight: 0.05 },
};

// Kimmy's moods map onto TalkingHead's mood engine plus a one-off expression
// (the expressions mirror the reference sheets kimmy1–6).
const MOOD_MAP = {
  happy: { mood: "happy", emoji: "😊" },
  soft: { mood: "happy", emoji: "🙂" },
  grin: { mood: "happy", emoji: "😁" },
  surprised: { mood: "neutral", emoji: "😮" },
  neutral: { mood: "neutral" },
  worried: { mood: "sad", emoji: "😟" },
  thinking: { mood: "neutral", emoji: "🤔" },
  playful: { mood: "happy", emoji: "😏" },
};

const GESTURE_MAP = {
  nod: { emoji: "yes" },
  headshake: { emoji: "no" },
  wink: { emoji: "😉" },
};

// Expressions TalkingHead doesn't ship with.
const EXTRA_EMOJIS = {
  "😮": {
    dt: [200, 1200], rescale: [0, 1],
    vs: { browInnerUp: [0.9], browOuterUpLeft: [0.8], browOuterUpRight: [0.8], eyeWideLeft: [0.8], eyeWideRight: [0.8], jawOpen: [0.25], mouthFunnel: [0.3] },
  },
  "😟": {
    dt: [400, 1500], rescale: [0, 1],
    vs: { browInnerUp: [0.9], browDownLeft: [0.2], browDownRight: [0.2], mouthFrownLeft: [0.4], mouthFrownRight: [0.4], mouthPressLeft: [0.3], mouthPressRight: [0.3], bodyRotateX: [0.05] },
  },
};

export class Avatar {
  constructor(node) {
    this.head = new TalkingHead(node, {
      ttsEndpoint: "N/A",
      lipsyncModules: [],
      cameraView: "upper",
      cameraRotateEnable: false,
      avatarIdleEyeContact: 0.6,
      avatarSpeakingEyeContact: 0.8,
      mixerGainSpeech: 3,
    });
    Object.assign(this.head.animEmojis, EXTRA_EMOJIS);
    this.lipsync = null;
    this.lastSpeechEnd = 0;
  }

  async load(onProgress) {
    await this.head.showAvatar(AVATAR, onProgress);
  }

  start() { this.head.start(); this.lipsync?.start?.(); }
  stop() { this.lipsync?.stop?.(); this.head.stop(); }

  // Play an expression immediately (bypasses TalkingHead's speech queue so it
  // works while ElevenLabs audio is playing).
  express(emoji) {
    let t = this.head.animEmojis[emoji];
    if (t?.link) t = this.head.animEmojis[t.link];
    if (t) this.head.animQueue.push(this.head.animFactory(t));
  }

  setMood(name) {
    const m = MOOD_MAP[name];
    if (!m) return;
    try { this.head.setMood(m.mood); } catch {}
    if (m.emoji) this.express(m.emoji);
  }

  gesture(name) {
    const g = GESTURE_MAP[name];
    if (g) this.express(g.emoji);
    else this.head.playGesture(name, 2, Math.random() < 0.5);
  }

  lookAtUser(ms = 800) { this.head.lookAtCamera(ms); }
  nod() { this.express("yes"); }

  // Visual "I'm thinking" beat: eyes drift up and away, small inhale.
  think() {
    this.head.animQueue.push(this.head.animFactory({
      name: "think", dt: [250, 900, 300], vs: { eyesLookUp: [0.5, 0.5, 0], eyesRotateY: [0.25, 0.25, 0], browInnerUp: [0.3, 0.3, 0], chestInhale: [0.5, 0.5, 0] },
    }));
  }

  // Attach audio-driven lip sync to the analyser node that carries Kimmy's voice.
  // HeadAudio runs inside that node's own AudioContext.
  async attachLipsync(analyser) {
    const ctx = analyser.context;
    await ctx.audioWorklet.addModule(headworkletUrl);
    const node = new HeadAudio(ctx, { parameterData: { speakerMeanHz: 220, vadGateActiveDb: -45, vadGateInactiveDb: -60 } });
    await node.loadModel(visemeModelUrl);
    analyser.connect(node);
    node.onvalue = (key, value) => {
      const mt = this.head.mtAvatar[key];
      if (mt) Object.assign(mt, { newvalue: value, needsUpdate: true });
    };
    node.onended = () => { this.lastSpeechEnd = performance.now(); };
    node.onstarted = () => {
      if (performance.now() - this.lastSpeechEnd > 150) { this.lookAtUser(500); this.head.speakWithHands(); }
    };
    this.head.opt.update = node.update.bind(node);
    node.start();
    this.lipsync = node;
    return node;
  }

  // Fallback when no analyser is available: drive the jaw from output volume.
  attachVolumeLipsync(getVolume) {
    this.head.opt.update = () => {
      const v = Math.min(1, getVolume() * 1.6);
      for (const [k, w] of [["jawOpen", 0.5], ["viseme_aa", 0.8]]) {
        const mt = this.head.mtAvatar[k];
        if (mt) Object.assign(mt, { newvalue: v * w, needsUpdate: true });
      }
    };
  }

  detachLipsync() {
    this.head.opt.update = null;
    try { this.lipsync?.disconnect(); } catch {}
    this.lipsync = null;
  }
}
