output "vm_ip_address" {
  description = "Public IP address VM"
  value = yandex_compute_instance.vm.network_interface[0].nat_ip_address
}
