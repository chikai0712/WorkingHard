variable "aws_profile" {
  description = "AWS CLI profile used for the new AWS account."
  type        = string
  default     = "new-website"
}

variable "aws_region" {
  description = "AWS region for the EC2 website."
  type        = string
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "Project name used for resource tags and names."
  type        = string
  default     = "ec2-simple-website"
}

variable "environment" {
  description = "Environment tag."
  type        = string
  default     = "dev"
}

variable "instance_name" {
  description = "EC2 instance Name tag."
  type        = string
  default     = "cloudsite-simple-web"
}

variable "instance_type" {
  description = "EC2 instance type."
  type        = string
  default     = "t3.micro"
}

variable "root_volume_size_gb" {
  description = "Root EBS volume size in GiB."
  type        = number
  default     = 8
}

variable "key_pair_name" {
  description = "AWS EC2 Key Pair name to create from the local public key."
  type        = string
  default     = "cloudsite-new-website-key"
}

variable "public_key_path" {
  description = "Path to local SSH public key."
  type        = string
  default     = "./cloudsite-new-website-key.pub"
}

variable "ssh_private_key_path" {
  description = "Path to local SSH private key, used only for output instructions."
  type        = string
  default     = "./cloudsite-new-website-key"
}

variable "ssh_allowed_cidr" {
  description = "CIDR allowed to SSH into the EC2 instance. Use your public IP with /32."
  type        = string

  validation {
    condition     = can(cidrhost(var.ssh_allowed_cidr, 0))
    error_message = "ssh_allowed_cidr must be a valid CIDR, for example 203.0.113.10/32."
  }
}

variable "domain_name" {
  description = "Optional domain planned for this site. DNS is not managed in phase 1."
  type        = string
  default     = "clouddeployment168.site"
}
