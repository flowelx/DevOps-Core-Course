variable "zone" {
  type = string
  default = "ru-central1-b"
}

variable "folder_id" {
  type = string
}

variable "vm_name" {
  type = string
  default = "terraform"
}

variable "subnet_id" {
  type = string
}

variable "image_id" {
  type = string
  default = "fd804teg9bthv0h96s8v"
}

variable "ssh_public_key" {
  type = string
  sensitive = true
}

variable "network_name" {
  type = string
  default = "default"
}

variable "sg_name" {
  type = string
  default = "terraform-vm-security-group"
}

variable "network_id" {
  type = string
}
