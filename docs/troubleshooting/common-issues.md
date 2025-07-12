# Common Issues and Solutions

This guide covers the most frequently encountered issues when setting up and running Code Researcher.

## Installation Issues

### Python Version Error

**Problem:**
```
ERROR: Python 3.11+ is required. Found: 3.9.7
```

**Solution:**
```bash
# Check current Python version
python3 --version

# Install Python 3.11+ (Ubuntu/Debian)
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip

# Install Python 3.11+ (macOS)
brew install python@3.11

# Create virtual environment with specific Python version
python3.11 -m venv venv
source venv/bin/activate
```

### Missing System Dependencies

**Problem:**
```
ERROR: git is not installed
ERROR: ctags is not installed
```

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install git ctags curl

# macOS
brew install git ctags curl

# CentOS/RHEL
sudo yum install git ctags curl

# Verify installation
git --version
ctags --version
```

### Virtual Environment Issues

**Problem:**
```
ModuleNotFoundError: No module named 'strands'
```

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Verify you're in the virtual environment
which python
# Should show: /path/to/your/project/venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt

# If still failing, recreate virtual environment
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration Issues

### AWS Configuration Problems

**Problem:**
```
ConfigurationError: AWS region not specified
```

**Solution:**
```bash
# Set AWS region in config file
aws:
  region: us-east-1
  bedrock_model: anthropic.claude-sonnet-4-20250514-v1:0

# Or set environment variable
export AWS_DEFAULT_REGION=us-east-1

# Verify AWS configuration
aws configure list
aws sts get-caller-identity
```

### Bedrock Access Issues

**Problem:**
```
AccessDeniedException: User is not authorized to perform: bedrock:InvokeModel
```

**Solution:**
1. **Enable Bedrock Model Access:**
   - Go to AWS Bedrock Console
   - Navigate to "Model access"
   - Request access to Claude 4.0 Sonnet
   - Wait for approval

2. **Check IAM Permissions:**
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
       }
     ]
   }
   ```

3. **Verify Model Access:**
   ```bash
   aws bedrock list-foundation-models --region us-east-1
   ```

### GitHub Token Issues

**Problem:**
```
github.GithubException.BadCredentialsException: 401 Bad credentials
```

**Solution:**
1. **Check Token Validity:**
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
   ```

2. **Verify Token Permissions:**
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Ensure token has `repo` permissions
   - For organizations, may need admin approval

3. **Update Token in Configuration:**
   ```yaml
   vcs:
     github:
       access_token: ghp_your_new_token_here
   ```

### Configuration File Not Found

**Problem:**
```
FileNotFoundError: Configuration file not found: config/config.yaml
```

**Solution:**
```bash
# Create configuration from example
cp config/config.yaml.example config/config.yaml

# Or specify custom path
export CONFIG_PATH=/path/to/your/config.yaml

# Or use command line argument
python -m src.api.webhook_server --config /path/to/config.yaml
```

## Runtime Issues

### Server Won't Start

**Problem:**
```
OSError: [Errno 98] Address already in use
```

**Solution:**
```bash
# Check what's using the port
lsof -i :8000

# Kill the process using the port
kill -9 PID

# Or use a different port
python -m src.api.webhook_server --port 8001

# Or in configuration
server:
  port: 8001
```

### Import Errors

**Problem:**
```
ModuleNotFoundError: No module named 'src'
```

**Solution:**
```bash
# Ensure you're in the project root directory
pwd
# Should show: /path/to/code-researcher

# Set PYTHONPATH
export PYTHONPATH=/path/to/code-researcher:$PYTHONPATH

# Or run from project root
python -m src.api.webhook_server

# For Docker
docker-compose up --build
```

### Memory Issues

**Problem:**
```
MemoryError: Unable to allocate memory
```

**Solution:**
```bash
# Check available memory
free -h

# Increase Docker memory limits
# In docker-compose.yml:
services:
  code-researcher:
    mem_limit: 4g
    memswap_limit: 4g

# For large repositories, increase timeout
# In configuration:
server:
  timeout: 1800  # 30 minutes
```

## Integration Issues

### CloudWatch Webhook Not Receiving Alerts

**Problem:**
No alerts are being received at the webhook endpoint.

**Solution:**
1. **Check SNS Subscription:**
   ```bash
   aws sns list-subscriptions-by-topic \
     --topic-arn arn:aws:sns:us-east-1:YOUR-ACCOUNT:code-researcher-alerts
   ```

2. **Verify Webhook URL:**
   ```bash
   # Test webhook endpoint
   curl https://your-domain.com/webhook/cloudwatch
   
   # Should return 405 Method Not Allowed (GET not supported)
   # POST should work:
   curl -X POST https://your-domain.com/webhook/cloudwatch \
     -H "Content-Type: application/json" \
     -d '{"Type":"SubscriptionConfirmation"}'
   ```

3. **Check Firewall/Security Groups:**
   - Ensure port 443 (HTTPS) is open
   - Allow SNS IP ranges if using IP filtering

4. **Confirm Subscription:**
   - Check Code Researcher logs for confirmation handling
   - Manually confirm via AWS console if needed

### Repository Not Found

**Problem:**
```
github.UnknownObjectException: 404 Not Found
```

**Solution:**
1. **Check Repository Configuration:**
   ```yaml
   vcs:
     github:
       repositories:
         - owner: correct-owner-name
           name: correct-repo-name
   ```

2. **Verify Repository Access:**
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" \
     https://api.github.com/repos/OWNER/REPO
   ```

3. **Check Organization Permissions:**
   - For organization repos, ensure token has access
   - May need to enable SSO for the token

### No Pull Requests Created

**Problem:**
Analysis completes but no pull requests are created.

**Solution:**
1. **Check Repository Relevance:**
   - Review alert keywords vs repository keywords
   - Check logs for relevance scoring

2. **Verify Analysis Results:**
   ```bash
   # Check job status
   curl http://localhost:8000/status/JOB_ID
   
   # Look for orchestrator_response
   ```

3. **Check Branch Permissions:**
   - Ensure token can create branches
   - Verify branch protection rules don't block automated PRs

## Performance Issues

### Slow Analysis

**Problem:**
Code analysis takes too long or times out.

**Solution:**
1. **Optimize Repository Size:**
   ```yaml
   vcs:
     github:
       repositories:
         - file_patterns:
             - "src/**/*.py"  # Limit to specific directories
             - "!test/**"     # Exclude test files
   ```

2. **Increase Timeouts:**
   ```yaml
   server:
     timeout: 1800  # 30 minutes
   ```

3. **Use Shallow Clones:**
   - Code already uses `depth=1` for git clones
   - Consider excluding large binary files

### High Memory Usage

**Problem:**
System runs out of memory during analysis.

**Solution:**
1. **Limit Concurrent Jobs:**
   ```python
   # In code_researcher_system.py
   MAX_CONCURRENT_JOBS = 2
   ```

2. **Optimize File Processing:**
   ```python
   # Limit file content size
   file_content[:3000]  # Already implemented
   ```

3. **Use Docker Memory Limits:**
   ```yaml
   services:
     code-researcher:
       mem_limit: 2g
       memswap_limit: 2g
   ```

## Debugging Steps

### Enable Debug Logging

```yaml
# In config.yaml
logging:
  level: DEBUG

# Or environment variable
export LOG_LEVEL=DEBUG
```

### Check System Status

```bash
# Health check
curl http://localhost:8000/health

# List active jobs
curl http://localhost:8000/jobs

# Check specific job
curl http://localhost:8000/status/JOB_ID
```

### Review Logs

```bash
# Application logs
tail -f logs/code-researcher.log

# Filter for errors
grep ERROR logs/code-researcher.log

# Filter for specific job
grep JOB_ID logs/code-researcher.log

# Docker logs
docker-compose logs -f code-researcher
```

### Test Components Individually

```bash
# Test AWS connection
python -c "
import boto3
client = boto3.client('bedrock-runtime', region_name='us-east-1')
print('AWS connection OK')
"

# Test GitHub connection
python -c "
import github
g = github.Github('YOUR_TOKEN')
print(g.get_user().login)
"

# Test configuration loading
python -c "
import yaml
config = yaml.safe_load(open('config/config.yaml'))
print('Configuration loaded OK')
"
```

## Getting Help

If you're still experiencing issues:

1. **Check the logs** for detailed error messages
2. **Search existing issues** on GitHub
3. **Create a new issue** with:
   - Error message and stack trace
   - Configuration (remove sensitive data)
   - Steps to reproduce
   - System information (OS, Python version, etc.)

### Issue Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Error message**
```
Paste error message here
```

**Configuration**
```yaml
# Your config.yaml (remove sensitive data)
```

**Environment**
- OS: [e.g. Ubuntu 20.04]
- Python version: [e.g. 3.11.0]
- Code Researcher version: [e.g. 0.1.0]
```

### Useful Commands for Bug Reports

```bash
# System information
uname -a
python3 --version
pip list | grep -E "(strands|boto3|fastapi)"

# Configuration validation
python -c "
import yaml
try:
    config = yaml.safe_load(open('config/config.yaml'))
    print('Configuration is valid YAML')
except Exception as e:
    print(f'Configuration error: {e}')
"

# Network connectivity
curl -I https://bedrock-runtime.us-east-1.amazonaws.com
curl -I https://api.github.com
```
