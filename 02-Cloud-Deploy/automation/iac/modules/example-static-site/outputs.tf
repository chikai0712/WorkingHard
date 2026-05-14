output "name_prefix" {
  description = "Computed resource prefix"
  value       = local.name_prefix
}

output "common_tags" {
  description = "Merged common tags"
  value       = local.common_tags
}
