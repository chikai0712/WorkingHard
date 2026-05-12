# ============================================================
# variables.tf — 所有可調整的參數
# ============================================================

# ── GCP ──────────────────────────────────────────────────────
variable "gcp_credentials_file" {
  description = "GCP Service Account JSON 金鑰路徑"
  type        = string
}

variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region"
  type        = string
  default     = "asia-northeast1"
}

variable "gcp_zone" {
  description = "GCP Zone"
  type        = string
  default     = "asia-northeast1-b"
}

variable "gce_machine_type" {
  description = "GCE VM 機型"
  type        = string
  default     = "e2-micro"
}

variable "gce_instance_name" {
  description = "GCE VM 名稱"
  type        = string
  default     = "test-web-server"
}

# ── AWS ──────────────────────────────────────────────────────
variable "aws_region" {
  description = "AWS Region（CloudFront + Route53）"
  type        = string
  default     = "ap-northeast-1"
}

variable "domain_name" {
  description = "根網域名稱，例如 example.com"
  type        = string
}

variable "subdomain" {
  description = "子網域，例如 www"
  type        = string
  default     = "www"
}

variable "route53_zone_id" {
  description = "Route53 Hosted Zone ID"
  type        = string
}

variable "cloudfront_price_class" {
  description = "CloudFront 價格方案"
  type        = string
  default     = "PriceClass_200" # 涵蓋亞太、美洲、歐洲
}
