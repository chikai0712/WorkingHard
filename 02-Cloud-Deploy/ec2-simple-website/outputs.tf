output "website_url" {
  description = "HTTP website URL."
  value       = "http://${aws_eip.website.public_ip}"
}

output "elastic_ip" {
  description = "Elastic IP assigned to the EC2 website."
  value       = aws_eip.website.public_ip
}

output "instance_id" {
  description = "EC2 instance ID."
  value       = aws_instance.website.id
}

output "ssh_command" {
  description = "SSH command for connecting to the EC2 instance."
  value       = "ssh -i ${var.ssh_private_key_path} ec2-user@${aws_eip.website.public_ip}"
}

output "dns_next_step" {
  description = "Manual DNS instruction for the next phase."
  value       = "Point ${var.domain_name} or www.${var.domain_name} A record to ${aws_eip.website.public_ip} after HTTP validation succeeds."
}
