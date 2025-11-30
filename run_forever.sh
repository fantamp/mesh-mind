#!/bin/bash

# Loop to restart the bot if it exits (e.g., for updates)
while true; do
    echo "Starting Mesh Mind Bot..."
    
    python -m telegram_bot.main
    
    EXIT_CODE=$?
    echo "Bot exited with code $EXIT_CODE."
    
    echo "Restarting in 5 seconds... (Press Ctrl+C to stop)"
    sleep 5
done
