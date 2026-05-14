# ============================================================
# outputs.tf — 部署完成後輸出的重要資訊
# ============================================================

output "gce_public_ip" {
  description = "GCE VM 的靜態公開 IP"
  value       = google_compute_address.web_ip.address
}

output "gce_ssh_command" {
  description = "SSH 連線指令"
  value       = "gcloud compute ssh ${var.gce_instance_name} --zone=${var.gcp_zone} --project=${var.gcp_project_id}"
}

output "cloudfront_domain" {
  description = "CloudFront Distribution 網域名稱"
  value       = aws_cloudfront_distribution.cdn.domain_name
}

output "cloudfront_id" {
  description = "CloudFront Distribution ID"
  value       = aws_cloudfront_distribution.cdn.id
}

output "website_url" {
  description = "網站最終網址"
  value       = "https://${var.subdomain}.${var.domain_name}"
}

output "acm_certificate_arn" {
  description = "ACM 憑證 ARN"
  value       = aws_acm_certificate.cert.arn
}
