terraform {
  required_providers {
    yandex = {
      source = "yandex-cloud/yandex"
    }
  }
  required_version = ">= 0.13"
}

provider "yandex" {
  zone = var.zone
}

data "http" "myip" {
  url = "https://api.ipify.org"
}

data "yandex_vpc_network" "existing-network" {
  name = var.network_name
}

resource "yandex_vpc_security_group" "vm-sg" {
  name = var.sg_name
  network_id = var.network_id
  
  ingress {
    protocol = "TCP"
    description = "SSH"
    port = 22
    v4_cidr_blocks = ["${chomp(data.http.myip.response_body)}/32"]
  }

  ingress {
    protocol = "TCP"
    description = "HTTP"
    port = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol = "TCP"
    description = "App Port 5000"
    port = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol = "ANY"
    description = "Outgoing traffic"
    v4_cidr_blocks = ["0.0.0.0/0"]
    from_port = 0
    to_port = 65535
  }
}

resource "yandex_compute_instance" "vm" {
  name = var.vm_name

  resources {
    cores = 2
    memory = 4
  }

  boot_disk {
    initialize_params {
      image_id = var.image_id
    }
  }

  network_interface {
    subnet_id = var.subnet_id
    nat = true
    security_group_ids = [yandex_vpc_security_group.vm-sg.id]
  }

  metadata = {
    ssh-keys = "ubuntu:${var.ssh_public_key}"
  }
}


