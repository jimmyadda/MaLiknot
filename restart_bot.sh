#!/bin/bash

echo "🔄 Stopping any existing bot..."
pkill -f "python3.10 /home/maliknot1bot/mysite/app.py"

echo "🚀 Starting bot again..."
nohup python3.10 /home/maliknot1bot/mysite/app.py > /home/maliknot1bot/mysite/bot.log 2>&1 &