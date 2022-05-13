locals {
  tags = {
    Name = "mc-syntropy"
  }
}

locals {
    ingress = [
        {
            cidr_blocks = [ "0.0.0.0/0" ]
            description = "ingress"
            from_port = 0
            protocol = "-1"
            ipv6_cidr_blocks = null
            prefix_list_ids = null 
            security_groups = null
            self = null
            to_port = 0
        }
    ]

    egress = [
        {
            cidr_blocks = [ "0.0.0.0/0" ]
            description = "egress"
            from_port = 0
            protocol = "-1"
            ipv6_cidr_blocks = null
            prefix_list_ids = null 
            security_groups = null
            self = null
            to_port = 0
        }
    ]
}