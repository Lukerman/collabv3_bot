#!/bin/bash

# Check if bot process is running
if systemctl is-active --quiet collalearn; then
    echo "✅ Bot is running"
else
    echo "❌ Bot is not running"
    systemctl start collalearn
fi

# Check MongoDB
if systemctl is-active --quiet mongod; then
    echo "✅ MongoDB is running"
else
    echo "❌ MongoDB is not running"
    systemctl start mongod
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "⚠️  Disk usage is above 90%: ${DISK_USAGE}%"
fi