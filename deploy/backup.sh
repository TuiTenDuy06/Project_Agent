#!/usr/bin/env bash
# Sao lưu database mỗi ngày, giữ 14 bản gần nhất, xóa hội thoại cũ hơn 90 ngày.
set -euo pipefail

cd "$(dirname "$0")/.."
BACKUP_DIR="$HOME/backups"
mkdir -p "$BACKUP_DIR"

docker compose exec -T db pg_dump -U agent agent | gzip > "$BACKUP_DIR/agent-$(date +%F).sql.gz"
find "$BACKUP_DIR" -name 'agent-*.sql.gz' -mtime +14 -delete

docker compose exec -T db psql -U agent -d agent -c \
    "DELETE FROM messages WHERE created_at < now() - interval '90 days';"

echo "$(date '+%F %T') sao lưu xong"
