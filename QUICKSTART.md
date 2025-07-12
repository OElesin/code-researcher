# Code Researcher - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites

- Python 3.11+
- AWS Account with Bedrock access (Claude 4.0 Sonnet enabled)
- GitHub Personal Access Token
- Git and ctags installed

### Step 1: Setup

```bash
# Run the setup script
./scripts/setup.sh
```

This will:
- Check system dependencies
- Create virtual environment
- Install Python packages
- Create configuration file
- Run tests

### Step 2: Configure

Edit `config/config.yaml`:

```yaml
aws:
  region: us-east-1
  bedrock_model: anthropic.claude-sonnet-4-20250514-v1:0

alerts:
  cloudwatch:
    enabled: true
    sns_topic_arn: "arn:aws:sns:us-east-1:YOUR-ACCOUNT:code-researcher-alerts"

vcs:
  github:
    access_token: "your-github-token"
    repositories:
      - owner: "your-org"
        name: "your-repo"
        branch: "main"
        alert_keywords: ["error", "exception", "crash"]
```

### Step 3: AWS Setup

```bash
# Configure AWS credentials
aws configure

# Create SNS topic for alerts
aws sns create-topic --name code-researcher-alerts

# Subscribe webhook (replace with your domain)
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:YOUR-ACCOUNT:code-researcher-alerts \
  --protocol https \
  --notification-endpoint https://your-domain.com/webhook/cloudwatch
```

### Step 4: Start the Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
python -m src.api.webhook_server

# Or with Docker
docker-compose up
```

### Step 5: Test

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test with sample alert
curl -X POST http://localhost:8000/test/alert \
  -H "Content-Type: application/json" \
  -d '{
    "Type": "Notification",
    "Message": "{\"AlarmName\":\"TestAlarm\",\"MetricName\":\"ErrorRate\",\"Namespace\":\"AWS/Lambda\",\"NewStateValue\":\"ALARM\",\"NewStateReason\":\"Test alert\"}"
  }'
```

## 🔧 Development

### Run Tests
```bash
pytest tests/ -v
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type check
mypy src/
```

### Debug Mode
```bash
python -m src.api.webhook_server --reload --debug
```

## 📊 Monitoring

- **Health Check**: `GET /health`
- **Job Status**: `GET /status/{job_id}`
- **List Jobs**: `GET /jobs`
- **Logs**: Check `logs/` directory

## 🐛 Troubleshooting

### Common Issues

1. **Import Error**: Make sure virtual environment is activated
2. **AWS Permissions**: Ensure Bedrock access is enabled
3. **GitHub Token**: Check token has repo access
4. **Dependencies**: Run `./scripts/setup.sh` again

### Debug Steps

1. Check logs in `logs/` directory
2. Verify configuration in `config/config.yaml`
3. Test AWS credentials: `aws sts get-caller-identity`
4. Test GitHub token: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user`

## 📚 Next Steps

- Read the full [README.md](README.md)
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for development
- Review the [technical implementation plan](Code-Researcher-Open-Source-Plan.md)
- Join our [GitHub Discussions](https://github.com/your-org/code-researcher/discussions)

## 🆘 Need Help?

- 📖 [Documentation](docs/)
- 💬 [GitHub Discussions](https://github.com/your-org/code-researcher/discussions)
- 🐛 [Issue Tracker](https://github.com/your-org/code-researcher/issues)

Happy coding! 🤖
