# ============================================================
# gcp.tf — GCP Provider + GCE VM（nginx 測試頁）
# ============================================================

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project     = var.gcp_project_id
  region      = var.gcp_region
  zone        = var.gcp_zone
  credentials = file(var.gcp_credentials_file)
}

# ── 靜態外部 IP ───────────────────────────────────────────────
resource "google_compute_address" "web_ip" {
  name   = "${var.gce_instance_name}-ip"
  region = var.gcp_region
}

# ── GCE VM（e2-micro，nginx 測試頁）─────────────────────────
resource "google_compute_instance" "web" {
  name         = var.gce_instance_name
  machine_type = var.gce_machine_type
  zone         = var.gcp_zone

  tags = ["http-server", "https-server", "allow-cloudfront"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 10
    }
  }

  network_interface {
    network = "default"
    access_config {
      nat_ip = google_compute_address.web_ip.address
    }
  }

  # startup script：安裝 nginx + 自簽 SSL + 測試頁
  metadata_startup_script = <<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y nginx openssl

    # 建立自簽憑證（供 CloudFront → Origin 的 HTTPS 使用）
    mkdir -p /etc/nginx/ssl
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
      -keyout /etc/nginx/ssl/selfsigned.key \
      -out    /etc/nginx/ssl/selfsigned.crt \
      -subj "/CN=${var.subdomain}.${var.domain_name}"

    # 建立測試頁
    cat > /var/www/html/index.html <<'HTML'
    <!DOCTYPE html>
    <html lang="zh-Hant">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>${var.subdomain}.${var.domain_name}</title>
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #0a0a0f;
          font-family: 'Courier New', monospace;
          color: #e2e8f0;
        }
        .container {
          text-align: center;
          padding: 3rem;
          border: 1px solid #2d3748;
          border-radius: 4px;
          background: #111118;
          max-width: 480px;
          width: 90%;
        }
        .badge {
          display: inline-block;
          font-size: 0.7rem;
          letter-spacing: 0.15em;
          text-transform: uppercase;
          color: #68d391;
          border: 1px solid #276749;
          padding: 2px 10px;
          border-radius: 2px;
          margin-bottom: 1.5rem;
        }
        h1 {
          font-size: 1.6rem;
          font-weight: 400;
          letter-spacing: 0.05em;
          margin-bottom: 0.75rem;
          color: #f7fafc;
        }
        .domain {
          font-size: 0.85rem;
          color: #4a9eff;
          margin-bottom: 2rem;
          letter-spacing: 0.08em;
        }
        .stack {
          display: flex;
          gap: 0.5rem;
          justify-content: center;
          flex-wrap: wrap;
        }
        .tag {
          font-size: 0.7rem;
          padding: 3px 8px;
          border-radius: 2px;
          letter-spacing: 0.1em;
        }
        .tag.gcp  { background: #1a3a5c; color: #63b3ed; border: 1px solid #2b6cb0; }
        .tag.aws  { background: #3d1a00; color: #f6ad55; border: 1px solid #c05621; }
        .tag.cf   { background: #1a1a3d; color: #b794f4; border: 1px solid #553c9a; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="badge">&#9679; online</div>
        <h1>Test Page</h1>
        <div class="domain">${var.subdomain}.${var.domain_name}</div>
        <div class="stack">
          <span class="tag gcp">GCE Origin</span>
          <span class="tag cf">CloudFront CDN</span>
          <span class="tag aws">Route53 DNS</span>
        </div>
      </div>
    </body>
    </html>
    HTML

    # nginx 設定：同時監聽 80（redirect）和 443（SSL）
    cat > /etc/nginx/sites-available/default <<'NGINX'
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    server {
        listen 443 ssl;
        server_name _;

        ssl_certificate     /etc/nginx/ssl/selfsigned.crt;
        ssl_certificate_key /etc/nginx/ssl/selfsigned.key;

        root /var/www/html;
        index index.html;

        # CloudFront health check
        location /health {
            return 200 'ok';
            add_header Content-Type text/plain;
        }

        location / {
            try_files $uri $uri/ =404;
        }
    }
    NGINX

    systemctl restart nginx
    systemctl enable nginx
  EOF

  service_account {
    scopes = ["cloud-platform"]
  }
}

# ── 防火牆：開放 80 + 443 ─────────────────────────────────────
resource "google_compute_firewall" "allow_web" {
  name    = "${var.gce_instance_name}-allow-web"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  # 只允許 CloudFront IP 範圍（可選：限縮來源）
  # 這裡開放全部，讓 ACM 驗證也能通過
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["allow-cloudfront"]
}
