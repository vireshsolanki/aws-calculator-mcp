# Examples — Copy-Paste Ready Prompts

Ready-to-use infrastructure descriptions. Copy, paste into `aws-calc --prompt "..."`, and get an instant cost estimate.

---

## Startup / MVP

### Micro: Solo project, minimal cost
```
1 t4g.micro EC2 with 20GB storage, 100MB S3 bucket, Route 53, CloudWatch basic logs
```
**Expected:** ~$8–15/mo

### Small: Basic website
```
1 t3.small EC2 with 30GB storage, 50GB S3 bucket, RDS MySQL db.t3.micro 20GB, Route 53, CloudFront 10GB transfer
```
**Expected:** ~$30–50/mo

### Startup MVP: Blog + API
```
1 t3.medium with 50GB storage daily snapshot, RDS MySQL db.t3.small 50GB single-az, 100GB S3, CloudFront 50GB transfer, API Gateway 100k requests
```
**Expected:** ~$50–80/mo

---

## Small Business (10k–100k users)

### Light web app
```
2 t3.medium EC2 with 50GB each, RDS MySQL db.t3.large 100GB Multi-AZ, ALB, CloudFront 200GB, 500GB S3, CloudWatch standard
```
**Expected:** ~$300–400/mo

### Balanced stack
```
3 t3.large EC2 with 50GB each, RDS MySQL db.m5.large 100GB Multi-AZ, 500GB S3, ALB, CloudFront 500GB, ElastiCache Redis cache.r6g.large, SQS, CloudWatch, CloudTrail
```
**Expected:** ~$500–700/mo

### Compute-heavy (batch processing)
```
5 m5.large EC2 with 100GB each, RDS PostgreSQL db.m5.large 200GB Multi-AZ, 2TB S3, CloudFront 1TB, DynamoDB provisioned 100 RCU 50 WCU, Lambda 2M requests 512MB
```
**Expected:** ~$700–1000/mo

---

## Medium Business (100k–1M users)

### Serverless-first API
```
Lambda 10M requests 256MB, API Gateway 10M requests, DynamoDB provisioned 200 RCU 100 WCU 100GB, S3 1TB, RDS MySQL db.r6g.large 200GB Multi-AZ, CloudFront 1TB, Cognito 50k MAU, KMS 5 CMKs
```
**Expected:** ~$700–1000/mo

### Compute + Database
```
4 m5.xlarge EC2 with 200GB each, RDS Aurora MySQL 2 nodes db.r6g.large, 2TB S3, ALB 1TB data, CloudFront 2TB, ElastiCache Redis cluster 3 nodes cache.r6g.large, CloudWatch 100 metrics
```
**Expected:** ~$1500–2000/mo

### Data lake + Analytics
```
10 m5.xlarge EC2 with 300GB each, RDS PostgreSQL db.m5.2xlarge 500GB Multi-AZ, 10TB S3, Athena 500GB scanned, Redshift cluster 2 nodes dc2.large, AWS Glue 100 DPU hours, QuickSight, CloudTrail
```
**Expected:** ~$3000–4500/mo

---

## Enterprise (1M+ users)

### High-availability infrastructure
```
10 m5.2xlarge EC2 with 500GB each, RDS Aurora MySQL 3 nodes db.r6g.2xlarge, 10TB S3, ALB 5TB data, CloudFront 5TB, ElastiCache Redis 3-node cluster cache.r6g.2xlarge, Cognito 500k MAU, KMS 10 CMKs, CloudWatch 500 metrics
```
**Expected:** ~$5000–7000/mo

### Kubernetes cluster
```
EKS cluster 3 nodes m5.xlarge, 20 Fargate tasks vCPU=2 memory=4GB, RDS Aurora PostgreSQL 3 nodes db.r6g.2xlarge 1TB, 50TB S3, CloudFront 10TB, ElastiCache Redis, GuardDuty, CloudWatch, CloudTrail, WAF
```
**Expected:** ~$6000–8000/mo

### Multi-region disaster recovery
```
4 m5.2xlarge EC2 in us-east-1, 4 m5.2xlarge EC2 in eu-west-1, 
RDS Aurora MySQL primary 2 nodes in us-east-1, secondary 2 nodes in eu-west-1, 
50TB S3, CloudFront 20TB, AWS DRS 10 servers 5 disks each 1000GB change rate
```
**Expected:** ~$12000–15000/mo

---

## AI/ML Workloads

### LLM inference (Bedrock)
```
Lambda 1M requests 2048MB, Bedrock 50 requests/minute, API Gateway 2M requests, DynamoDB provisioned 200 RCU 100 WCU, OpenSearch 4 nodes r6g.large.search, S3 5TB, CloudWatch, CloudTrail
```
**Expected:** ~$2000–3000/mo

### Agent orchestration
```
Lambda 5M requests 1024MB, Bedrock 100 requests/minute 5000 input tokens 8000 output tokens, Step Functions proxy (Lambda), OpenSearch 6 nodes r6g.large.search with 3 master nodes, DynamoDB 300 RCU 150 WCU 200GB, API Gateway 5M requests, SQS 50M messages, SNS 100M notifications
```
**Expected:** ~$4000–6000/mo

### Data pipeline (ETH ETL)
```
Lambda 100M requests 512MB, AWS Glue 500 DPU hours, RDS PostgreSQL db.m5.2xlarge 500GB Multi-AZ, 100TB S3, Athena 2TB scanned, EMR cluster 10 m5.xlarge nodes, Kinesis 1M records/sec, EventBridge
```
**Expected:** ~$5000–8000/mo

---

## Content Delivery

### Video streaming platform
```
CloudFront 500TB/mo, S3 500TB storage, 50M PUT requests, Lambda 50M requests 512MB, DynamoDB provisioned 500 RCU 200 WCU, RDS MySQL db.r6g.2xlarge 500GB Multi-AZ, Cognito 500k MAU, Elemental MediaPackage
```
**Expected:** ~$50000–100000/mo

### Static site CDN
```
CloudFront 1TB/mo, S3 100GB, Route 53 1M queries, WAF 1 ACL 5 rules 1M requests, CloudWatch basic
```
**Expected:** ~$50–100/mo

---

## Real-World Scenarios

### SaaS: Slack-like chat app
```
API Gateway 50M requests, Lambda 50M requests 512MB, 
RDS PostgreSQL db.r6g.large 200GB Multi-AZ, 
DynamoDB 300 RCU 150 WCU for messages/presence, 
S3 2TB for files, CloudFront 500GB, 
ElastiCache Redis cache.r6g.large, 
Cognito 50k MAU, SES 500k emails/mo,
CloudWatch 200 metrics, CloudTrail
```
**Expected:** ~$1500–2000/mo

### FinTech: Real-time trading platform
```
6 m5.2xlarge EC2 24/7, RDS Oracle db.r6g.2xlarge 500GB Multi-AZ, 
ElastiCache Redis 3-node cluster cache.r6g.2xlarge, 
Lambda 100M requests 1024MB, API Gateway 100M requests,
DynamoDB 1000 RCU 500 WCU for order books,
S3 50TB for data, Redshift cluster 3 nodes ra3.xlplus,
CloudWatch 500 metrics, CloudTrail, GuardDuty, WAF
```
**Expected:** ~$10000–15000/mo

### EdTech: LMS with video
```
2 t3.large EC2, Lambda 5M requests 512MB, 
RDS MySQL db.m5.large 100GB Multi-AZ,
DynamoDB 100 RCU 50 WCU for progress tracking,
S3 5TB for course materials and video, CloudFront 2TB transfer,
Bedrock 20 requests/minute for AI tutoring,
OpenSearch 2 nodes t3.medium.search for search,
Cognito 50k MAU, SES 100k emails/mo, SQS, SNS
```
**Expected:** ~$2500–3500/mo

### IoT: Sensor data pipeline
```
Lambda 100M requests 256MB, Kinesis 500k records/sec,
RDS TimeSeries (Aurora PostgreSQL) 3 nodes db.r6g.2xlarge 1TB,
S3 100TB for data lake, Athena 5TB scanned,
Redshift cluster 5 nodes for analytics,
DynamoDB for real-time dashboard 500 RCU 200 WCU,
IoT Core 1M messages, CloudWatch 1000 metrics, X-Ray tracing
```
**Expected:** ~$8000–12000/mo

### Healthcare: HIPAA-compliant app
```
4 m5.large EC2, RDS MySQL db.m5.large 200GB Multi-AZ with encryption,
S3 1TB with versioning and encryption, CloudFront 200GB,
API Gateway 5M requests, Lambda 5M requests 512MB,
DynamoDB 100 RCU 50 WCU, KMS 5 CMKs,
CloudWatch 200 metrics, CloudTrail with log validation,
Config for compliance monitoring, GuardDuty, WAF, VPC with NAT
```
**Expected:** ~$2000–3000/mo

---

## Regional Cost Comparisons

Use these to compare regions:

### Growth tier (same config, different regions)
```
2 t3.large EC2 with 50GB, RDS MySQL db.m5.large 100GB Multi-AZ, 500GB S3, ALB, CloudFront 500GB
```

Run in each region:
```bash
aws-calc --prompt "..." --region us-east-1    # baseline
aws-calc --prompt "..." --region ap-south-1   # Mumbai (cheaper)
aws-calc --prompt "..." --region eu-west-1    # Ireland
aws-calc --prompt "..." --region ap-southeast-1  # Singapore
aws-calc --prompt "..." --region sa-east-1    # São Paulo (most expensive)
```

**Rough cost multipliers (vs us-east-1):**
- ap-south-1 (Mumbai): 1.0x (cheapest in Asia)
- us-east-1: 1.0x (baseline)
- eu-west-1: 1.1x
- ap-southeast-1 (Singapore): 1.15x
- sa-east-1 (São Paulo): 1.25x

---

## Savings Plans vs On-Demand

### Growth tier with Savings Plans

**On-Demand:**
```
2 t3.large EC2 with 50GB, RDS MySQL db.m5.large, 500GB S3, ALB
```

**1-Year Savings Plan:**
```
2 t3.large EC2 with 50GB 1-year savings plan, RDS MySQL db.m5.large, 500GB S3, ALB
```

**3-Year Savings Plan:**
```
2 t3.large EC2 with 50GB 3-year savings plan, RDS MySQL db.m5.large, 500GB S3, ALB
```

Compare the three links to see the discount (~20% for 1yr, ~35% for 3yr on compute).

---

## Disaster Recovery / Backup

### Standard backup strategy
```
RDS MySQL db.m5.large 100GB Multi-AZ with daily backup 30-day retention,
EBS volume 500GB with daily snapshots,
S3 bucket 1TB with versioning
```

### AWS DRS (Elastic Disaster Recovery) setup
```
AWS DRS 10 source servers, 4 disks each, 500GB storage per server, 5% daily change rate, 30-day retention, 20% using larger instance types
```

### Cross-region replication
```
S3 bucket 5TB with cross-region replication enabled,
RDS Aurora with read replicas in 2 additional regions,
DynamoDB global tables (replication)
```

---

## Networking & Security

### VPC with NAT and VPN
```
VPC with 2 NAT Gateways 500GB data/mo, 
Site-to-Site VPN 1 connection 24hrs/day,
Transit Gateway with 3 attachments 100GB data/mo,
PrivateLink 2 VPC endpoints 50GB data/mo,
Network Firewall 2 endpoints 10GB data/mo,
WAF 1 Web ACL 10 rules 10M requests
```

### Secure Kubernetes cluster
```
EKS cluster 3 nodes m5.large,
NAT Gateway 1 gateway 100GB data/mo,
API Gateway with WAF 1 ACL 5 rules 1M requests,
KMS 5 customer-managed keys,
Secrets Manager 10 secrets,
GuardDuty enabled,
CloudTrail with log validation
```

---

## Auto-Scaling Scenarios

### Variable workload (8 hours/day peak)
```
2 t3.medium EC2 base 24/7, 
4 t3.medium EC2 additional 8 hours/day,
RDS MySQL db.m5.large Multi-AZ always on,
DynamoDB 100 RCU 50 WCU provisioned
```

### Batch processing (weekends only)
```
10 m5.large EC2 runs 20 hours on Saturday, 20 hours on Sunday,
RDS PostgreSQL db.m5.large Multi-AZ always on,
S3 1TB always on,
Lambda 500M requests on weekends only 512MB
```

### Scheduled analytics (monthly full scan)
```
5 m5.2xlarge EC2 runs 4 hours on the 1st of each month,
Redshift cluster 5 nodes runs 8 hours on the 1st,
Athena 100GB scanned on the 1st,
RDS PostgreSQL always-on db.m5.large
```

---

## Cost Optimization Examples

### Before (naive) vs After (optimized)

**Naive:**
```
5 m5.large EC2 with 100GB each, RDS db.m5.large, DynamoDB on-demand
```

**Optimized:**
```
3 t3.large EC2 with 50GB each, 1-year savings plan,
RDS db.t3.large (same workload, smaller instance), DynamoDB provisioned
```

Compare the two estimates to see potential savings.

---

## Template: Create Your Own

Copy this template and fill in your values:

```
[COUNT] [INSTANCE_TYPE] EC2 with [STORAGE_GB]GB [OPTIONAL: FREQUENCY snapshot],
RDS [ENGINE] db.[TYPE] [STORAGE_GB]GB [OPTIONAL: Multi-AZ],
Lambda [REQUESTS]M requests [MEMORY_MB]MB,
S3 [STORAGE_GB]GB,
[OTHER SERVICES]
```

Then run:
```bash
aws-calc --prompt "your estimate"
```

---

## Tips for Better Estimates

1. **Use exact AWS instance types if you know them:** `t3.large`, `m5.xlarge`, `db.r6g.large`, `cache.r6g.large`
2. **Always include units:** `500GB`, `10M requests`, `100 metrics`, not just `500` or `10` or `100`
3. **Separate services with commas:** Not `EC2 and RDS and S3` but `EC2, RDS, S3`
4. **If the tool doesn't understand, ask Claude/Cursor to rewrite:** "Rewrite this as a comma-separated infrastructure list for AWS cost estimation"
5. **After generating the link, open it and verify:** Check that costs are non-zero and breakdown makes sense

---

## Getting Help

- **Prompt not working?** See `FAQ.md` → Parser tips
- **Service not available?** See `README.md` → Supported services, or file an issue
- **Want to add custom services?** See `CONTRIBUTING.md`
