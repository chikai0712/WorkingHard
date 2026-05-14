# 輸出資訊

output "route53_zone_id" {
  description = "Route53 Hosted Zone ID"
  value       = aws_route53_zone.main.zone_id
}

output "route53_name_servers" {
  description = "Route53 Name Servers（請將這些 NS 記錄設定到您的域名註冊商）"
  value       = aws_route53_zone.main.name_servers
}

output "acm_certificate_arn" {
  description = "ACM 憑證 ARN"
  value       = aws_acm_certificate.cloudfront.arn
}

output "acm_certificate_status" {
  description = "ACM 憑證狀態"
  value       = aws_acm_certificate.cloudfront.status
}

output "cloudfront_distribution_id" {
  description = "CloudFront Distribution ID"
  value       = aws_cloudfront_distribution.main.id
}

output "cloudfront_domain_name" {
  description = "CloudFront 域名"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "cloudfront_url" {
  description = "CloudFront HTTPS URL"
  value       = "https://${aws_cloudfront_distribution.main.domain_name}"
}

output "s3_bucket_name" {
  description = "S3 Bucket 名稱"
  value       = aws_s3_bucket.website.id
}

output "s3_bucket_arn" {
  description = "S3 Bucket ARN"
  value       = aws_s3_bucket.website.arn
}

output "website_url" {
  description = "網站 URL"
  value       = "https://${var.domain_name}"
}

output "setup_instructions" {
  description = "設定說明"
  value       = <<-EOT
  
  ✅ 部署完成！請按照以下步驟完成設定：
  
  1. 更新域名 NS 記錄：
     請到您的域名註冊商（如 GoDaddy、Namecheap 等），將以下 Name Servers 設定到您的域名：
     ${join("\n     ", aws_route53_zone.main.name_servers)}
  
  2. 上傳網站內容到 S3：
     aws s3 sync ./your-website-folder s3://${aws_s3_bucket.website.id}/
  
  3. 測試網站：
     https://${var.domain_name}
     https://www.${var.domain_name}
  
  4. CloudFront 管理：
     Distribution ID: ${aws_cloudfront_distribution.main.id}
     清除快取: aws cloudfront create-invalidation --distribution-id ${aws_cloudfront_distribution.main.id} --paths "/*"
  
  EOT
}
