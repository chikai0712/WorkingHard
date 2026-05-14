#!/bin/bash
# fix-nginx.sh — Fix nginx on GCE VM to serve plain HTTP on port 80
set -e

INSTANCE=test-web-server
ZONE=asia-northeast1-b
PROJECT=future-union-463404-t9

echo '==> Writing nginx config...'
gcloud compute ssh "$INSTANCE" \
  --zone="$ZONE" \
  --project="$PROJECT" \
  --command="sudo tee /etc/nginx/sites-available/default > /dev/null << 'NGINXEOF'
server {
    listen 80;
    server_name _;
    root /var/www/html;
    index index.html;

    location /health {
        return 200 'ok';
        add_header Content-Type text/plain;
    }

    location / {
        try_files \\$uri \\$uri/ =404;
    }
}
NGINXEOF"

echo '==> Testing and restarting nginx...'
gcloud compute ssh "$INSTANCE" \
  --zone="$ZONE" \
  --project="$PROJECT" \
  --command="sudo nginx -t && sudo systemctl restart nginx && echo 'nginx OK'"

echo '==> Done. Wait ~30s then test: curl -sI https://www.clouddeployment168.site'
