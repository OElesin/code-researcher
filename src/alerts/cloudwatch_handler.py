"""CloudWatch alert handler for processing AWS CloudWatch alarms."""

import boto3
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CloudWatchAlert:
    """CloudWatch alert data structure."""
    alarm_name: str
    alarm_description: str
    metric_name: str
    namespace: str
    timestamp: str
    state: str
    reason: str
    region: str
    account_id: str
    
    @classmethod
    def from_sns_message(cls, sns_message: Dict[str, Any]) -> 'CloudWatchAlert':
        """Parse CloudWatch alarm from SNS message."""
        try:
            # Handle both direct alarm messages and SNS-wrapped messages
            if 'Message' in sns_message:
                # SNS-wrapped message
                message_data = json.loads(sns_message['Message'])
            else:
                # Direct alarm message
                message_data = sns_message
            
            return cls(
                alarm_name=message_data.get('AlarmName', ''),
                alarm_description=message_data.get('AlarmDescription', ''),
                metric_name=message_data.get('MetricName', ''),
                namespace=message_data.get('Namespace', ''),
                timestamp=message_data.get('StateChangeTime', ''),
                state=message_data.get('NewStateValue', ''),
                reason=message_data.get('NewStateReason', ''),
                region=message_data.get('Region', ''),
                account_id=message_data.get('AWSAccountId', '')
            )
        except Exception as e:
            logger.error(f"Error parsing CloudWatch alert: {e}")
            raise ValueError(f"Invalid CloudWatch alert format: {e}")


class CloudWatchAlertHandler:
    """Handler for CloudWatch alerts via SNS."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize CloudWatch alert handler.
        
        Args:
            config: CloudWatch configuration dictionary
        """
        self.config = config
        self.sns_client = boto3.client('sns', region_name=config.get('region', 'us-east-1'))
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=config.get('region', 'us-east-1'))
        
    def setup_webhook_endpoint(self) -> Optional[str]:
        """Setup SNS topic and webhook endpoint for CloudWatch alerts.
        
        Returns:
            SNS topic ARN if successful, None otherwise
        """
        try:
            topic_name = self.config.get('topic_name', 'code-researcher-alerts')
            
            # Create SNS topic for alerts
            topic_response = self.sns_client.create_topic(Name=topic_name)
            topic_arn = topic_response['TopicArn']
            
            # Subscribe webhook endpoint to topic if URL provided
            webhook_url = self.config.get('webhook_url')
            if webhook_url:
                self.sns_client.subscribe(
                    TopicArn=topic_arn,
                    Protocol='https',
                    Endpoint=webhook_url
                )
                logger.info(f"Subscribed webhook {webhook_url} to topic {topic_arn}")
            
            return topic_arn
            
        except Exception as e:
            logger.error(f"Error setting up CloudWatch webhook: {e}")
            return None
    
    def process_alert(self, sns_message: Dict[str, Any]) -> CloudWatchAlert:
        """Process incoming CloudWatch alert.
        
        Args:
            sns_message: SNS message containing CloudWatch alarm
            
        Returns:
            Parsed CloudWatch alert
        """
        try:
            alert = CloudWatchAlert.from_sns_message(sns_message)
            
            # Enrich alert with additional context
            alert = self._enrich_alert_context(alert)
            
            logger.info(f"Processed CloudWatch alert: {alert.alarm_name}")
            return alert
            
        except Exception as e:
            logger.error(f"Error processing CloudWatch alert: {e}")
            raise
    
    def _enrich_alert_context(self, alert: CloudWatchAlert) -> CloudWatchAlert:
        """Enrich alert with additional AWS context.
        
        Args:
            alert: Base CloudWatch alert
            
        Returns:
            Enriched alert with additional context
        """
        try:
            # Get metric history for additional context
            if alert.metric_name and alert.namespace:
                response = self.cloudwatch_client.get_metric_statistics(
                    Namespace=alert.namespace,
                    MetricName=alert.metric_name,
                    StartTime=datetime.now().replace(hour=datetime.now().hour - 1),
                    EndTime=datetime.now(),
                    Period=300,
                    Statistics=['Average', 'Maximum']
                )
                
                # Add metric data to alert reason if available
                if response.get('Datapoints'):
                    latest_datapoint = max(response['Datapoints'], key=lambda x: x['Timestamp'])
                    alert.reason += f" (Latest: Avg={latest_datapoint.get('Average', 'N/A')}, Max={latest_datapoint.get('Maximum', 'N/A')})"
            
        except Exception as e:
            logger.warning(f"Could not enrich alert context: {e}")
        
        return alert
    
    def validate_alert(self, alert: CloudWatchAlert) -> bool:
        """Validate if alert should be processed.
        
        Args:
            alert: CloudWatch alert to validate
            
        Returns:
            True if alert should be processed, False otherwise
        """
        # Only process ALARM state
        if alert.state != 'ALARM':
            logger.info(f"Skipping alert {alert.alarm_name} - state is {alert.state}")
            return False
        
        # Check if alarm name matches any configured patterns
        ignore_patterns = self.config.get('ignore_patterns', [])
        for pattern in ignore_patterns:
            if pattern in alert.alarm_name.lower():
                logger.info(f"Skipping alert {alert.alarm_name} - matches ignore pattern {pattern}")
                return False
        
        return True
    
    def extract_keywords(self, alert: CloudWatchAlert) -> list[str]:
        """Extract relevant keywords from alert for repository matching.
        
        Args:
            alert: CloudWatch alert
            
        Returns:
            List of keywords extracted from the alert
        """
        keywords = []
        
        # Extract from alarm name
        alarm_words = alert.alarm_name.lower().replace('-', ' ').replace('_', ' ').split()
        keywords.extend([word for word in alarm_words if len(word) > 2])
        
        # Extract from namespace
        if alert.namespace:
            namespace_words = alert.namespace.lower().replace('/', ' ').replace('-', ' ').split()
            keywords.extend([word for word in namespace_words if len(word) > 2])
        
        # Extract from metric name
        if alert.metric_name:
            metric_words = alert.metric_name.lower().replace('-', ' ').replace('_', ' ').split()
            keywords.extend([word for word in metric_words if len(word) > 2])
        
        # Extract from reason
        if alert.reason:
            # Simple keyword extraction from reason text
            reason_words = alert.reason.lower().split()
            technical_keywords = [word for word in reason_words 
                                if any(tech in word for tech in ['error', 'exception', 'timeout', 'fail', 'high', 'low'])]
            keywords.extend(technical_keywords)
        
        # Remove duplicates and return
        return list(set(keywords))
