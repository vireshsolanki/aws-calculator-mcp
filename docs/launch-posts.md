# Launch Posts

Use these when announcing `aws-calculator-mcp` v1.3.4. Replace the repository URL if needed.

Repository: https://github.com/vireshsolanki/aws-calculator-mcp
PyPI: https://pypi.org/project/aws-calculator-mcp/

## LinkedIn

I open-sourced a small tool I have been building: **AWS Calculator MCP**.

It lets you describe AWS infrastructure in plain English and get an official AWS Pricing Calculator link with costs already computed.

Examples:

- "2 t3.large EC2 with 50GB, RDS MySQL db.m5.large 100GB, 500GB S3, an ALB"
- "Hyderabad DR with EDR, EC2 drill servers, VPC networking, and data transfer"
- "Lambda with 10M requests, DynamoDB, API Gateway, 200GB S3"

It works as:

- an MCP server for Claude, Cursor, and other AI IDEs
- a CLI
- an optional REST API

The latest release focuses on correctness:

- cleaner AWS Pricing Calculator payloads
- no empty optional transfer sections
- default EC2 boot storage for plain-English prompts
- fixed Aurora node parsing
- better DRS/EDR and AWS Data Transfer support
- regression tests for the parser and service builders

I am making it open source because AWS cost estimation should be easier to validate, share, and improve. If you work with AWS, FinOps, DevOps, infra planning, or AI agents, please try it and share feedback.

GitHub: https://github.com/vireshsolanki/aws-calculator-mcp
PyPI: https://pypi.org/project/aws-calculator-mcp/

Feedback welcome via GitHub issues.

## Reddit

Title:

Open-sourced an MCP server that turns plain English AWS infra into official AWS Pricing Calculator links

Post:

I built and open-sourced **AWS Calculator MCP**.

It lets you describe AWS infrastructure in plain English and returns an official AWS Pricing Calculator link with costs already computed.

It can run as:

- MCP server for Claude/Cursor/AI IDEs
- CLI
- REST API

Example prompt:

```text
2 t3.large EC2 with 50GB, RDS MySQL db.m5.large 100GB, 500GB S3, an ALB
```

It returns a shareable `calculator.aws` estimate link that you can open and verify.

The new release fixes several real calculator edge cases:

- EC2 default boot storage
- Aurora node counts
- DRS/EDR payloads
- AWS Data Transfer
- empty transfer sections in generated calculator payloads
- baked non-zero calculator links in docs

Repo:
https://github.com/vireshsolanki/aws-calculator-mcp

PyPI:
https://pypi.org/project/aws-calculator-mcp/

I am looking for feedback from AWS/DevOps/FinOps folks. If you can break the parser or find wrong calculator payloads, please open an issue. The goal is to make this a useful MCP tool for everyone estimating AWS costs from AI workflows.

Suggested subreddits:

- r/aws
- r/devops
- r/finops
- r/selfhosted, only if positioning around local tools
- r/Python
- r/opensource
- r/ClaudeAI or r/cursor, if allowed by rules

Check each subreddit rules before posting. Some communities prefer a "Show HN-style" technical post and dislike launch language.

## X / Twitter

Open-sourced AWS Calculator MCP.

Describe AWS infra in plain English -> get an official AWS Pricing Calculator link with real costs baked in.

Works as MCP server, CLI, or REST API.

Latest release fixes DRS/EDR, data transfer, EC2 storage defaults, Aurora nodes, and adds regression tests.

GitHub: https://github.com/vireshsolanki/aws-calculator-mcp
PyPI: https://pypi.org/project/aws-calculator-mcp/

Feedback welcome.

## Short X / Twitter

I open-sourced AWS Calculator MCP.

Plain English AWS infra -> official calculator.aws link with computed costs.

MCP server + CLI + REST API.

Try it, break it, send feedback:
https://github.com/vireshsolanki/aws-calculator-mcp

## Where To Share

- GitHub README and repo topics
- PyPI project page
- LinkedIn
- X / Twitter
- Reddit: r/aws, r/devops, r/finops, r/Python, r/opensource
- Hacker News: "Show HN: AWS Calculator MCP..."
- Product Hunt, if you want broader visibility
- Dev.to or Hashnode for a technical walkthrough
- AWS / FinOps Slack or Discord communities where self-promotion is allowed
- Cursor / Claude / MCP communities

## Feedback CTA

Best call to action:

> Try it with a real AWS architecture you know. If the generated calculator link is wrong, open a GitHub issue with the prompt and expected calculator behavior.

