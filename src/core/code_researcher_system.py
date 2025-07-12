"""Main Code Researcher system integrating all components."""

import asyncio
import tempfile
import shutil
import time
import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ..alerts.cloudwatch_handler import CloudWatchAlertHandler, CloudWatchAlert
from ..vcs.github_handler import GitHubHandler, RepositoryConfig
from ..agents.code_research_agents import CodeResearcherOrchestrator

logger = logging.getLogger(__name__)


@dataclass
class ResearchJob:
    """Research job data structure."""
    job_id: str
    alert: CloudWatchAlert
    repositories: List[RepositoryConfig]
    status: str  # 'pending', 'analyzing', 'generating_fixes', 'creating_prs', 'completed', 'failed'
    orchestrator_response: Optional[Dict[str, Any]] = None
    pull_requests: Optional[List[str]] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class CodeResearcherSystem:
    """Main Code Researcher system."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Code Researcher system.
        
        Args:
            config: System configuration dictionary
        """
        self.config = config
        
        # Initialize handlers
        self.alert_handler = CloudWatchAlertHandler(config.get('alerts', {}).get('cloudwatch', {}))
        
        github_config = config.get('vcs', {}).get('github', {})
        if github_config.get('access_token'):
            self.github_handler = GitHubHandler(github_config['access_token'])
        else:
            logger.warning("GitHub access token not configured")
            self.github_handler = None
        
        # Initialize Strands orchestrator
        self.orchestrator = CodeResearcherOrchestrator()
        
        # Job tracking
        self.active_jobs: Dict[str, ResearchJob] = {}
        
        logger.info("Code Researcher system initialized")
    
    async def process_alert(self, alert_data: Dict[str, Any]) -> str:
        """Main entry point for processing alerts.
        
        Args:
            alert_data: Alert data from monitoring system
            
        Returns:
            Job ID for tracking the research process
        """
        try:
            # Parse alert
            alert = self.alert_handler.process_alert(alert_data)
            
            # Validate alert should be processed
            if not self.alert_handler.validate_alert(alert):
                logger.info(f"Alert {alert.alarm_name} skipped - validation failed")
                return None
            
            # Create research job
            job_id = self._generate_job_id()
            repositories = self._get_configured_repositories()
            
            job = ResearchJob(
                job_id=job_id,
                alert=alert,
                repositories=repositories,
                status='pending',
                created_at=datetime.now()
            )
            
            self.active_jobs[job_id] = job
            
            logger.info(f"Created research job {job_id} for alert {alert.alarm_name}")
            
            # Start async processing
            asyncio.create_task(self._process_research_job(job))
            
            return job_id
            
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
            raise
    
    async def _process_research_job(self, job: ResearchJob):
        """Process a research job through all stages using Strands agents.
        
        Args:
            job: Research job to process
        """
        try:
            logger.info(f"Processing research job {job.job_id}")
            
            # Stage 1: Identify relevant repositories
            job.status = 'analyzing'
            
            if not self.github_handler:
                job.status = 'failed'
                job.error_message = 'GitHub handler not configured'
                return
            
            relevant_repos = self.github_handler.identify_relevant_repositories(
                job.alert, 
                job.repositories
            )
            
            if not relevant_repos:
                job.status = 'failed'
                job.error_message = 'No relevant repositories found'
                logger.warning(f"No relevant repositories found for job {job.job_id}")
                return
            
            logger.info(f"Found {len(relevant_repos)} relevant repositories for job {job.job_id}")
            
            # Stage 2: Use Strands orchestrator for analysis and fix generation
            for repo_config, relevance_score in relevant_repos[:2]:  # Limit to top 2 repos
                logger.info(f"Processing repository {repo_config.full_name} (relevance: {relevance_score:.2f})")
                
                # Create temporary workspace
                with tempfile.TemporaryDirectory() as workspace:
                    try:
                        # Clone repository
                        self.github_handler.clone_repository(repo_config, workspace)
                        
                        # Use Strands orchestrator for comprehensive analysis
                        crash_report = self._format_alert_as_crash_report(job.alert)
                        
                        orchestrator_result = await self.orchestrator.analyze_crash(
                            crash_report=crash_report,
                            repository_path=workspace
                        )
                        
                        job.orchestrator_response = orchestrator_result
                        
                        # Stage 3: Create pull requests based on orchestrator results
                        if orchestrator_result.get('analysis_complete'):
                            job.status = 'creating_prs'
                            
                            # Extract fix proposals from orchestrator messages
                            fix_proposals = self._extract_fixes_from_orchestrator_response(
                                orchestrator_result
                            )
                            
                            if fix_proposals:
                                pr_url = await self._create_pull_request_for_fixes(
                                    repo_config, 
                                    fix_proposals, 
                                    job.alert,
                                    orchestrator_result
                                )
                                
                                if not job.pull_requests:
                                    job.pull_requests = []
                                job.pull_requests.append(pr_url)
                                
                                logger.info(f"Created pull request: {pr_url}")
                        
                    except Exception as e:
                        logger.error(f"Error processing repository {repo_config.full_name}: {e}")
                        job.error_message = str(e)
            
            # Update job status
            if job.pull_requests:
                job.status = 'completed'
                logger.info(f"Research job {job.job_id} completed successfully")
            else:
                job.status = 'failed'
                if not job.error_message:
                    job.error_message = 'No pull requests created'
                logger.warning(f"Research job {job.job_id} failed: {job.error_message}")
            
            job.completed_at = datetime.now()
            
        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.now()
            logger.error(f"Error processing research job {job.job_id}: {e}")
    
    def _format_alert_as_crash_report(self, alert: CloudWatchAlert) -> str:
        """Format CloudWatch alert as crash report for analysis.
        
        Args:
            alert: CloudWatch alert
            
        Returns:
            Formatted crash report string
        """
        return f"""
CLOUDWATCH ALERT DETAILS:
- Alarm Name: {alert.alarm_name}
- Description: {alert.alarm_description}
- Metric: {alert.metric_name}
- Namespace: {alert.namespace}
- State: {alert.state}
- Reason: {alert.reason}
- Timestamp: {alert.timestamp}
- Region: {alert.region}
- Account: {alert.account_id}

ERROR CONTEXT:
The system has detected an issue based on the CloudWatch metric '{alert.metric_name}' 
in namespace '{alert.namespace}'. The alert reason states: {alert.reason}

This suggests a potential bug or performance issue that needs investigation and fixing.

KEYWORDS FOR ANALYSIS:
{', '.join(self.alert_handler.extract_keywords(alert))}
"""
    
    def _extract_fixes_from_orchestrator_response(self, 
                                                 orchestrator_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract fix proposals from orchestrator response.
        
        Args:
            orchestrator_result: Result from Strands orchestrator
            
        Returns:
            List of fix proposals
        """
        fixes = []
        
        try:
            # Parse orchestrator messages for tool results
            messages = orchestrator_result.get('messages', [])
            
            for message in messages:
                if isinstance(message, dict) and 'content' in message:
                    for content in message.get('content', []):
                        if isinstance(content, dict) and 'toolResult' in content:
                            tool_result = content['toolResult']
                            if 'content' in tool_result:
                                try:
                                    # Try to parse as JSON for structured fixes
                                    result_data = json.loads(tool_result['content'])
                                    if isinstance(result_data, dict):
                                        if 'patches' in result_data or 'proposed_changes' in result_data:
                                            fixes.append(result_data)
                                        elif 'fix_needed' in result_data and result_data.get('fix_needed'):
                                            fixes.append(result_data)
                                except json.JSONDecodeError:
                                    # If not JSON, treat as text fix
                                    fixes.append({
                                        'type': 'text_fix',
                                        'content': tool_result['content']
                                    })
            
            logger.info(f"Extracted {len(fixes)} fix proposals from orchestrator response")
            
        except Exception as e:
            logger.error(f"Error extracting fixes from orchestrator response: {e}")
        
        return fixes
    
    async def _create_pull_request_for_fixes(self,
                                           repo_config: RepositoryConfig,
                                           fix_proposals: List[Dict[str, Any]],
                                           alert: CloudWatchAlert,
                                           orchestrator_result: Dict[str, Any]) -> str:
        """Create pull request with Strands-generated fixes.
        
        Args:
            repo_config: Repository configuration
            fix_proposals: List of fix proposals
            alert: CloudWatch alert
            orchestrator_result: Orchestrator analysis result
            
        Returns:
            URL of created pull request
        """
        try:
            # Generate branch name
            branch_name = f"auto-fix/{alert.alarm_name.lower().replace(' ', '-')}-{int(time.time())}"
            
            # Generate PR description with orchestrator insights
            pr_description = self._generate_strands_pr_description(
                alert, 
                fix_proposals, 
                orchestrator_result
            )
            
            # Create analysis documentation file
            analysis_content = self._format_analysis_as_markdown(orchestrator_result)
            
            files = [{
                'path': 'CODE_RESEARCHER_ANALYSIS.md',
                'content': analysis_content,
                'commit_message': 'Add automated code analysis results'
            }]
            
            # Add actual code fixes if available
            for fix in fix_proposals:
                if isinstance(fix, dict) and 'proposed_changes' in fix:
                    for change in fix['proposed_changes']:
                        if 'file_path' in change and 'proposed_code' in change:
                            files.append({
                                'path': change['file_path'],
                                'content': change['proposed_code'],
                                'commit_message': f"Auto-fix: {change.get('explanation', 'Bug fix')[:50]}..."
                            })
            
            # Create PR
            pr_url = self.github_handler.create_pull_request(
                repo_config=repo_config,
                branch_name=branch_name,
                title=f"🤖 Code Researcher Analysis: {alert.alarm_name}",
                description=pr_description,
                files=files
            )
            
            return pr_url
            
        except Exception as e:
            logger.error(f"Error creating pull request: {e}")
            raise
    
    def _generate_strands_pr_description(self, 
                                       alert: CloudWatchAlert, 
                                       fix_proposals: List[Dict[str, Any]],
                                       orchestrator_result: Dict[str, Any]) -> str:
        """Generate PR description with Strands orchestrator insights.
        
        Args:
            alert: CloudWatch alert
            fix_proposals: List of fix proposals
            orchestrator_result: Orchestrator result
            
        Returns:
            PR description string
        """
        description = f"""
## 🤖 Automated Code Research Analysis

This pull request was automatically generated by Code Researcher using AWS Strands Agents.

### Alert Details
- **Alarm Name**: {alert.alarm_name}
- **Description**: {alert.alarm_description}
- **Metric**: {alert.metric_name}
- **Namespace**: {alert.namespace}
- **Timestamp**: {alert.timestamp}
- **Reason**: {alert.reason}

### AI Analysis Summary
{orchestrator_result.get('response', 'Analysis completed successfully')[:500]}...

### Proposed Changes
"""
        
        for i, fix in enumerate(fix_proposals, 1):
            if isinstance(fix, dict):
                description += f"""
#### {i}. Analysis Result
- **Type**: {fix.get('type', 'Unknown')}
- **Confidence**: {fix.get('confidence', 'N/A')}
- **Summary**: {str(fix).replace('{', '').replace('}', '')[:200]}...
"""
        
        description += f"""

### 🔍 How This Was Generated
1. CloudWatch alert was received and analyzed
2. Strands orchestrator agent coordinated the analysis
3. Specialized code analysis agent performed deep research using:
   - Symbol definition search with ctags
   - Code pattern matching with git grep
   - Historical commit analysis
4. Code synthesis agent generated fix proposals
5. This pull request was automatically created for review

### ⚠️ Review Required
This is an automated analysis. Please:
1. Review all findings carefully
2. Validate the proposed solutions
3. Test any code changes in a staging environment
4. Verify the analysis addresses the root cause

### 🤖 Agent Workflow
The analysis was performed using a multi-agent system:
- **Orchestrator Agent**: Coordinated the overall process
- **Analysis Agent**: Performed deep code research with specialized tools
- **Synthesis Agent**: Generated fix proposals based on analysis

### 📊 Analysis Metrics
- **Repositories Analyzed**: 1
- **Tools Used**: {len([msg for msg in orchestrator_result.get('messages', []) if 'toolUse' in str(msg)])}
- **Analysis Duration**: ~{(orchestrator_result.get('completed_at', time.time()) - orchestrator_result.get('started_at', time.time())):.1f}s
"""
        
        return description
    
    def _format_analysis_as_markdown(self, orchestrator_result: Dict[str, Any]) -> str:
        """Format orchestrator analysis as markdown documentation.
        
        Args:
            orchestrator_result: Orchestrator analysis result
            
        Returns:
            Markdown formatted analysis
        """
        markdown = f"""# Code Researcher Analysis Report

## Analysis Summary
{orchestrator_result.get('response', 'Analysis completed')}

## Repository Information
- **Path**: {orchestrator_result.get('repository_path', 'N/A')}
- **Analysis Complete**: {orchestrator_result.get('analysis_complete', False)}

## Agent Messages and Tool Usage
"""
        
        messages = orchestrator_result.get('messages', [])
        for i, message in enumerate(messages):
            if isinstance(message, dict):
                markdown += f"""
### Message {i + 1}
**Role**: {message.get('role', 'Unknown')}

**Content**:
"""
                content = message.get('content', [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            if 'text' in item:
                                markdown += f"{item['text']}\n\n"
                            elif 'toolUse' in item:
                                tool_use = item['toolUse']
                                markdown += f"""
**Tool Used**: {tool_use.get('name', 'Unknown')}
**Input**: 
```json
{json.dumps(tool_use.get('input', {}), indent=2)}
```
"""
                            elif 'toolResult' in item:
                                tool_result = item['toolResult']
                                markdown += f"""
**Tool Result**:
```
{tool_result.get('content', '')[:1000]}...
```
"""
                else:
                    markdown += f"{str(content)}\n\n"
        
        markdown += f"""
## Analysis Timestamp
Generated at: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}

## Next Steps
1. Review the analysis findings above
2. Validate any proposed code changes
3. Test fixes in a staging environment
4. Deploy to production after verification

---
*This analysis was generated automatically by Code Researcher using AWS Strands Agents*
"""
        
        return markdown
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a research job.
        
        Args:
            job_id: Job ID to check
            
        Returns:
            Job status dictionary or None if not found
        """
        job = self.active_jobs.get(job_id)
        if not job:
            return None
        
        return {
            'job_id': job.job_id,
            'status': job.status,
            'alert': {
                'alarm_name': job.alert.alarm_name,
                'timestamp': job.alert.timestamp,
                'state': job.alert.state
            },
            'repositories_configured': len(job.repositories),
            'pull_requests_created': len(job.pull_requests or []),
            'error_message': job.error_message,
            'has_orchestrator_response': job.orchestrator_response is not None,
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None
        }
    
    def list_active_jobs(self) -> List[Dict[str, Any]]:
        """List all active jobs.
        
        Returns:
            List of job status dictionaries
        """
        return [self.get_job_status(job_id) for job_id in self.active_jobs.keys()]
    
    def _generate_job_id(self) -> str:
        """Generate unique job ID.
        
        Returns:
            Unique job identifier
        """
        import uuid
        return str(uuid.uuid4())
    
    def _get_configured_repositories(self) -> List[RepositoryConfig]:
        """Get list of configured repositories.
        
        Returns:
            List of repository configurations
        """
        repos = []
        github_config = self.config.get('vcs', {}).get('github', {})
        
        for repo_data in github_config.get('repositories', []):
            repo_config = RepositoryConfig(
                owner=repo_data['owner'],
                name=repo_data['name'],
                access_token=github_config['access_token'],
                branch=repo_data.get('branch', 'main'),
                file_patterns=repo_data.get('file_patterns', ["**/*.py", "**/*.js", "**/*.java", "**/*.go"]),
                alert_keywords=repo_data.get('alert_keywords', []),
                priority=repo_data.get('priority', 'medium')
            )
            repos.append(repo_config)
        
        return repos
