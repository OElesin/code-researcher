# Code Researcher 
Inspired by [Microsoft Code Researcher White Paper](https://arxiv.org/abs/2506.11060) 🤖

An open source AI-powered platform that automatically investigates bugs and creates fix proposals using AWS Strands Agents.

## Overview

Code Researcher automatically:
1. **Receives alerts** from monitoring tools (CloudWatch, DataDog, New Relic)
2. **Identifies relevant repositories** from configured VCS systems (GitHub, GitLab)
3. **Performs intelligent code research** using specialized AI agents
4. **Creates pull requests** with proposed fixes for engineer review

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Code Researcher System                      │
├─────────────────┬───────────────────┬─────────────────────┤
│ Alert Handler   │   Research Agent  │   Fix Generator     │
│ (CloudWatch)    │   (AI Analysis)   │   (PR Creation)     │
└─────────────────┴───────────────────┴─────────────────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
    ┌────────────────────────┼────────────────────────┐
    │                        │                        │
┌───────────┐    ┌──────────────────┐    ┌─────────────────┐
│VCS Tools  │    │  Analysis Tools  │    │ AI/ML Services  │
│(GitHub/   │    │  (Code Search)   │    │   (AWS Bedrock) │
│ GitLab)   │    │                  │    │                 │
└───────────┘    └──────────────────┘    └─────────────────┘
```

## Features

- 🔍 **Intelligent Code Analysis**: AI-powered deep code research using AWS Strands Agents
- 🚨 **Multi-Platform Alerts**: CloudWatch, DataDog, New Relic integration
- 🔧 **VCS Integration**: GitHub and GitLab support with automatic PR creation
- 🤖 **Agent-Based Architecture**: Specialized AI agents for analysis and synthesis
- 📊 **Real-time Monitoring**: Job tracking and status APIs
- 🐳 **Docker Ready**: Easy deployment with Docker Compose

## Quick Start

### Prerequisites

- Python 3.11+
- AWS account with Bedrock access (Claude 4.0 Sonnet enabled)
- GitHub/GitLab access tokens
- Git and ctags installed

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/code-researcher.git
   cd code-researcher
   ```

2. **Set up configuration**
   ```bash
   cp config/config.yaml.example config/config.yaml
   # Edit config.yaml with your settings
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run with Docker**
   ```bash
   docker-compose up -d
   ```

### Configuration

Edit `config/config.yaml` with your settings:

```yaml
aws:
  region: us-east-1
  bedrock_model: anthropic.claude-sonnet-4-20250514-v1:0

alerts:
  cloudwatch:
    enabled: true
    sns_topic_arn: your-sns-topic-arn

vcs:
  github:
    access_token: your-github-token
    repositories:
      - owner: your-org
        name: your-repo
        branch: main
```

## Usage

### CloudWatch Integration

1. Create SNS topic for alerts
2. Subscribe Code Researcher webhook to the topic
3. Configure CloudWatch alarms to publish to the topic

```bash
aws sns create-topic --name code-researcher-alerts
aws sns subscribe --topic-arn arn:aws:sns:us-east-1:123456789:code-researcher-alerts \
  --protocol https --notification-endpoint https://your-domain.com/webhook/cloudwatch
```

### API Endpoints

- `POST /webhook/cloudwatch` - Receive CloudWatch alerts
- `GET /status/{job_id}` - Check job status
- `GET /health` - Health check

## Development

### Setup Development Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Run Tests

```bash
pytest tests/
```

### Start Development Server

```bash
python -m src.api.webhook_server --reload
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](docs/)
- 💬 [GitHub Discussions](https://github.com/your-org/code-researcher/discussions)
- 🐛 [Issue Tracker](https://github.com/your-org/code-researcher/issues)

## Roadmap

- [x] CloudWatch integration
- [x] GitHub integration
- [x] AWS Strands Agents
- [ ] GitLab integration
- [ ] DataDog integration
- [ ] New Relic integration
- [ ] Web UI
- [ ] Metrics dashboard

---

Built with ❤️ using AWS Strands Agents
