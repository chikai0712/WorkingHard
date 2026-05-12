#!/bin/bash
cd /Users/selina/Desktop/Game/Ollie
open -a "Google Chrome" battle_game.html 2>/dev/null || \
open -a "Safari" battle_game.html 2>/dev/null || \
open -a "Firefox" battle_game.html 2>/dev/null || \
python3 -m webbrowser -t "file:///Users/selina/Desktop/Game/Ollie/battle_game.html"

