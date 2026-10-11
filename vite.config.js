import { defineConfig, loadEnv } from "vite";
import { getConversationToken } from "./api/token.js";

// In dev, serve /api/token from the Vite server so `npm run dev` works without Vercel.
function devTokenRoute(env) {
  return {
    name: "kimmy-dev-token",
    configureServer(server) {
      server.middlewares.use("/api/token", async (req, res) => {
        const { status, body } = await getConversationToken(env, req.headers["x-kimmy-password"] || "");
        res.statusCode = status;
        res.setHeader("Content-Type", "application/json");
        res.setHeader("Cache-Control", "no-store");
        res.end(JSON.stringify(body));
      });
    },
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  return {
    plugins: [devTokenRoute(env)],
    server: { host: true },
    assetsInclude: ["**/*.bin"],
  };
});
