# personalized-aws-features

Ever missed a critical AWS feature release for a service you actually use, while being bombarded with updates about Amazon Chime or Sumerian that you'll never touch? Suffering from AWS announcement fatigue?

This project attempts to cut through the noise by analyzing your actual AWS usage through Cost Explorer data, fetching recent AWS announcements, and using Amazon Bedrock (Default: Amazon Nova Lite) to determine which announcements are relevant to your services. It helps you stay informed about updates that matter to your specific AWS environment without drowning in a sea of irrelevant feature releases. Notifications can be viewed in the CLI or sent directly to a Slack channel.

*AI (LLM) responses are still not perfect - as anyone who actively uses them is well aware.

## Table of Contents
- [personalized-aws-features](#personalized-aws-features)
  - [Table of Contents](#table-of-contents)
  - [Architecture](#architecture)
    - [CLI](#cli)
    - [Lambda](#lambda)
  - [Features](#features)
  - [Prerequisites](#prerequisites)
  - [Configuration Parameters](#configuration-parameters)
  - [Installation](#installation)
    - [Poetry](#poetry)
    - [CLI Usage](#cli-usage)
    - [Lambda Deployment](#lambda-deployment)
  - [Setting Up Slack Integration](#setting-up-slack-integration)
  - [Development](#development)
    - [Running Tests](#running-tests)
    - [Formatting and Linting](#formatting-and-linting)
  - [Cost Implications](#cost-implications)
  - [License](#license)

## Architecture
*Dotted lines are optional flows.

### CLI
![CLI Architecture](./assets/cli-arch.png)

### Lambda
![Lambda Architecture](./assets/lambda-arch.png)

## Features

- **Service Usage Detection**: Automatically identifies AWS services you're using via Cost Explorer (supports single accounts or all accounts running under consolidated billing)
- **AI (LLM) Filtering**: Uses Amazon Bedrock to analyze and determine announcement relevance
- **Deduplication**: Optionally tracks previously seen announcements in DynamoDB to avoid duplicate announcements upon rerun
- **Flexible Deployment**: Run as a CLI tool (which can then run on Cron, etc.) or deploy as an AWS Lambda function (runs daily by default but is configurabe)
- **Infrastructure as Code**: Complete Terraform configuration for AWS deployment with options for Lambda deployment, scheduled runs via EventBridge, DyanmoDB persistence, CloudWatch Alarms and more

## Prerequisites

- Python ` >=3.13 `
- AWS account with appropriate permissions
- AWS CLI configured with credentials
- [Amazon Nova Lite](https://docs.aws.amazon.com/nova/latest/userguide/what-is-nova.html) (`amazon.nova-lite-v1:0`) enabled in `us-east-1`
  - Other Bedrock models and regions can be modified via CLI/Lambda but have not been tested!
- [Poetry](https://python-poetry.org/docs/) for dependency management
- [Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli) (for infrastructure deployment)

*This installation will assume everything will be deployed to `us-east-1`, however most of this can be reconfigured (aside from Cost Explorer which is hard coded for `us-east-1`).

## Configuration Parameters

| CLI Parameter | Lambda Env Var | Description | Default Value |
| --- | --- | --- | --- |
| `--days` | `DAYS_BACK` | Number of days to look back for announcements | `7` |
| `--region` | `APP_AWS_REGION` | AWS region for all resources | `us-east-1` |
| `--model` | `BEDROCK_MODEL` | Bedrock model ID to use | `amazon.nova-lite-v1:0` |
| `--ddb-table` | `DDB_TABLE` | DynamoDB table name | `personalized-aws-features` |
| `--no-history` | `NO_HISTORY` | Disable tracking of seen announcements | `false` |
| `--slack-token` | `SLACK_TOKEN` | Slack API token for notifications | `""` |
| `--slack-channel` | `SLACK_CHANNEL` | Slack channel for notifications | `""` |
| `--slack-enabled` | `SLACK_ENABLED` | Enable Slack integration | `false` (CLI), `true` (Lambda) |
| `--workers` | `MAX_WORKERS` | Number of parallel workers | `10` |
| `--verbose`, `-v` | `VERBOSE` | Enable detailed output | `false` (CLI), `true` (Lambda) |
| `--log-level` | `LOG_LEVEL` | Logging level | `INFO` |

## Installation

### Poetry

```bash
# Clone the repository
git clone https://github.com/moebaca/personalized-aws-features.git
cd personalized-aws-features

# Install dependencies
poetry install
```

### CLI Usage

Please make sure to set your AWS config to use the `us-east-1` region (if you have not changed project defaults).

**Required AWS Permissions**

Unlike the Lambda deploy which creates all required permissions via IaC - the CLI requires the caller to have the below permissions:

- `ce:GetCostAndUsage` for Cost Explorer
- `bedrock:InvokeModel` for Amazon Bedrock
- `dynamodb:PutItem`, `dynamodb:GetItem`, `dynamodb:DescribeTable` on generated table for DynamoDB access (if using history tracking)

💿 ❌ **Without announcement persistence**

To get a quick idea if you like the tool output before setting up Slack integration, announcement persistence, and Lambda deploy - you can run the below command:

```bash
personalized-aws-features --verbose --no-history
```

Example output:
![CLI Output](./assets/cli-output.png)

💿 ✅ **With announcement persistence**

Announcement persistence requires a DyanmoDB table to track seen announcements. This has been automated in Terraform with the instruction below:

Edit [variables.tf](./terraform/variables.tf) to customize your deployment:

```hcl
create_dynamodb   = true # This is default
create_lambda     = false # Be sure to set this to false
```

Deploy DynamoDB using Terraform:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

You should obviously setup your own backend for `tfstate`, but the default does not include one for deployment simplicity (`tfstate` is local).

You can now test announcement persistence by running the same command twice and observing announcement filtering:

```bash
personalized-aws-features --verbose
```

See the *Setting Up Slack Integration* section below for Slack integration.

### Lambda Deployment

Lambda deployment allows the program to run on Cron via EventBridge. All permissions are handled by a Role. CloudWatch Alarms, SNS notifications application deployment to Lambda (zip) and more are all handled below.

**Building the Lambda Package**

The below script:
1. Creates a temporary build directory
2. Installs dependencies
3. Packages everything into a Lambda deployment zip

This is required to run before deploying the Terraform.

```bash
# From project root
./build_lambda.sh
```

**Infrastructure Variables**

Edit [variables.tf](./terraform/variables.tf) to customize your deployment:

```hcl
aws_region        = "us-east-1"
create_dynamodb   = true
create_lambda     = true
days_back         = 7
slack_enabled     = true
slack_token       = "xoxb-your-token-here"
slack_channel     = "#your-channel"
alarm_email       = "your@email.com"
```

See the *Setting Up Slack Integration* section below for Slack integration.

**Deploy using Terraform**

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

**Testing Lambda**

You can either wait until the next scheduled run (`cron(0 12 * * ? *)`) or [manually test the Lambda](https://docs.aws.amazon.com/lambda/latest/dg/testing-functions.html).

Example Output in CloudWatch Logs:
![Lambda Logs Output](./assets/lambda-output.png)

**CloudWatch Alarm and Notifications**

When deploying the Lambda function, a CloudWatch alarm is automatically created to monitor for Lambda execution errors. If the Lambda function encounters any errors:

1. The CloudWatch alarm will trigger
2. An SNS notification will be sent
3. If you provided an `alarm_email` in your Terraform variables, you'll receive an email notification

Be sure to approve the email or you will not receive alerts.

## Setting Up Slack Integration

1. **Create a Slack App**:
   - Go to [https://api.slack.com/apps](https://api.slack.com/apps)
   - Click "Create New App" and choose "From scratch"
   - Name your app (e.g., "AWS Feature Notifier")
   - Select your workspace

2. **Configure App Permissions**:
   - Navigate to "OAuth & Permissions"
   - Add these Bot Token Scopes:
     - `chat:write`
     - `chat:write.public`
   - Install the app to your workspace

3. **Get Bot Token**:
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)
   - Use this token with the `--slack-token` option or in `slack_token` Terraform variable

4. **Invite Bot to Channel**:
   - Create or choose a channel for notifications
   - Use this token with the `--slack-channel` option or in `slack_channel` Terraform variable
   - Invite the bot to the channel with `/invite @aws-feature-notifier`

You can now test the notification delivery via CLI or Lambda invocation:

```bash
# CLI example
personalized-aws-features --slack-enabled --slack-token "xoxb-xxxxx-xxxxxx-xxxxx" --slack-channel "#your-slack-channel" -v 
```

Example Output in Slack:
![Slack Output](./assets/slack-output.png)

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest
```

### Formatting and Linting

```bash
# Format code
poetry run black .

# Run linter
poetry run flake8 --max-line-length=127
```

## Cost Implications

This solution costs pennies a day to run. Due to the cost-effective pricing of Amazon Bedrock, even the heaviest day of development only cost approximately $0.68. Daily operational costs are now roughly $0.05.

![Slack Output](./assets/cost-explorer.png)

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE.txt) file for details.