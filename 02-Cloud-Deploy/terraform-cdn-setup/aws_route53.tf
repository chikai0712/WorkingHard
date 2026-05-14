# ============================================================
# aws_route53.tf — Route53 A Record 指向 CloudFront
# ============================================================

# www.clouddeployment168.site → CloudFront
resource "aws_route53_record" "www" {
  zone_id         = var.route53_zone_id
  name            = "${var.subdomain}.${var.domain_name}"
  type            = "A"
  allow_overwrite = true

  alias {
    name                   = aws_cloudfront_distribution.cdn.domain_name
    zone_id                = aws_cloudfront_distribution.cdn.hosted_zone_id
    evaluate_target_health = false
  }
}
