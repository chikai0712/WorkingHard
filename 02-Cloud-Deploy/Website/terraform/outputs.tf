output "s3_bucket_name" {
  description = "S3 Bucket 名稱"
  value       = aws_s3_bucket.website.id
}

output "s3_bucket_website_endpoint" {
  description = "S3 靜態網站端點（僅用於測試，正式使用 CloudFront）"
  value       = aws_s3_bucket_website_configuration.website.website_endpoint
}

output "cloudfront_distribution_id" {
  description = "CloudFront Distribution ID"
  value       = aws_cloudfront_distribution.website.id
}

output "cloudfront_domain_name" {
  description = "CloudFront 域名"
  value       = aws_cloudfront_distribution.website.domain_name
}

output "cloudfront_arn" {
  description = "CloudFront Distribution ARN"
  value       = aws_cloudfront_distribution.website.arn
}

output "acm_certificate_arn" {
  description = "ACM 證書 ARN"
  value       = aws_acm_certificate.website.arn
}

output "website_url" {
  description = "網站網址"
  value       = "https://${var.domain_name}"
}

output "domain_name" {
  description = "域名"
  value       = var.domain_name
}

output "dns_instructions" {
  description = "DNS 設定說明"
  value = var.create_route53_zone ? "DNS 已自動設定在 Route 53" : <<-EOT
    請在你的 DNS 提供商設定以下記錄：
    
    Type: A (或 CNAME)
    Name: ${var.domain_name}
    Value: ${aws_cloudfront_distribution.website.domain_name}
    
    或使用 Alias：
    Type: A (Alias)
    Name: ${var.domain_name}
    Alias Target: ${aws_cloudfront_distribution.website.domain_name}
    Alias Hosted Zone ID: ${aws_cloudfront_distribution.website.hosted_zone_id}
    
    ${length(var.additional_domains) > 0 ? "\n對於子域名（如 www）：\n" : ""}
    ${join("\n", [for domain in var.additional_domains : "Type: CNAME\nName: ${domain}\nValue: ${aws_cloudfront_distribution.website.domain_name}"])}
    
    ⚠️ 注意：ACM 證書驗證需要設定 DNS 記錄
    請查看 ACM 證書的驗證記錄並在 DNS 中設定
  EOT
}

output "acm_validation_records" {
  description = "ACM 證書驗證所需的 DNS 記錄"
  value = {
    for dvo in aws_acm_certificate.website.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      record = dvo.resource_record_value
    }
  }
}
