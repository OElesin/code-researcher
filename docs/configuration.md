# Configuration Guide

This guide covers all configuration options available in Code Researcher.

## Configuration File Structure

Code Researcher uses a YAML configuration file located at `config/config.yaml`. The configuration is organized into several sections:

```yaml
aws:           # AWS and Bedrock settings
alerts:        # Alert source configurations
vcs:           # Version control system settings
server:        # Web server configuration
logging:       # Logging configuration
```

## AWS Configuration

### Basic AWS Settings

```yaml
aws:
  region: us-east-1                                    # AWS region
  bedrock_model: anthropic.claude-sonnet-4-20250514-v1:0  # Bedrock model ID
```

**Options:**
- `region`: AWS region where Bedrock is available (default: `us-east-1`)
- `bedrock_model`: Claude model to use for AI analysis

**Supported Models:**
- `anthropic.claude-sonnet-4-20250514-v1:0` (recommended)
- `anthropic.claude-3-5-sonnet-20241022-v2:0`
- `anthropic.claude-3-haiku-20240307-v1:0`

## Alert Configuration

### CloudWatch Alerts

```yaml
alerts:
  cloudwatch:
    enabled: true                                        # Enable CloudWatch integration
    sns_topic_arn: arn:aws:sns:us-east-1:123:alerts    # SNS topic ARN
    webhook_url: https://your-domain.com/webhook/cloudwatch  # Webhook URL
    topic_name: code-researcher-alerts                  # SNS topic name
    ignore_patterns:                                    # Patterns to ignore
      - "test-alarm"
      - "dev-environment"
```

**Options:**
- `enabled`: Enable/disable CloudWatch integration
- `sns_topic_arn`: ARN of SNS topic for alerts
- `webhook_url`: Public URL for webhook endpoint
- `topic_name`: Name for SNS topic creation
- `ignore_patterns`: List of alarm name patterns to ignore

### DataDog Alerts (Future)

```yaml
alerts:
  datadog:
    enabled: false
    api_key: your-datadog-api-key
    webhook_url: https://your-domain.com/webhook/datadog
```

### New Relic Alerts (Future)

```yaml
alerts:
  newrelic:
    enabled: false
    api_key: your-newrelic-api-key
    webhook_url: https://your-domain.com/webhook/newrelic
```

## VCS Configuration

### GitHub Integration

```yaml
vcs:
  github:
    access_token: ghp_your_token_here                   # GitHub personal access token
    repositories:                                       # List of repositories to monitor
      - owner: your-org                                 # Repository owner
        name: backend-service                           # Repository name
        branch: main                                    # Default branch
        alert_keywords:                                 # Keywords for relevance matching
          - "error"
          - "exception"
          - "crash"
          - "timeout"
        file_patterns:                                  # File patterns to analyze
          - "**/*.py"
          - "**/*.js"
          - "**/*.java"
          - "**/*.go"
        priority: high                                  # Repository priority (low/medium/high)
      - owner: your-org
        name: frontend-app
        branch: develop
        alert_keywords:
          - "javascript"
          - "react"
          - "ui"
          - "frontend"
        file_patterns:
          - "**/*.js"
          - "**/*.jsx"
          - "**/*.ts"
          - "**/*.tsx"
        priority: medium
```

**Repository Options:**
- `owner`: GitHub username or organization name
- `name`: Repository name
- `branch`: Default branch to analyze (default: `main`)
- `alert_keywords`: Keywords for matching alerts to repositories
- `file_patterns`: Glob patterns for files to analyze
- `priority`: Repository priority for relevance scoring

**File Pattern Examples:**
- `**/*.py` - All Python files
- `src/**/*.js` - JavaScript files in src directory
- `*.{java,kt}` - Java and Kotlin files in root
- `!test/**` - Exclude test directories

### GitLab Integration

```yaml
vcs:
  gitlab:
    enabled: true
    access_token: glpat_your_token_here                 # GitLab access token
    base_url: https://gitlab.com                        # GitLab instance URL
    repositories:
      - owner: your-group
        name: your-project
        branch: main
        alert_keywords: ["error", "bug"]
        file_patterns: ["**/*.py", "**/*.go"]
        priority: high
```

**GitLab Options:**
- `base_url`: GitLab instance URL (use your self-hosted URL if applicable)
- Other options same as GitHub

## Server Configuration

```yaml
server:
  host: 0.0.0.0                                        # Server bind address
  port: 8000                                           # Server port
  debug: false                                         # Enable debug mode
  workers: 1                                           # Number of worker processes
  reload: false                                        # Enable auto-reload (development)
```

**Options:**
- `host`: IP address to bind to (`0.0.0.0` for all interfaces)
- `port`: Port number for the web server
- `debug`: Enable debug logging and error details
- `workers`: Number of worker processes (for production)
- `reload`: Enable auto-reload on code changes (development only)

## Logging Configuration

```yaml
logging:
  level: INFO                                          # Log level
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # Log format
  file: logs/code-researcher.log                       # Log file path
  max_size: 10MB                                       # Max log file size
  backup_count: 5                                      # Number of backup files
```

**Log Levels:**
- `DEBUG`: Detailed debugging information
- `INFO`: General information (recommended)
- `WARNING`: Warning messages only
- `ERROR`: Error messages only
- `CRITICAL`: Critical errors only

**Log Format Variables:**
- `%(asctime)s`: Timestamp
- `%(name)s`: Logger name
- `%(levelname)s`: Log level
- `%(message)s`: Log message
- `%(filename)s`: Source filename
- `%(lineno)d`: Line number

## Environment Variables

You can override configuration values using environment variables:

```bash
# AWS Configuration
export AWS_DEFAULT_REGION=us-west-2
export BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-20250514-v1:0

# GitHub Configuration
export GITHUB_ACCESS_TOKEN=your_token_here

# Server Configuration
export SERVER_HOST=127.0.0.1
export SERVER_PORT=9000
export DEBUG=true

# Logging
export LOG_LEVEL=DEBUG
```

**Environment Variable Naming:**
- Use uppercase
- Replace dots with underscores
- Prefix with section name: `AWS_REGION`, `GITHUB_ACCESS_TOKEN`, etc.

## Configuration Validation

Code Researcher validates configuration on startup:

```python
# Example validation errors
ConfigurationError: AWS region not specified
ConfigurationError: GitHub access token is required
ConfigurationError: No repositories configured
ConfigurationError: Invalid Bedrock model ID
```

### Validation Rules

1. **AWS section is required** with valid region and model
2. **At least one alert source** must be enabled
3. **At least one VCS provider** must be configured
4. **Repository configurations** must have owner and name
5. **Server port** must be between 1024-65535
6. **Log level** must be valid Python logging level

## Configuration Examples

### Minimal Configuration

```yaml
aws:
  region: us-east-1
  bedrock_model: anthropic.claude-sonnet-4-20250514-v1:0

alerts:
  cloudwatch:
    enabled: true
    sns_topic_arn: arn:aws:sns:us-east-1:123456789:alerts

vcs:
  github:
    access_token: your_token
    repositories:
      - owner: myorg
        name: myrepo
        branch: main
```

### Production Configuration

```yaml
aws:
  region: us-east-1
  bedrock_model: anthropic.claude-sonnet-4-20250514-v1:0

alerts:
  cloudwatch:
    enabled: true
    sns_topic_arn: arn:aws:sns:us-east-1:123456789:code-researcher-alerts
    webhook_url: https://code-researcher.company.com/webhook/cloudwatch
    ignore_patterns:
      - "test-*"
      - "dev-*"

vcs:
  github:
    access_token: ghp_production_token
    repositories:
      - owner: company
        name: backend-api
        branch: main
        alert_keywords: ["error", "exception", "timeout", "database"]
        file_patterns: ["**/*.py", "**/*.sql"]
        priority: high
      - owner: company
        name: frontend-web
        branch: main
        alert_keywords: ["javascript", "react", "ui", "frontend"]
        file_patterns: ["src/**/*.{js,jsx,ts,tsx}"]
        priority: medium

server:
  host: 0.0.0.0
  port: 8000
  debug: false
  workers: 4

logging:
  level: INFO
  file: /var/log/code-researcher/app.log
  max_size: 50MB
  backup_count: 10
```

### Development Configuration

```yaml
aws:
  region: us-east-1
  bedrock_model: anthropic.claude-sonnet-4-20250514-v1:0

alerts:
  cloudwatch:
    enabled: true
    sns_topic_arn: arn:aws:sns:us-east-1:123456789:dev-alerts

vcs:
  github:
    access_token: ghp_dev_token
    repositories:
      - owner: myusername
        name: test-repo
        branch: develop
        alert_keywords: ["test", "error"]
        file_patterns: ["**/*.py"]
        priority: low

server:
  host: 127.0.0.1
  port: 8000
  debug: true
  reload: true

logging:
  level: DEBUG
  format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
```

## Security Considerations

### Sensitive Data

- **Never commit tokens** to version control
- **Use environment variables** for sensitive values
- **Rotate tokens regularly**
- **Use least-privilege permissions**

### Token Permissions

**GitHub Token Permissions:**
- `repo`: Full repository access
- `read:org`: Read organization membership (if needed)

**AWS IAM Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sns:CreateTopic",
        "sns:Subscribe",
        "sns:ListTopics"
      ],
      "Resource": "*"
    }
  ]
}
```

## Configuration Management

### Multiple Environments

Use different configuration files:

```bash
# Development
CONFIG_PATH=config/config.dev.yaml python -m src.api.webhook_server

# Staging
CONFIG_PATH=config/config.staging.yaml python -m src.api.webhook_server

# Production
CONFIG_PATH=config/config.prod.yaml python -m src.api.webhook_server
```

### Configuration Templates

Create templates for different use cases:

- `config.minimal.yaml` - Minimal setup
- `config.development.yaml` - Development environment
- `config.production.yaml` - Production environment
- `config.enterprise.yaml` - Enterprise features

## Troubleshooting Configuration

### Common Issues

1. **Invalid YAML syntax**
   ```bash
   python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"
   ```

2. **Missing required fields**
   - Check startup logs for validation errors
   - Ensure all required sections are present

3. **Token authentication failures**
   - Verify token permissions
   - Check token hasn't expired
   - Test token manually with curl

4. **AWS access issues**
   - Verify AWS credentials
   - Check Bedrock model access
   - Ensure correct region

### Validation Tools

```bash
# Validate configuration
python -c "
from src.core.code_researcher_system import CodeResearcherSystem
import yaml
config = yaml.safe_load(open('config/config.yaml'))
system = CodeResearcherSystem(config)
print('Configuration valid!')
"
```
