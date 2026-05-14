variable "aws_region" {
  description = "AWS 區域"
  type        = string
  default     = "ap-northeast-1" # 東京區域，可改為 us-east-1, us-west-2 等
}

variable "domain_name" {
  description = "你的域名（例如：example.com）"
  type        = string
  # 請修改為你的域名
  # default     = "example.com"
}

variable "bucket_name" {
  description = "S3 Bucket 名稱（必須全球唯一）"
  type        = string
  # 建議格式：your-domain-name-website 或 your-domain-name-static
  # default     = "example-com-website"
}

variable "additional_domains" {
  description = "額外的域名（例如：www.example.com）"
  type        = list(string)
  default     = []
}

variable "create_route53_zone" {
  description = "是否在 Route 53 建立 Hosted Zone（如果域名已在 Route 53，設為 true）"
  type        = bool
  default     = false
}

variable "cloudfront_price_class" {
  description = "CloudFront 價格等級"
  type        = string
  default     = "PriceClass_100" # 僅北美和歐洲，最便宜
  # 選項：
  # - PriceClass_100: 僅北美和歐洲（最便宜）
  # - PriceClass_200: 包含北美、歐洲、亞洲、中東、非洲
  # - PriceClass_All: 全球所有區域（最貴）
}
