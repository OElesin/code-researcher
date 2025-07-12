# API Reference

Code Researcher provides a REST API for webhook integration, job monitoring, and system management.

## Base URL

```
http://localhost:8000  # Development
https://your-domain.com  # Production
```

## Authentication

Currently, Code Researcher uses IP-based access control. Future versions will include:
- API key authentication
- JWT token authentication
- OAuth integration

## Endpoints

### Health Check

#### GET /health

Check system health and status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "0.1.0",
  "active_jobs": 3
}
```

**Status Codes:**
- `200` - System healthy
- `503` - System unavailable

---

### CloudWatch Webhook

#### POST /webhook/cloudwatch

Receive CloudWatch alarm notifications via SNS.

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "Type": "Notification",
  "MessageId": "12345678-1234-1234-1234-123456789012",
  "TopicArn": "arn:aws:sns:us-east-1:123456789:code-researcher-alerts",
  "Subject": "ALARM: HighErrorRate",
  "Message": "{\"AlarmName\":\"HighErrorRate\",\"AlarmDescription\":\"Error rate is high\",\"MetricName\":\"ErrorRate\",\"Namespace\":\"AWS/Lambda\",\"NewStateValue\":\"ALARM\",\"NewStateReason\":\"Threshold Crossed\",\"StateChangeTime\":\"2024-01-01T12:00:00.000Z\",\"Region\":\"us-east-1\",\"AWSAccountId\":\"123456789\"}",
  "Timestamp": "2024-01-01T12:00:00.000Z",
  "SignatureVersion": "1",
  "Signature": "signature-string",
  "SigningCertURL": "https://sns.us-east-1.amazonaws.com/cert.pem",
  "UnsubscribeURL": "https://sns.us-east-1.amazonaws.com/unsubscribe"
}
```

**Response:**
```json
{
  "message": "Alert received and queued for processing",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Status Codes:**
- `200` - Alert accepted
- `400` - Invalid request format
- `503` - System unavailable

---

### Job Status

#### GET /status/{job_id}

Get the status of a research job.

**Parameters:**
- `job_id` (string) - Unique job identifier

**Response:**
```json
{
  "job_id": "12345678-1234-1234-1234-123456789012",
  "status": "completed",
  "alert": {
    "alarm_name": "HighErrorRate",
    "timestamp": "2024-01-01T12:00:00Z",
    "state": "ALARM"
  },
  "repositories_configured": 2,
  "pull_requests_created": 1,
  "error_message": null,
  "has_orchestrator_response": true,
  "created_at": "2024-01-01T12:00:00Z",
  "completed_at": "2024-01-01T12:05:00Z"
}
```

**Job Status Values:**
- `pending` - Job created, waiting to start
- `analyzing` - Identifying relevant repositories
- `generating_fixes` - AI analysis in progress
- `creating_prs` - Creating pull requests
- `completed` - Job finished successfully
- `failed` - Job failed with error

**Status Codes:**
- `200` - Job found
- `404` - Job not found
- `503` - System unavailable

---

### List Jobs

#### GET /jobs

List all active jobs.

**Query Parameters:**
- `status` (optional) - Filter by job status
- `limit` (optional) - Maximum number of jobs to return (default: 50)
- `offset` (optional) - Number of jobs to skip (default: 0)

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "12345678-1234-1234-1234-123456789012",
      "status": "completed",
      "alert": {
        "alarm_name": "HighErrorRate",
        "timestamp": "2024-01-01T12:00:00Z"
      },
      "repositories_configured": 2,
      "pull_requests_created": 1,
      "created_at": "2024-01-01T12:00:00Z",
      "completed_at": "2024-01-01T12:05:00Z"
    }
  ],
  "count": 1,
  "total": 1
}
```

**Status Codes:**
- `200` - Success
- `503` - System unavailable

---

### Test Alert

#### POST /test/alert

Submit a test alert for processing (development/testing only).

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "Type": "Notification",
  "Message": "{\"AlarmName\":\"TestAlarm\",\"MetricName\":\"ErrorRate\",\"Namespace\":\"AWS/Lambda\",\"NewStateValue\":\"ALARM\",\"NewStateReason\":\"Test alert\"}"
}
```

**Response:**
```json
{
  "message": "Test alert queued for processing",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Status Codes:**
- `200` - Alert accepted
- `400` - Invalid request format
- `503` - System unavailable

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "detail": "Error description",
  "timestamp": "2024-01-01T12:00:00Z",
  "error_code": "INTERNAL_ERROR"
}
```

### Common Error Codes

- `INVALID_REQUEST` - Request format is invalid
- `SYSTEM_UNAVAILABLE` - System is not ready
- `JOB_NOT_FOUND` - Requested job doesn't exist
- `CONFIGURATION_ERROR` - System configuration issue
- `INTERNAL_ERROR` - Unexpected system error

## Rate Limiting

Current rate limits (subject to change):

- **Webhook endpoints**: 100 requests/minute
- **Status endpoints**: 1000 requests/minute
- **Test endpoints**: 10 requests/minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Webhooks

### SNS Subscription Confirmation

Code Researcher automatically handles SNS subscription confirmations:

**Request:**
```json
{
  "Type": "SubscriptionConfirmation",
  "MessageId": "12345678-1234-1234-1234-123456789012",
  "Token": "confirmation-token",
  "TopicArn": "arn:aws:sns:us-east-1:123456789:code-researcher-alerts",
  "Message": "You have chosen to subscribe...",
  "SubscribeURL": "https://sns.us-east-1.amazonaws.com/confirm-subscription",
  "Timestamp": "2024-01-01T12:00:00.000Z"
}
```

**Response:**
```json
{
  "message": "Subscription confirmation received"
}
```

### Webhook Security

For production deployments, consider:

1. **HTTPS Only**: All webhook endpoints should use HTTPS
2. **Message Validation**: Verify SNS message signatures
3. **IP Filtering**: Restrict access to known SNS IP ranges
4. **Rate Limiting**: Implement appropriate rate limits

## SDK Examples

### Python

```python
import requests
import json

# Check system health
response = requests.get('https://your-domain.com/health')
print(response.json())

# Get job status
job_id = "12345678-1234-1234-1234-123456789012"
response = requests.get(f'https://your-domain.com/status/{job_id}')
print(response.json())

# Submit test alert
alert_data = {
    "Type": "Notification",
    "Message": json.dumps({
        "AlarmName": "TestAlarm",
        "MetricName": "ErrorRate",
        "Namespace": "AWS/Lambda",
        "NewStateValue": "ALARM",
        "NewStateReason": "Test alert"
    })
}

response = requests.post(
    'https://your-domain.com/test/alert',
    json=alert_data,
    headers={'Content-Type': 'application/json'}
)
print(response.json())
```

### JavaScript

```javascript
// Check system health
fetch('https://your-domain.com/health')
  .then(response => response.json())
  .then(data => console.log(data));

// Get job status
const jobId = "12345678-1234-1234-1234-123456789012";
fetch(`https://your-domain.com/status/${jobId}`)
  .then(response => response.json())
  .then(data => console.log(data));

// Submit test alert
const alertData = {
  Type: "Notification",
  Message: JSON.stringify({
    AlarmName: "TestAlarm",
    MetricName: "ErrorRate",
    Namespace: "AWS/Lambda",
    NewStateValue: "ALARM",
    NewStateReason: "Test alert"
  })
};

fetch('https://your-domain.com/test/alert', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(alertData)
})
.then(response => response.json())
.then(data => console.log(data));
```

### cURL

```bash
# Check system health
curl https://your-domain.com/health

# Get job status
curl https://your-domain.com/status/12345678-1234-1234-1234-123456789012

# List jobs
curl "https://your-domain.com/jobs?status=completed&limit=10"

# Submit test alert
curl -X POST https://your-domain.com/test/alert \
  -H "Content-Type: application/json" \
  -d '{
    "Type": "Notification",
    "Message": "{\"AlarmName\":\"TestAlarm\",\"MetricName\":\"ErrorRate\",\"Namespace\":\"AWS/Lambda\",\"NewStateValue\":\"ALARM\",\"NewStateReason\":\"Test alert\"}"
  }'
```

## OpenAPI Specification

The complete OpenAPI specification is available at:
```
GET /openapi.json
```

You can also view the interactive documentation at:
```
GET /docs
```

## Monitoring

### Health Check Endpoint

Use the health endpoint for:
- Load balancer health checks
- Monitoring system integration
- Uptime monitoring

### Metrics

Code Researcher exposes metrics at:
```
GET /metrics
```

Available metrics:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request duration
- `active_jobs_total` - Number of active jobs
- `jobs_completed_total` - Total completed jobs
- `jobs_failed_total` - Total failed jobs

## Versioning

API versioning follows semantic versioning:
- **Major version**: Breaking changes
- **Minor version**: New features, backward compatible
- **Patch version**: Bug fixes

Current version: `v1.0.0`

Future versions will be available at:
```
/api/v2/...
```

## Support

For API support:
- [GitHub Issues](https://github.com/your-org/code-researcher/issues)
- [Documentation](../README.md)
- [Examples](../examples/integrations.md)
