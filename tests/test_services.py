from aws_calc_mcp.services import build


def test_ec2_omits_transfer_table_when_not_configured():
    payload = build("EC2", "us-east-1", "app", {
        "instances": 1,
        "instance_type": "t3.micro",
        "storage_gb": 30,
    })

    calc = payload["calculationComponents"]
    assert calc["storageAmount"] == {"value": "30", "unit": "gb|NA"}
    assert "dataTransferForEC2" not in calc


def test_ec2_includes_transfer_table_when_configured():
    payload = build("EC2", "ap-south-2", "dr", {
        "instances": 1,
        "instance_type": "m5.xlarge",
        "storage_gb": 300,
        "data_inbound_gb": 100,
        "data_outbound_gb": 100,
        "data_intra_region_gb": 100,
        "data_inbound_from_region": "",
        "data_outbound_to_region": "",
    })

    rows = payload["calculationComponents"]["dataTransferForEC2"]["value"]
    assert rows == [
        {"entryType": "INBOUND", "value": "100", "unit": "gb_month", "fromRegion": ""},
        {"entryType": "OUTBOUND", "value": "100", "unit": "gb_month", "toRegion": ""},
        {"entryType": "INTRA_REGION", "value": "100", "unit": "gb_month"},
    ]


def test_s3_omits_data_transfer_subservice_when_not_configured():
    payload = build("S3", "us-east-1", "bucket", {"storage_gb": 100})

    assert len(payload["subServices"]) == 1
    assert payload["subServices"][0]["estimateFor"] == "s3Standard"


def test_s3_includes_data_transfer_subservice_when_configured():
    payload = build("S3", "us-east-1", "bucket", {
        "storage_gb": 100,
        "data_outbound_gb": 50,
    })

    assert len(payload["subServices"]) == 2
    transfer = payload["subServices"][1]
    assert transfer["serviceCode"] == "awsS3DataTransfer"
    assert transfer["calculationComponents"]["dataTransfer"]["value"][1] == {
        "entryType": "OUTBOUND",
        "value": "50",
        "unit": "gb_month",
        "toRegion": "External",
    }


def test_edr_matches_replicate_and_drill_shape():
    payload = build("EDR", "ap-south-2", "EDR", {
        "source_servers": 3,
        "disks": 5,
        "storage_gb": 2800,
        "change_rate_pct": 15,
        "retention_days": 7,
        "percent_large_disks": 80,
    })

    assert payload["serviceCode"] == "awsElasticDisasterRecovery"
    assert [sub["serviceCode"] for sub in payload["subServices"]] == [
        "awsDrsRecoveryReplication",
        "awsDrsDrill",
    ]
    replication = payload["subServices"][0]["calculationComponents"]
    assert replication["ebsVolumeType"]["value"] == "Storage General Purpose gp3 GB Mo"
    assert replication["storageAmount"] == {"value": "2800", "unit": "gb|NA"}


def test_data_transfer_builder():
    payload = build("AWS Data Transfer", "ap-south-2", None, {
        "data_inbound_gb": 250,
        "data_outbound_gb": 250,
        "data_intra_region_gb": 250,
        "data_inbound_from_region": "",
        "data_outbound_to_region": "",
    })

    assert payload["serviceCode"] == "aWSDataTransfer"
    assert payload["calculationComponents"]["dataTransfer"]["value"] == [
        {"entryType": "INBOUND", "value": "250", "unit": "gb_month", "fromRegion": ""},
        {"entryType": "OUTBOUND", "value": "250", "unit": "gb_month", "toRegion": ""},
        {"entryType": "INTRA_REGION", "value": "250", "unit": "gb_month"},
    ]
