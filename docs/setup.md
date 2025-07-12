# Setup Guide

This guide provides detailed instructions for setting up Code Researcher in your environment.

## Prerequisites

### System Requirements
- **Python**: 3.11 or higher
- **Operating System**: Linux, macOS, or Windows with WSL
- **Memory**: Minimum 4GB RAM, recommended 8GB+
- **Storage**: At least 2GB free space

### Required Tools
- **Git**: Version control system
- **ctags**: Code indexing tool for symbol analysis
- **Docker**: Container runtime (optional but recommended)
- **curl**: For testing API endpoints

### AWS Requirements
- **AWS Account** with appropriate permissions
- **AWS Bedrock Access** with Claude 4.0 Sonnet enabled
- **AWS CLI** configured with credentials
- **IAM Permissions** for:
  - Bedrock model access
  - SNS topic creation and management
  - CloudWatch alarm configuration

### VCS Requirements
- **GitHub Personal Access Token** with repo permissions
- **GitLab Access Token** (if using GitLab)

## Installation Methods

### Method 1: Automated Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/code-researcher.git
   cd code-researcher
   ```

2. **Run the setup script**
   ```bash
   ./scripts/setup.sh
   ```

   This script will:
   - Check system dependencies
   - Create Python virtual environment
   - Install all required packages
   - Create configuration file
   - Run initial tests

### Method 2: Manual Setup

1. **Clone and navigate**
   ```bash
   git clone https://github.com/your-org/code-researcher.git
   cd code-researcher
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

4. **Create configuration**
   ```bash
   cp config/config.yaml.example config/config.yaml
   ```

### Method 3: Docker Setup

1. **Clone repository**
   ```bash
   git clone https://github.com/your-org/code-researcher.git
   cd code-researcher
   ```

2. **Create configuration**
   ```bash
   cp config/config.yaml.example config/config.yaml
   # Edit config.yaml with your settings
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

## Configuration

### AWS Configuration

1. **Configure AWS CLI**
   ```bash
   aws configure
   ```
   
   Or set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=your-access-key
   export AWS_SECRET_ACCESS_KEY=your-secret-key
   export AWS_DEFAULT_REGION=us-east-1
   ```

2. **Enable Bedrock Models**
   - Go to AWS Bedrock Console
   - Navigate to "Model access"
   - Request access to Claude 4.0 Sonnet
   - Wait for approval (usually immediate)

3. **Create SNS Topic**
   ```bash
   aws sns create-topic --name code-researcher-alerts
   ```

### GitHub Configuration

1. **Create Personal Access Token**
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate new token with `repo` permissions
   - Copy the token

2. **Configure Repository Access**
   - Ensure token has access to target repositories
   - For organizations, may need admin approval

### Application Configuration

Edit `config/config.yaml`:

```yaml
# AWS Configuration
aws:
  region: us-east-1
  bedrock_model: anthropic.claude-sonnet-4-20250514-v1:0

# Alert Sources
alerts:
  cloudwatch:
    enabled: true
    sns_topic_arn: arn:aws:sns:us-east-1:YOUR-ACCOUNT:code-researcher-alerts
    webhook_url: https://your-domain.com/webhook/cloudwatch

# Version Control
vcs:
  github:
    access_token: your-github-token
    repositories:
      - owner: your-org
        name: your-repo
        branch: main
        alert_keywords: ["error", "exception", "crash", "timeout"]
        file_patterns: ["**/*.py", "**/*.js", "**/*.java", "**/*.go"]
        priority: high

# Server Settings
server:
  host: 0.0.0.0
  port: 8000
  debug: false

# Logging
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

## Verification

### Test Installation

1. **Run health check**
   ```bash
   # Start the server
   python -m src.api.webhook_server
   
   # In another terminal, test health endpoint
   curl http://localhost:8000/health
   ```

2. **Run test suite**
   ```bash
   pytest tests/ -v
   ```

3. **Test alert processing**
   ```bash
   curl -X POST http://localhost:8000/test/alert \
     -H "Content-Type: application/json" \
     -d '{
       "Type": "Notification",
       "Message": "{\"AlarmName\":\"TestAlarm\",\"MetricName\":\"ErrorRate\",\"Namespace\":\"AWS/Lambda\",\"NewStateValue\":\"ALARM\",\"NewStateReason\":\"Test alert for setup verification\"}"
     }'
   ```

### Verify AWS Integration

1. **Test Bedrock access**
   ```bash
   aws bedrock list-foundation-models --region us-east-1
   ```

2. **Test SNS topic**
   ```bash
   aws sns list-topics --region us-east-1
   ```

### Verify GitHub Integration

1. **Test GitHub token**
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
   ```

2. **Test repository access**
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/repos/YOUR_ORG/YOUR_REPO
   ```

## Troubleshooting

### Common Issues

1. **Python version error**
   ```bash
   # Check Python version
   python3 --version
   
   # Install Python 3.11+ if needed
   # Ubuntu/Debian: sudo apt install python3.11
   # macOS: brew install python@3.11
   ```

2. **Missing system dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install git ctags curl
   
   # macOS
   brew install git ctags curl
   ```

3. **AWS permissions error**
   - Check IAM permissions for Bedrock and SNS
   - Verify AWS credentials are configured
   - Ensure Bedrock model access is approved

4. **GitHub token issues**
   - Verify token has correct permissions
   - Check token hasn't expired
   - Ensure repository access is granted

### Getting Help

- Check [Common Issues](troubleshooting/common-issues.md)
- Review [FAQ](troubleshooting/faq.md)
- Open an [issue](https://github.com/your-org/code-researcher/issues)
- Join [discussions](https://github.com/your-org/code-researcher/discussions)

## Next Steps

After successful setup:

1. [Configure CloudWatch Integration](integrations/cloudwatch.md)
2. [Set up GitHub Repositories](integrations/github.md)
3. [Review API Documentation](api/reference.md)
4. [Explore Examples](examples/configurations.md)
