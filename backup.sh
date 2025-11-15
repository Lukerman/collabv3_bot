#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/collalearn"
mkdir -p $BACKUP_DIR

# Backup MongoDB
mongodump --db collalearn --out $BACKUP_DIR/mongodb_$DATE

# Backup environment file
cp .env $BACKUP_DIR/.env_$DATE

# Compress
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz $BACKUP_DIR/mongodb_$DATE $BACKUP_DIR/.env_$DATE

# Clean up
rm -rf $BACKUP_DIR/mongodb_$DATE $BACKUP_DIR/.env_$DATE

# Keep only last 7 backups
ls -t $BACKUP_DIR/backup_*.tar.gz | tail -n +8 | xargs rm -f

echo "Backup completed: backup_$DATE.tar.gz"