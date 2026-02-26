import pulumi
from pulumi_yandex import compute, vpc
import requests

config = pulumi.Config()

folder_id = config.require("folder_id") 
cloud_id = config.require("cloud_id")

zone = config.get("zone", "ru-central1-b")
vm_name = config.get("vm_name", "pulumi-vm")
subnet_id = config.get("subnet_id") 
network_name = config.get("network_name", "default")
image_family = config.get("image_family", "ubuntu-2204-lts")
ssh_public_key = config.require("ssh_public_key")
cpu_cores = config.get_int("cpu_cores", 2)
memory_gb = config.get_int("memory_gb", 4)
disk_size_gb = config.get_int("disk_size_gb", 20)

try:
    my_ip = requests.get('https://api.ipify.org').text.strip()
    pulumi.export('my_ip', my_ip)
except:
    my_ip = "0.0.0.0"  # fallback
    pulumi.log.warn("Не удалось определить ваш IP, используется 0.0.0.0")

image = compute.get_image(
    family=image_family,
    folder_id="standard-images" 
)

network = vpc.get_network(name=network_name)

security_group = vpc.SecurityGroup(
    "vm-sg",
    name="pulumi-vm-security-group",
    description="Правила firewall для ВМ",
    network_id=network.id,
    ingress=[
        vpc.SecurityGroupIngressArgs(
            protocol="TCP",
            description="SSH",
            port=22,
            v4_cidr_blocks=[f"{my_ip}/32"],
        ),
        vpc.SecurityGroupIngressArgs(
            protocol="TCP",
            description="HTTP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
        vpc.SecurityGroupIngressArgs(
            protocol="TCP",
            description="App Port 5000",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egress=[
        vpc.SecurityGroupEgressArgs(
            protocol="ANY",
            description="Outbound traffic",
            v4_cidr_blocks=["0.0.0.0/0"],
            from_port=0,
            to_port=65535,
        )
    ],
)

if not subnet_id:
    subnet = vpc.Subnet(
        "vm-subnet",
        name="pulumi-vm-subnet",
        zone=zone,
        network_id=network.id,
        v4_cidr_blocks=["192.168.10.0/24"],
    )
    subnet_id = subnet.id

vm = compute.Instance(
    vm_name,
    name=vm_name,
    zone=zone,
    platform_id="standard-v3",
    resources=compute.InstanceResourcesArgs(
        cores=cpu_cores,
        memory=memory_gb,
        core_fraction=20,
    ),
    boot_disk=compute.InstanceBootDiskArgs(
        initialize_params=compute.InstanceBootDiskInitializeParamsArgs(
            image_id=image.id,
            size=disk_size_gb,
            type="network-hdd",
        ),
    ),
    network_interfaces=[
        compute.InstanceNetworkInterfaceArgs(
            subnet_id=subnet_id,
            nat=True,
            security_group_ids=[security_group.id],
        )
    ],
    metadata={
        "user-data": f"""#cloud-config
users:
  - name: ubuntu
    groups: sudo
    shell: /bin/bash
    sudo: ['ALL=(ALL) NOPASSWD:ALL']
    ssh-authorized-keys:
      - {ssh_public_key}
""",
    },
    labels={
        "environment": config.get("environment", "development"),
        "managed_by": "pulumi",
        "project": config.get("project_name", "pulumi-demo"),
    },
)

pulumi.export("vm_id", vm.id)
pulumi.export("vm_name", vm.name)
pulumi.export("external_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("internal_ip", vm.network_interfaces[0].ip_address)
pulumi.export("ssh_command", vm.network_interfaces[0].nat_ip_address.apply(
    lambda ip: f"ssh ubuntu@{ip}"
))
pulumi.export("security_group_id", security_group.id)
pulumi.export("zone", zone)
pulumi.export("image_id", image.id)
