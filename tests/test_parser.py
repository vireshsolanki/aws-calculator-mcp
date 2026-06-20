from aws_calc_mcp.parser import parse_prompt


def _service(prompt: str, name: str) -> dict:
    services, _notes, unknown = parse_prompt(prompt)
    assert unknown == []
    matches = [svc for svc in services if svc["service"] == name]
    assert matches, services
    return matches[0]


def test_ec2_prompt_defaults_to_30gb_boot_storage():
    ec2 = _service("2 m5.large EC2, RDS MySQL db.m5.large 100GB, an ALB", "ec2")

    assert ec2["config"]["instances"] == 2
    assert ec2["config"]["instance_type"] == "m5.large"
    assert ec2["config"]["storage_gb"] == 30


def test_explicit_ec2_storage_still_wins():
    ec2 = _service("1 t4g.small server with 20GB for a personal blog", "ec2")

    assert ec2["config"]["instance_type"] == "t4g.small"
    assert ec2["config"]["storage_gb"] == 20


def test_aurora_nodes_after_instance_type_are_detected():
    aurora = _service("Aurora MySQL db.r6g.large 2 nodes", "aurora mysql")

    assert aurora["config"]["instance_type"] == "db.r6g.large"
    assert aurora["config"]["nodes"] == 2


def test_hyderabad_dr_prompt_detects_region_and_hours():
    ec2 = _service(
        "In Hyderabad create DR for 3 Windows EC2 servers m5.xlarge with 300GB storage, 8 hours per month",
        "ec2",
    )

    assert ec2["region"] == "ap-south-2"
    assert ec2["config"]["instances"] == 3
    assert ec2["config"]["os"] == "windows"
    assert ec2["config"]["hours_per_month"] == 8


def test_data_transfer_prompt_maps_outbound_transfer():
    transfer = _service("AWS data transfer 250GB outbound", "data transfer")

    assert transfer["config"] == {"data_outbound_gb": 250}
