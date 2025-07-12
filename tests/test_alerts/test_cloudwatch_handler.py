"""Tests for CloudWatch alert handler."""

import pytest
import json
from unittest.mock import Mock, patch

from src.alerts.cloudwatch_handler import CloudWatchAlertHandler, CloudWatchAlert


class TestCloudWatchAlert:
    """Test CloudWatch alert data structure."""
    
    def test_from_sns_message_direct(self):
        """Test parsing direct CloudWatch alarm message."""
        message = {
            'AlarmName': 'TestAlarm',
            'AlarmDescription': 'Test description',
            'MetricName': 'ErrorRate',
            'Namespace': 'AWS/Lambda',
            'NewStateValue': 'ALARM',
            'NewStateReason': 'Threshold crossed',
            'StateChangeTime': '2023-01-01T00:00:00.000Z',
            'Region': 'us-east-1',
            'AWSAccountId': '123456789'
        }
        
        alert = CloudWatchAlert.from_sns_message(message)
        
        assert alert.alarm_name == 'TestAlarm'
        assert alert.alarm_description == 'Test description'
        assert alert.metric_name == 'ErrorRate'
        assert alert.namespace == 'AWS/Lambda'
        assert alert.state == 'ALARM'
        assert alert.reason == 'Threshold crossed'
        assert alert.region == 'us-east-1'
        assert alert.account_id == '123456789'
    
    def test_from_sns_message_wrapped(self):
        """Test parsing SNS-wrapped CloudWatch alarm message."""
        alarm_data = {
            'AlarmName': 'TestAlarm',
            'AlarmDescription': 'Test description',
            'MetricName': 'ErrorRate',
            'Namespace': 'AWS/Lambda',
            'NewStateValue': 'ALARM',
            'NewStateReason': 'Threshold crossed',
            'StateChangeTime': '2023-01-01T00:00:00.000Z',
            'Region': 'us-east-1',
            'AWSAccountId': '123456789'
        }
        
        sns_message = {
            'Type': 'Notification',
            'Message': json.dumps(alarm_data)
        }
        
        alert = CloudWatchAlert.from_sns_message(sns_message)
        
        assert alert.alarm_name == 'TestAlarm'
        assert alert.state == 'ALARM'
    
    def test_from_sns_message_invalid(self):
        """Test parsing invalid message raises error."""
        with pytest.raises(ValueError):
            CloudWatchAlert.from_sns_message({'invalid': 'data'})


class TestCloudWatchAlertHandler:
    """Test CloudWatch alert handler."""
    
    def test_init(self, sample_config):
        """Test handler initialization."""
        config = sample_config['alerts']['cloudwatch']
        
        with patch('boto3.client'):
            handler = CloudWatchAlertHandler(config)
            assert handler.config == config
    
    @patch('boto3.client')
    def test_setup_webhook_endpoint(self, mock_boto_client, sample_config):
        """Test webhook endpoint setup."""
        config = sample_config['alerts']['cloudwatch']
        config['webhook_url'] = 'https://example.com/webhook'
        config['topic_name'] = 'test-topic'
        
        mock_sns = Mock()
        mock_sns.create_topic.return_value = {'TopicArn': 'test-topic-arn'}
        mock_boto_client.return_value = mock_sns
        
        handler = CloudWatchAlertHandler(config)
        topic_arn = handler.setup_webhook_endpoint()
        
        assert topic_arn == 'test-topic-arn'
        mock_sns.create_topic.assert_called_once_with(Name='test-topic')
        mock_sns.subscribe.assert_called_once()
    
    @patch('boto3.client')
    def test_process_alert(self, mock_boto_client, sample_cloudwatch_alert):
        """Test alert processing."""
        config = {'region': 'us-east-1'}
        
        mock_sns = Mock()
        mock_cloudwatch = Mock()
        mock_cloudwatch.get_metric_statistics.return_value = {'Datapoints': []}
        mock_boto_client.side_effect = [mock_sns, mock_cloudwatch]
        
        handler = CloudWatchAlertHandler(config)
        alert = handler.process_alert(sample_cloudwatch_alert)
        
        assert isinstance(alert, CloudWatchAlert)
        assert alert.alarm_name == 'TestAlarm'
    
    @patch('boto3.client')
    def test_validate_alert_alarm_state(self, mock_boto_client):
        """Test alert validation for ALARM state."""
        config = {}
        handler = CloudWatchAlertHandler(config)
        
        # Test ALARM state (should be processed)
        alarm_alert = CloudWatchAlert(
            alarm_name='TestAlarm',
            alarm_description='Test',
            metric_name='ErrorRate',
            namespace='AWS/Lambda',
            timestamp='2023-01-01T00:00:00.000Z',
            state='ALARM',
            reason='Threshold crossed',
            region='us-east-1',
            account_id='123456789'
        )
        
        assert handler.validate_alert(alarm_alert) is True
        
        # Test OK state (should be skipped)
        ok_alert = CloudWatchAlert(
            alarm_name='TestAlarm',
            alarm_description='Test',
            metric_name='ErrorRate',
            namespace='AWS/Lambda',
            timestamp='2023-01-01T00:00:00.000Z',
            state='OK',
            reason='Threshold not crossed',
            region='us-east-1',
            account_id='123456789'
        )
        
        assert handler.validate_alert(ok_alert) is False
    
    @patch('boto3.client')
    def test_extract_keywords(self, mock_boto_client):
        """Test keyword extraction from alert."""
        config = {}
        handler = CloudWatchAlertHandler(config)
        
        alert = CloudWatchAlert(
            alarm_name='HighErrorRate-Lambda-Function',
            alarm_description='Test',
            metric_name='ErrorRate',
            namespace='AWS/Lambda',
            timestamp='2023-01-01T00:00:00.000Z',
            state='ALARM',
            reason='Error rate exceeded threshold',
            region='us-east-1',
            account_id='123456789'
        )
        
        keywords = handler.extract_keywords(alert)
        
        assert 'higherrorrate' in keywords
        assert 'lambda' in keywords
        assert 'function' in keywords
        assert 'errorrate' in keywords
        assert 'error' in keywords
