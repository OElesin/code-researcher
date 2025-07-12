"""Test configuration and fixtures."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch

@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        'aws': {
            'region': 'us-east-1',
            'bedrock_model': 'anthropic.claude-sonnet-4-20250514-v1:0'
        },
        'alerts': {
            'cloudwatch': {
                'enabled': True,
                'sns_topic_arn': 'arn:aws:sns:us-east-1:123456789:test-topic'
            }
        },
        'vcs': {
            'github': {
                'access_token': 'test-token',
                'repositories': [
                    {
                        'owner': 'test-org',
                        'name': 'test-repo',
                        'branch': 'main',
                        'alert_keywords': ['error', 'exception']
                    }
                ]
            }
        },
        'server': {
            'host': '0.0.0.0',
            'port': 8000
        }
    }

@pytest.fixture
def sample_cloudwatch_alert():
    """Sample CloudWatch alert for testing."""
    return {
        'Type': 'Notification',
        'MessageId': 'test-message-id',
        'TopicArn': 'arn:aws:sns:us-east-1:123456789:test-topic',
        'Message': '{"AlarmName":"TestAlarm","AlarmDescription":"Test alarm description","MetricName":"ErrorRate","Namespace":"AWS/Lambda","NewStateValue":"ALARM","NewStateReason":"Threshold Crossed","StateChangeTime":"2023-01-01T00:00:00.000Z","Region":"us-east-1","AWSAccountId":"123456789"}'
    }

@pytest.fixture
def temp_workspace():
    """Temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def mock_github():
    """Mock GitHub client."""
    with patch('src.vcs.github_handler.github.Github') as mock:
        yield mock

@pytest.fixture
def mock_strands_agent():
    """Mock Strands Agent."""
    with patch('src.agents.code_research_agents.Agent') as mock:
        yield mock
