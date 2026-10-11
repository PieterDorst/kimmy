#!/bin/bash
# Double-click after changing KIMMY_VOICE_ID (or other settings) in .env.
{
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$(dirname "$0")" || exit 1
npm run create-agent
read -r -p "Klaar. Druk op Enter om te sluiten."
exit
}
