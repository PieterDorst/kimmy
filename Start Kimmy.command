#!/bin/bash
# Double-click in Finder: updates Kimmy, then opens her in your browser.
# (Wrapped in { } so the update can safely replace this file while it runs.)
{
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$(dirname "$0")" || exit 1
echo "Kimmy bijwerken..."
npm run update || echo "Bijwerken lukte niet, ik start de vorige versie."
if ! grep -q '^ELEVENLABS_AGENT_ID=.' .env 2>/dev/null; then
  npm run create-agent || { echo "Controleer je ElevenLabs-sleutel in het .env bestand."; read -r -p "Druk op Enter om te sluiten."; exit 1; }
fi
echo "Kimmy start. Sluit dit venster om haar te stoppen."
npm run dev -- --open
exit
}
