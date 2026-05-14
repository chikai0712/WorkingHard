# ============================================================
# aws_cloudfront.tf — ACM 憑證 + CloudFront Distribution
# ============================================================

provider "aws" {
  region = var.aws_region
}

# ACM 憑證必須建在 us-east-1（CloudFront 限制）
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

# ── ACM 憑證（DNS 驗證）────────────────────────────────────────
resource "aws_acm_certificate" "cert" {
  provider          = aws.us_east_1
  domain_name       = "${var.subdomain}.${var.domain_name}"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name    = "${var.subdomain}.${var.domain_name}"
    Project = "terraform-cdn-setup"
  }
}

# ACM DNS 驗證紀錄（自動加到 Route53）
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.cert.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      record = dvo.resource_record_value
    }
  }

  zone_id = var.route53_zone_id
  name    = each.value.name
  type    = each.value.type
  records = [each.value.record]
  ttl     = 60
}

# 等待 ACM 驗證完成
resource "aws_acm_certificate_validation" "cert" {
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.cert.arn
  validation_record_fqdns = [for r in aws_route53_record.cert_validation : r.fqdn]
}

# ── CloudFront Distribution ──────────────────────────────────
resource "aws_cloudfront_distribution" "cdn" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "CDN for ${var.subdomain}.${var.domain_name}"
  default_root_object = "index.html"
  price_class         = var.cloudfront_price_class
  aliases             = ["${var.subdomain}.${var.domain_name}"]

  # Origin：GCE VM（HTTPS）
  # CloudFront 不允許 IP 作為 origin，改用 sslip.io 將 IP 轉為 DNS 名稱
  # 34.180.110.77 → 34-180-110-77.sslip.io
  origin {
    domain_name = "${replace(google_compute_address.web_ip.address, ".", "-")}.sslip.io"
    origin_id   = "gce-origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
      origin_keepalive_timeout = 5
      origin_read_timeout      = 30
    }

    custom_header {
      name  = "X-Origin-Secret"
      value = "cloudfront-gce-${var.gcp_project_id}"
    }
  }

  # 預設快取行為
  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "gce-origin"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    cache_policy_id          = "658327ea-f89d-4fab-a63d-7e88639e58f6" # CachingOptimized
    origin_request_policy_id = "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf" # CORS-S3Origin

    min_ttl     = 0
    default_ttl = 86400
    max_ttl     = 31536000
  }

  # /health 不快取（健康檢查用）
  ordered_cache_behavior {
    path_pattern           = "/health"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "gce-origin"
    viewer_protocol_policy = "redirect-to-https"

    cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" # CachingDisabled
    min_ttl         = 0
    default_ttl     = 0
    max_ttl         = 0
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.cert.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Name    = "${var.subdomain}.${var.domain_name}"
    Project = "terraform-cdn-setup"
  }

  depends_on = [aws_acm_certificate_validation.cert]
}
