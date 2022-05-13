terraform {
  required_version = "v0.14.8"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.69"
    }
  }
}

resource "aws_vpc" "this" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support = true
  
  tags = local.tags
}

resource "aws_subnet" "this" {
  cidr_block = "10.0.0.0/16"
  vpc_id = aws_vpc.this.id
  availability_zone = "eu-west-2a"
  map_public_ip_on_launch = true

  tags = local.tags
}

resource "aws_security_group" "this" {
  name = "mc-syntropy"

  vpc_id = aws_vpc.this.id

  ingress = local.ingress

  egress = local.egress
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = local.tags
}

resource "aws_route_table" "this" {
  vpc_id = aws_vpc.this.id

  route = [ {
    carrier_gateway_id = null
    cidr_block = "0.0.0.0/0"
    destination_prefix_list_id = null
    egress_only_gateway_id = null
    gateway_id = aws_internet_gateway.this.id
    instance_id = null
    ipv6_cidr_block = null
    local_gateway_id = null
    nat_gateway_id = null
    network_interface_id = null
    transit_gateway_id = null
    vpc_endpoint_id = null
    vpc_peering_connection_id = null
  } ]

  tags = local.tags
}

resource "aws_route_table_association" "this" {
  subnet_id = aws_subnet.this.id
  route_table_id = aws_route_table.this.id
}

resource "aws_instance" "this" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t2.large"
  key_name = var.ssh_key_name
  security_groups = [aws_security_group.this.id]
  subnet_id = aws_subnet.this.id
  tags = local.tags
}

 resource "local_file" "this" {
   content = templatefile("inventory.tmpl", {
     ip_address  = try("${aws_instance.this.public_ip}", ""),
     key_name = try("${var.ssh_key_name}", ""),
   })
   filename = "../ansible/inventory.yml"
}
