# 變數定義文件
# 請根據您的需求修改這些值

variable "domain_name" {
  description = "您的域名（例如：example.com）"
  type        = string
  default     = "example.com"  # 請修改為您的域名
}

variable "aws_region" {
  description = "AWS 主要區域"
  type        = string
  default     = "ap-northeast-1"  # 東京區域，可改為其他區域
}

variable "environment" {
  description = "環境標籤（dev/staging/production）"
  type        = string
  default     = "production"
}

variable "cloudfront_price_class" {
  description = "CloudFront 價格等級"
  type        = string
  default     = "PriceClass_All"  # 可選：PriceClass_100, PriceClass_200, PriceClass_All
  
  validation {
    condition     = contains(["PriceClass_100", "PriceClass_200", "PriceClass_All"], var.cloudfront_price_class)
    error_message = "價格等級必須是 PriceClass_100、PriceClass_200 或 PriceClass_All"
  }
}
