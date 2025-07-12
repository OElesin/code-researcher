# CloudWatch Integration Guide

This guide covers setting up AWS CloudWatch integration with Code Researcher to automatically receive and process alarm notifications.

## Overview

CloudWatch integration allows Code Researcher to:
- Receive alarm notifications via SNS
- Parse CloudWatch alarm data
- Extract relevant keywords for repository matching
- Trigger automated code analysis when alarms fire

## Architecture

```
CloudWatch Alarm → SNS Topic → Code Researcher Webhook → AI Analysis → GitHub PR
```

## Prerequisites

- AWS account with CloudWatch access
- SNS permissions for topic creation and management
- Public endpoint for webhook (or use ngrok for testing)
- Code Researcher deployed and running

## Setup Steps

### 1. Configure Code Researcher

Edit `config/config.yaml`:

```yaml
alerts:
  cloudwatch:
    enabled: true
    sns_topic_arn: arn:aws:sns:us-east-1:YOUR-ACCOUNT:code-researcher-alerts
    webhook_url: https://your-domain.com/webhook/cloudwatch
    ignore_patterns:
      - "test-*"
      - "dev-*"
```

### 2. Create SNS Topic

```bash
# Create SNS topic
aws sns create-topic --name code-researcher-alerts

# Get topic ARN (save this for configuration)
aws sns list-topics --query 'Topics[?contains(TopicArn, `code-researcher-alerts`)].TopicArn' --output text
```

### 3. Subscribe Webhook to SNS Topic

```bash
# Subscribe your webhook endpoint
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:YOUR-ACCOUNT:code-researcher-alerts \
  --protocol https \
  --notification-endpoint https://your-domain.com/webhook/cloudwatch
```

**Note**: SNS will send a subscription confirmation to your webhook. Code Researcher automatically handles this.

### 4. Configure CloudWatch Alarms

#### Option A: Existing Alarms

Modify existing alarms to publish to your SNS topic:

```bash
# Add SNS action to existing alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "HighErrorRate" \
  --alarm-description "High error rate detected" \
  --metric-name "ErrorRate" \
  --namespace "AWS/Lambda" \
  --statistic "Average" \
  --period 300 \
  --threshold 5.0 \
  --comparison-operator "GreaterThanThreshold" \
  --alarm-actions arn:aws:sns:us-east-1:YOUR-ACCOUNT:code-researcher-alerts
```

#### Option B: New Alarms

Create new alarms that publish to your topic:

```bash
# Lambda error rate alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "Lambda-HighErrorRate" \
  --alarm-description "Lambda function error rate is high" \
  --metric-name "Errors" \
  --namespace "AWS/Lambda" \
  --dimensions Name=FunctionName,Value=YourFunctionName \
  --statistic "Sum" \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 10 \
  --comparison-operator "GreaterThanThreshold" \
  --alarm-actions arn:aws:sns:us-east-1:YOUR-ACCOUNT:code-researcher-alerts

# API Gateway 5xx errors
aws cloudwatch put-metric-alarm \
  --alarm-name "APIGateway-5xxErrors" \
  --alarm-description "API Gateway 5xx error rate is high" \
  --metric-name "5XXError" \
  --namespace "AWS/ApiGateway" \
  --dimensions Name=ApiName,Value=YourApiName \
  --statistic "Sum" \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 5 \
  --comparison-operator "GreaterThanThreshold" \
  --alarm-actions arn:aws:sns:us-east-1:YOUR-ACCOUNT:code-researcher-alerts

# RDS connection errors
aws cloudwatch put-metric-alarm \
  --alarm-name "RDS-ConnectionErrors" \
  --alarm-description "RDS connection errors detected" \
  --metric-name "DatabaseConnections" \
  --namespace "AWS/RDS" \
  --dimensions Name=DBInstanceIdentifier,Value=YourDBInstance \
  --statistic "Average" \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 80 \
  --comparison-operator "GreaterThanThreshold" \
  --alarm-actions arn:aws:sns:us-east-1:YOUR-ACCOUNT:code-researcher-alerts
```

## Testing the Integration

### 1. Test Webhook Endpoint

```bash
# Test health check
curl https://your-domain.com/health

# Test webhook endpoint with sample data
curl -X POST https://your-domain.com/webhook/cloudwatch \
  -H "Content-Type: application/json" \
  -d '{
    "Type": "Notification",
    "MessageId": "test-message-id",
    "TopicArn": "arn:aws:sns:us-east-1:123456789:code-researcher-alerts",
    "Message": "{\"AlarmName\":\"TestAlarm\",\"AlarmDescription\":\"Test alarm for integration\",\"MetricName\":\"ErrorRate\",\"Namespace\":\"AWS/Lambda\",\"NewStateValue\":\"ALARM\",\"NewStateReason\":\"Threshold Crossed: 1 out of the last 1 datapoints was greater than the threshold (5.0).\",\"StateChangeTime\":\"2023-01-01T00:00:00.000Z\",\"Region\":\"us-east-1\",\"AWSAccountId\":\"123456789\"}"
  }'
```

### 2. Trigger Test Alarm

Create a test alarm that will definitely trigger:

```bash
# Create test alarm with very low threshold
aws cloudwatch put-metric-alarm \
  --alarm-name "CodeResearcher-Test-Alarm" \
  --alarm-description "Test alarm for Code Researcher integration" \
  --metric-name "CPUUtilization" \
  --namespace "AWS/EC2" \
  --statistic "Average" \
  --period 300 \
  --threshold 0.1 \
  --comparison-operator "GreaterThanThreshold" \
  --alarm-actions arn:aws:sns:us-east-1:YOUR-ACCOUNT:code-researcher-alerts

# Wait a few minutes, then check if alarm triggered
aws cloudwatch describe-alarms --alarm-names "CodeResearcher-Test-Alarm"

# Clean up test alarm
aws cloudwatch delete-alarms --alarm-names "CodeResearcher-Test-Alarm"
```

## CloudWatch Alarm Best Practices

### 1. Meaningful Alarm Names

Use descriptive names that help with repository matching:

```bash
# Good examples
"Lambda-UserService-HighErrorRate"
"API-PaymentService-5xxErrors"
"Database-OrderDB-ConnectionErrors"

# Poor examples
"Alarm1"
"HighErrors"
"DatabaseIssue"
```

### 2. Detailed Descriptions

Include context in alarm descriptions:

```yaml
AlarmDescription: "User service Lambda function error rate exceeded 5% over 5 minutes. This may indicate issues with user authentication or database connectivity."
```

### 3. Appropriate Thresholds

Set thresholds that indicate real issues:

```bash
# Error rates
--threshold 5.0  # 5% error rate

# Response times
--threshold 2000  # 2 second response time

# Resource utilization
--threshold 80  # 80% CPU/memory usage
```

### 4. Evaluation Periods

Use multiple evaluation periods to avoid false alarms:

```bash
--evaluation-periods 2  # Must breach threshold twice
--period 300           # Over 5-minute periods
```

## Repository Matching

Code Researcher matches CloudWatch alarms to repositories using keywords extracted from:

- Alarm name
- Metric name
- Namespace
- Alarm reason

### Keyword Extraction Examples

```yaml
# Alarm: "Lambda-UserService-HighErrorRate"
# Extracted keywords: ["lambda", "userservice", "higherrorrate", "error"]

# Namespace: "AWS/ApiGateway"
# Extracted keywords: ["aws", "apigateway", "api", "gateway"]

# Reason: "Error rate exceeded threshold"
# Extracted keywords: ["error", "rate", "exceeded", "threshold"]
```

### Improve Matching

Configure repository keywords to match your alarms:

```yaml
vcs:
  github:
    repositories:
      - owner: myorg
        name: user-service
        alert_keywords:
          - "user"
          - "userservice"
          - "lambda"
          - "authentication"
          - "auth"
      - owner: myorg
        name: payment-api
        alert_keywords:
          - "payment"
          - "api"
          - "gateway"
          - "transaction"
```

## Advanced Configuration

### Filtering Alarms

Ignore specific alarm patterns:

```yaml
alerts:
  cloudwatch:
    ignore_patterns:
      - "test-*"           # Ignore test alarms
      - "dev-*"            # Ignore development alarms
      - "*-canary-*"       # Ignore canary alarms
      - "scheduled-*"      # Ignore scheduled maintenance
```

### Custom Webhook URL

For development or testing, use ngrok:

```bash
# Install ngrok
npm install -g ngrok

# Expose local server
ngrok http 8000

# Use the HTTPS URL in your SNS subscription
# Example: https://abc123.ngrok.io/webhook/cloudwatch
```

### Multiple Environments

Use different SNS topics for different environments:

```yaml
# Production
alerts:
  cloudwatch:
    sns_topic_arn: arn:aws:sns:us-east-1:123:prod-code-researcher-alerts

# Staging
alerts:
  cloudwatch:
    sns_topic_arn: arn:aws:sns:us-east-1:123:staging-code-researcher-alerts

# Development
alerts:
  cloudwatch:
    sns_topic_arn: arn:aws:sns:us-east-1:123:dev-code-researcher-alerts
```

## Monitoring and Troubleshooting

### Check SNS Subscription Status

```bash
# List subscriptions for your topic
aws sns list-subscriptions-by-topic \
  --topic-arn arn:aws:sns:us-east-1:YOUR-ACCOUNT:code-researcher-alerts
```

### Verify Alarm Actions

```bash
# Check alarm configuration
aws cloudwatch describe-alarms --alarm-names "YourAlarmName"
```

### Monitor Code Researcher Logs

```bash
# Check application logs
tail -f logs/code-researcher.log

# Check for webhook requests
grep "cloudwatch_webhook" logs/code-researcher.log

# Check for processing errors
grep "ERROR" logs/code-researcher.log
```

### Common Issues

1. **Subscription not confirmed**
   - Check Code Researcher logs for confirmation handling
   - Manually confirm via AWS console if needed

2. **Webhook not receiving requests**
   - Verify SNS topic ARN in configuration
   - Check firewall/security group settings
   - Ensure webhook URL is publicly accessible

3. **Alarms not triggering analysis**
   - Check alarm state in CloudWatch console
   - Verify repository keyword matching
   - Review ignore patterns configuration

4. **SSL/TLS issues**
   - Ensure webhook URL uses HTTPS
   - Check SSL certificate validity
   - SNS requires valid SSL certificates

## Security Considerations

### SNS Message Validation

Code Researcher should validate SNS messages:

```python
# Example validation (implemented in the handler)
def validate_sns_message(message):
    # Verify message signature
    # Check message timestamp
    # Validate topic ARN
    pass
```

### Webhook Security

- Use HTTPS endpoints only
- Consider adding authentication headers
- Implement rate limiting
- Monitor for suspicious activity

### IAM Permissions

Minimal IAM policy for CloudWatch integration:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sns:CreateTopic",
        "sns:Subscribe",
        "sns:ListTopics",
        "sns:ListSubscriptionsByTopic"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:DescribeAlarms",
        "cloudwatch:PutMetricAlarm"
      ],
      "Resource": "*"
    }
  ]
}
```

## Next Steps

After setting up CloudWatch integration:

1. [Configure GitHub repositories](github.md)
2. [Set up additional alert sources](../configuration.md#alert-configuration)
3. [Monitor system performance](../troubleshooting/debugging.md)
4. [Review generated pull requests](../examples/integrations.md)
