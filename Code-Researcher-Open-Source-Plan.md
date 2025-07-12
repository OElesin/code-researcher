# Code Researcher: Open Source Automated Bug Investigation & Fix Platform

## Project Overview

**Code Researcher** is an open source AI-powered platform that automatically investigates bugs and creates fix proposals by:
1. **Receiving alerts** from monitoring/alerting tools (CloudWatch, DataDog, New Relic)
2. **Identifying relevant repositories** from configured VCS systems (GitHub, GitLab)
3. **Performing intelligent code research** based on bug reports using AI agents
4. **Creating pull requests** with proposed fixes for engineer review

## Vision & Mission

### Vision
To democratize automated bug investigation and resolution, making it accessible to development teams of all sizes through open source technology.

### Mission
Reduce mean time to resolution (MTTR) for production bugs by providing intelligent, automated first-response investigation and fix proposals.

## Architecture Overview

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
│(GitHub/   │    │  (Code Search)   │    │   (OpenAI/      │
│ GitLab)   │    │                  │    │    Anthropic)   │
└───────────┘    └──────────────────┘    └─────────────────┘
```

## Phase 1: Core Open Source Foundation

### 1.1 Alert Integration Layer

**Priority Order:**
1. **AWS CloudWatch** (Primary focus)
2. DataDog
3. New Relic

#### CloudWatch Integration
```python
# src/alerts/cloudwatch_handler.py
import boto3
import json
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class CloudWatchAlert:
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
        """Parse CloudWatch alarm from SNS message"""
        return cls(
            alarm_name=sns_message.get('AlarmName', ''),
            alarm_description=sns_message.get('AlarmDescription', ''),
            metric_name=sns_message.get('MetricName', ''),
            namespace=sns_message.get('Namespace', ''),
            timestamp=sns_message.get('StateChangeTime', ''),
            state=sns_message.get('NewStateValue', ''),
            reason=sns_message.get('NewStateReason', ''),
            region=sns_message.get('Region', ''),
            account_id=sns_message.get('AWSAccountId', '')
        )

class CloudWatchAlertHandler:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sns_client = boto3.client('sns')
        
    def setup_webhook_endpoint(self) -> str:
        """Setup SNS topic and webhook endpoint for CloudWatch alerts"""
        # Create SNS topic for alerts
        topic_response = self.sns_client.create_topic(
            Name='code-researcher-alerts'
        )
        
        # Subscribe webhook endpoint to topic
        self.sns_client.subscribe(
            TopicArn=topic_response['TopicArn'],
            Protocol='https',
            Endpoint=f"{self.config['webhook_base_url']}/webhook/cloudwatch"
        )
        
        return topic_response['TopicArn']
    
    def process_alert(self, sns_message: Dict[str, Any]) -> CloudWatchAlert:
        """Process incoming CloudWatch alert"""
        alert = CloudWatchAlert.from_sns_message(sns_message)
        
        # Enrich alert with additional context
        alert = self._enrich_alert_context(alert)
        
        return alert
    
    def _enrich_alert_context(self, alert: CloudWatchAlert) -> CloudWatchAlert:
        """Enrich alert with additional AWS context"""
        # Add log insights, metrics, etc.
        return alert
```

### 1.2 VCS Integration Layer

**Priority Order:**
1. **GitHub** (Primary focus)
2. GitLab

#### GitHub Integration
```python
# src/vcs/github_handler.py
import github
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class RepositoryConfig:
    owner: str
    name: str
    access_token: str
    branch: str = "main"
    file_patterns: List[str] = None
    alert_keywords: List[str] = None
    
    def __post_init__(self):
        if self.file_patterns is None:
            self.file_patterns = ["**/*.py", "**/*.js", "**/*.java", "**/*.go"]
        if self.alert_keywords is None:
            self.alert_keywords = []

class GitHubHandler:
    def __init__(self, access_token: str):
        self.github = github.Github(access_token)
        
    def clone_repository(self, repo_config: RepositoryConfig, workspace_path: str) -> str:
        """Clone repository to local workspace"""
        import git
        
        repo_url = f"https://github.com/{repo_config.owner}/{repo_config.name}.git"
        
        # Clone repository
        repo = git.Repo.clone_from(
            repo_url,
            workspace_path,
            branch=repo_config.branch
        )
        
        return workspace_path
    
    def identify_relevant_repositories(self, 
                                    alert: Any, 
                                    repo_configs: List[RepositoryConfig]) -> List[RepositoryConfig]:
        """Identify which repositories are relevant to the alert"""
        relevant_repos = []
        
        # Extract keywords from alert
        alert_text = self._extract_alert_text(alert)
        alert_keywords = self._extract_keywords(alert_text)
        
        for repo_config in repo_configs:
            relevance_score = self._calculate_relevance_score(
                alert_keywords, 
                repo_config
            )
            
            if relevance_score > 0.3:  # Threshold for relevance
                relevant_repos.append((repo_config, relevance_score))
        
        # Sort by relevance score and return top 3
        relevant_repos.sort(key=lambda x: x[1], reverse=True)
        return [repo for repo, score in relevant_repos[:3]]
    
    def create_pull_request(self, 
                          repo_config: RepositoryConfig,
                          branch_name: str,
                          title: str,
                          description: str,
                          files: List[Dict[str, str]]) -> str:
        """Create pull request with proposed fixes"""
        repo = self.github.get_repo(f"{repo_config.owner}/{repo_config.name}")
        
        # Create new branch
        base_branch = repo.get_branch(repo_config.branch)
        repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=base_branch.commit.sha
        )
        
        # Commit files
        for file_info in files:
            try:
                # Try to get existing file
                existing_file = repo.get_contents(file_info['path'], ref=branch_name)
                repo.update_file(
                    path=file_info['path'],
                    message=f"Auto-fix: {file_info.get('commit_message', 'Bug fix')}",
                    content=file_info['content'],
                    sha=existing_file.sha,
                    branch=branch_name
                )
            except github.UnknownObjectException:
                # File doesn't exist, create new
                repo.create_file(
                    path=file_info['path'],
                    message=f"Auto-fix: {file_info.get('commit_message', 'Bug fix')}",
                    content=file_info['content'],
                    branch=branch_name
                )
        
        # Create pull request
        pr = repo.create_pull(
            title=title,
            body=description,
            head=branch_name,
            base=repo_config.branch
        )
        
        # Add labels
        pr.add_to_labels("automated-fix", "needs-review")
        
        return pr.html_url
    
    def _extract_alert_text(self, alert: Any) -> str:
        """Extract searchable text from alert"""
        # Implementation depends on alert type
        return str(alert)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from alert text"""
        # Simple keyword extraction - can be enhanced with NLP
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        return [word for word in words if len(word) > 3]
    
    def _calculate_relevance_score(self, 
                                 alert_keywords: List[str], 
                                 repo_config: RepositoryConfig) -> float:
        """Calculate relevance score between alert and repository"""
        if not repo_config.alert_keywords:
            return 0.5  # Default relevance if no keywords configured
        
        matches = set(alert_keywords) & set(repo_config.alert_keywords)
        return len(matches) / len(repo_config.alert_keywords)
```

### 1.3 Code Research Engine

```python
# src/research/code_analyzer.py
import os
import subprocess
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class CodeAnalysisResult:
    repository_path: str
    alert_context: Dict[str, Any]
    relevant_files: List[str]
    symbol_definitions: List[Dict[str, Any]]
    code_patterns: List[Dict[str, Any]]
    commit_history: List[Dict[str, Any]]
    confidence_score: float

class CodeAnalyzer:
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
        
    def analyze_for_bug(self, 
                       workspace_path: str, 
                       alert: Any) -> CodeAnalysisResult:
        """Perform comprehensive code analysis for bug investigation"""
        
        # Step 1: Extract relevant information from alert
        alert_context = self._extract_alert_context(alert)
        
        # Step 2: Search for relevant files
        relevant_files = self._find_relevant_files(workspace_path, alert_context)
        
        # Step 3: Analyze symbols and definitions
        symbol_definitions = self._analyze_symbols(workspace_path, alert_context)
        
        # Step 4: Search for code patterns
        code_patterns = self._search_code_patterns(workspace_path, alert_context)
        
        # Step 5: Analyze commit history
        commit_history = self._analyze_commit_history(workspace_path, alert_context)
        
        # Step 6: Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            relevant_files, symbol_definitions, code_patterns, commit_history
        )
        
        return CodeAnalysisResult(
            repository_path=workspace_path,
            alert_context=alert_context,
            relevant_files=relevant_files,
            symbol_definitions=symbol_definitions,
            code_patterns=code_patterns,
            commit_history=commit_history,
            confidence_score=confidence_score
        )
    
    def _extract_alert_context(self, alert: Any) -> Dict[str, Any]:
        """Extract searchable context from alert"""
        context = {
            'error_message': getattr(alert, 'reason', ''),
            'metric_name': getattr(alert, 'metric_name', ''),
            'namespace': getattr(alert, 'namespace', ''),
            'timestamp': getattr(alert, 'timestamp', ''),
            'keywords': []
        }
        
        # Extract keywords from error message
        if context['error_message']:
            context['keywords'] = self._extract_technical_keywords(
                context['error_message']
            )
        
        return context
    
    def _find_relevant_files(self, 
                           workspace_path: str, 
                           alert_context: Dict[str, Any]) -> List[str]:
        """Find files relevant to the alert using various search strategies"""
        relevant_files = []
        
        # Search by keywords in file content
        for keyword in alert_context['keywords']:
            files = self._search_files_by_content(workspace_path, keyword)
            relevant_files.extend(files)
        
        # Search by file patterns (e.g., error logs, config files)
        pattern_files = self._search_files_by_patterns(workspace_path, alert_context)
        relevant_files.extend(pattern_files)
        
        # Remove duplicates and return
        return list(set(relevant_files))
    
    def _search_files_by_content(self, workspace_path: str, keyword: str) -> List[str]:
        """Search for files containing specific keywords"""
        try:
            result = subprocess.run([
                'git', 'grep', '-l', keyword
            ], cwd=workspace_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')
        except Exception:
            pass
        
        return []
    
    def _analyze_symbols(self, 
                        workspace_path: str, 
                        alert_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze symbol definitions using ctags"""
        symbols = []
        
        try:
            # Generate ctags
            subprocess.run([
                'ctags', '-R', '--fields=+iaS', '--extra=+q', '.'
            ], cwd=workspace_path, check=True)
            
            # Read tags file
            tags_file = os.path.join(workspace_path, 'tags')
            if os.path.exists(tags_file):
                with open(tags_file, 'r') as f:
                    for line in f:
                        if not line.startswith('!'):
                            parts = line.strip().split('\t')
                            if len(parts) >= 3:
                                symbols.append({
                                    'name': parts[0],
                                    'file': parts[1],
                                    'pattern': parts[2],
                                    'type': parts[3] if len(parts) > 3 else 'unknown'
                                })
        except Exception as e:
            print(f"Error analyzing symbols: {e}")
        
        return symbols
    
    def _calculate_confidence_score(self, *args) -> float:
        """Calculate confidence score based on analysis results"""
        # Simple scoring algorithm - can be enhanced
        base_score = 0.5
        
        # Increase confidence based on number of relevant files found
        if args[0]:  # relevant_files
            base_score += min(len(args[0]) * 0.1, 0.3)
        
        # Increase confidence based on symbol matches
        if args[1]:  # symbol_definitions
            base_score += min(len(args[1]) * 0.05, 0.2)
        
        return min(base_score, 1.0)
```

### 1.4 Strands Agent Architecture

Following the AWS Strands SDK agent-as-tools pattern, we'll implement specialized agents:

```python
# src/agents/code_research_agents.py
import os
import json
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from strands import Agent, tool
from strands.models import BedrockModel

@dataclass
class FixProposal:
    file_path: str
    original_code: str
    proposed_code: str
    explanation: str
    confidence: float
    fix_type: str  # 'bug_fix', 'performance', 'security', etc.

# Specialized Agent System Prompts
ANALYSIS_AGENT_PROMPT = """
You are a Code Analysis Specialist focused on deep research and context gathering.

Your expertise:
- Symbol definition analysis using ctags and git grep
- Code pattern searching with regex
- Historical commit analysis for similar fixes
- Root cause investigation through systematic exploration

Your process:
1. Parse crash reports to identify key symbols and functions
2. Search for symbol definitions and understand code structure
3. Analyze historical commits for similar issues and fixes
4. Build comprehensive context about the crash
5. Continue until you have sufficient understanding of root cause

Available tools:
- search_definition: Find symbol definitions in codebase
- search_code: Search for code patterns using regex
- search_commits: Analyze git history for relevant changes
- analyze_symbols: Deep dive into symbol relationships
"""

SYNTHESIS_AGENT_PROMPT = """
You are a Code Synthesis Specialist focused on generating fixes for software crashes.

Your expertise:
- Hypothesis generation based on analysis context
- Patch creation following best practices
- Fix validation and explanation

Your process:
1. Receive comprehensive analysis context from Analysis Agent
2. Generate root cause hypothesis
3. Create targeted patches addressing the root cause
4. Validate patches against similar historical fixes
5. Provide clear explanations of the fix rationale

Available tools:
- generate_patch: Create code patches based on analysis
- validate_patch: Check patch against best practices
- explain_fix: Provide detailed fix explanations
"""

ORCHESTRATOR_PROMPT = """
You are the Code Researcher Orchestrator, managing a team of specialized agents
to analyze and fix complex software crashes.

Your workflow:
1. Receive crash report and repository information
2. Delegate deep analysis to the Analysis Agent
3. Once sufficient context is gathered, delegate patch generation to Synthesis Agent
4. Coordinate the overall research and fix generation process

Available specialist agents:
- code_analysis_agent: Deep code exploration and context gathering
- code_synthesis_agent: Hypothesis generation and patch creation

Always use the appropriate specialist agent based on the task at hand.
"""

# Tool Functions for Code Analysis
@tool
def search_definition(symbol_name: str, repository_path: str, file_path: str = None) -> str:
    """
    Search for symbol definitions using ctags in the codebase.
    
    Args:
        symbol_name: Name of the symbol to search for
        repository_path: Path to the repository
        file_path: Optional specific file to search in
        
    Returns:
        JSON string containing symbol definitions with file locations and content
    """
    try:
        # Generate ctags if not exists
        ctags_file = os.path.join(repository_path, 'tags')
        if not os.path.exists(ctags_file):
            subprocess.run([
                'ctags', '-R', '--fields=+iaS', '--extra=+q', '.'
            ], cwd=repository_path, check=True)
        
        # Search for symbol
        results = []
        with open(ctags_file, 'r') as f:
            for line in f:
                if not line.startswith('!') and symbol_name in line:
                    parts = line.strip().split('\t')
                    if len(parts) >= 3 and parts[0] == symbol_name:
                        results.append({
                            'symbol': parts[0],
                            'file': parts[1],
                            'pattern': parts[2],
                            'type': parts[3] if len(parts) > 3 else 'unknown'
                        })
        
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({'error': str(e)})

@tool
def search_code(pattern: str, repository_path: str, context_lines: int = 2) -> str:
    """
    Search code patterns using git grep with context.
    
    Args:
        pattern: Regular expression pattern to search
        repository_path: Path to the repository
        context_lines: Number of context lines to include
        
    Returns:
        JSON string containing matching code snippets with context
    """
    try:
        result = subprocess.run([
            'git', 'grep', '-n', f'-C{context_lines}', pattern
        ], cwd=repository_path, capture_output=True, text=True)
        
        if result.returncode == 0:
            matches = []
            current_file = None
            current_match = {'file': '', 'lines': []}
            
            for line in result.stdout.split('\n'):
                if ':' in line:
                    file_part, content = line.split(':', 1)
                    if file_part != current_file:
                        if current_match['lines']:
                            matches.append(current_match)
                        current_file = file_part
                        current_match = {'file': file_part, 'lines': [content]}
                    else:
                        current_match['lines'].append(content)
            
            if current_match['lines']:
                matches.append(current_match)
            
            return json.dumps(matches, indent=2)
        else:
            return json.dumps({'message': 'No matches found'})
    except Exception as e:
        return json.dumps({'error': str(e)})

@tool
def search_commits(query: str, repository_path: str, max_results: int = 10) -> str:
    """
    Search git commit history for relevant changes.
    
    Args:
        query: Search query for commits
        repository_path: Path to the repository
        max_results: Maximum number of results to return
        
    Returns:
        JSON string containing relevant commits with diffs
    """
    try:
        # Search commit messages
        result = subprocess.run([
            'git', 'log', '--grep=' + query, f'--max-count={max_results}',
            '--pretty=format:%H|%s|%an|%ad', '--date=short'
        ], cwd=repository_path, capture_output=True, text=True)
        
        commits = []
        if result.returncode == 0 and result.stdout:
            for line in result.stdout.split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        commit_hash = parts[0]
                        
                        # Get diff for this commit
                        diff_result = subprocess.run([
                            'git', 'show', '--stat', commit_hash
                        ], cwd=repository_path, capture_output=True, text=True)
                        
                        commits.append({
                            'hash': commit_hash,
                            'message': parts[1],
                            'author': parts[2],
                            'date': parts[3],
                            'diff_summary': diff_result.stdout[:1000] if diff_result.returncode == 0 else ''
                        })
        
        return json.dumps(commits, indent=2)
    except Exception as e:
        return json.dumps({'error': str(e)})

@tool
def generate_patch(file_path: str, repository_path: str, analysis_context: str) -> str:
    """
    Generate code patch based on analysis context.
    
    Args:
        file_path: Path to the file to patch
        repository_path: Path to the repository
        analysis_context: JSON string containing analysis results
        
    Returns:
        JSON string containing proposed patch
    """
    try:
        # Read file content
        full_path = os.path.join(repository_path, file_path)
        with open(full_path, 'r') as f:
            file_content = f.read()
        
        # Parse analysis context
        context = json.loads(analysis_context)
        
        # Create a simple patch generation agent
        patch_agent = Agent(
            system_prompt="""You are a code patch generator. Based on the analysis context and file content,
            generate a specific patch to fix the identified issue. Return your response as JSON with:
            - analysis: your understanding of the issue
            - proposed_changes: list of specific line changes
            - explanation: why this fix addresses the root cause""",
            model=BedrockModel(model_id="anthropic.claude-sonnet-4-20250514-v1:0")
        )
        
        prompt = f"""
        ANALYSIS CONTEXT:
        {json.dumps(context, indent=2)}
        
        FILE TO PATCH: {file_path}
        FILE CONTENT:
        {file_content[:3000]}  # Limit to avoid token limits
        
        Generate a patch to fix the identified issue.
        """
        
        response = patch_agent(prompt)
        return str(response)
        
    except Exception as e:
        return json.dumps({'error': str(e)})

# Specialized Agent Tools
@tool
def code_analysis_agent(crash_report: str, repository_path: str) -> str:
    """
    Perform deep analysis of a crash report using specialized analysis agent.
    
    Args:
        crash_report: The crash report to analyze
        repository_path: Path to the code repository
        
    Returns:
        JSON string containing comprehensive analysis context
    """
    try:
        # Create specialized analysis agent
        analysis_agent = Agent(
            system_prompt=ANALYSIS_AGENT_PROMPT,
            tools=[search_definition, search_code, search_commits],
            model=BedrockModel(model_id="anthropic.claude-sonnet-4-20250514-v1:0")
        )
        
        analysis_prompt = f"""
        Analyze this crash report and gather comprehensive context:
        
        CRASH REPORT:
        {crash_report}
        
        REPOSITORY: {repository_path}
        
        Perform systematic analysis using your available tools.
        Continue until you have sufficient context to understand the root cause.
        """
        
        # Set environment variable for tools
        os.environ['CURRENT_REPO_PATH'] = repository_path
        
        response = analysis_agent(analysis_prompt)
        
        # Extract analysis context from agent's conversation
        analysis_context = {
            'crash_report': crash_report,
            'repository_path': repository_path,
            'analysis_result': str(response),
            'tool_calls': []
        }
        
        # Parse tool usage from messages
        for message in analysis_agent.messages:
            if isinstance(message, dict) and 'content' in message:
                for content in message.get('content', []):
                    if isinstance(content, dict) and 'toolUse' in content:
                        analysis_context['tool_calls'].append({
                            'tool': content['toolUse']['name'],
                            'input': content['toolUse']['input']
                        })
        
        return json.dumps(analysis_context, indent=2)
        
    except Exception as e:
        return json.dumps({'error': str(e)})

@tool
def code_synthesis_agent(analysis_context: str, repository_path: str) -> str:
    """
    Generate patches based on analysis context using specialized synthesis agent.
    
    Args:
        analysis_context: JSON string containing analysis results
        repository_path: Path to the repository
        
    Returns:
        JSON string containing hypothesis and patches
    """
    try:
        # Create specialized synthesis agent
        synthesis_agent = Agent(
            system_prompt=SYNTHESIS_AGENT_PROMPT,
            tools=[generate_patch],
            model=BedrockModel(model_id="anthropic.claude-sonnet-4-20250514-v1:0")
        )
        
        synthesis_prompt = f"""
        Based on the comprehensive analysis, generate a fix for this crash:
        
        ANALYSIS CONTEXT:
        {analysis_context}
        
        REPOSITORY: {repository_path}
        
        Provide:
        1. Root cause hypothesis
        2. Proposed patch with justification
        3. Explanation of how the fix addresses the root cause
        """
        
        # Set environment variable for tools
        os.environ['CURRENT_REPO_PATH'] = repository_path
        
        response = synthesis_agent(synthesis_prompt)
        
        # Extract synthesis results
        synthesis_result = {
            'repository_path': repository_path,
            'hypothesis': str(response),
            'patches': [],
            'tool_calls': []
        }
        
        # Parse tool usage from messages
        for message in synthesis_agent.messages:
            if isinstance(message, dict) and 'content' in message:
                for content in message.get('content', []):
                    if isinstance(content, dict) and 'toolUse' in content:
                        synthesis_result['tool_calls'].append({
                            'tool': content['toolUse']['name'],
                            'input': content['toolUse']['input']
                        })
        
        return json.dumps(synthesis_result, indent=2)
        
    except Exception as e:
        return json.dumps({'error': str(e)})

# Main Orchestrator Agent
class CodeResearcherOrchestrator:
    def __init__(self):
        self.orchestrator = Agent(
            system_prompt=ORCHESTRATOR_PROMPT,
            tools=[code_analysis_agent, code_synthesis_agent],
            model=BedrockModel(
                model_id="anthropic.claude-sonnet-4-20250514-v1:0",
                additional_request_fields={
                    "thinking": {
                        "type": "enabled",
                        "budget_tokens": 4096,
                    }
                }
            )
        )
    
    async def analyze_crash(self, crash_report: str, repository_path: str):
        """
        Main entry point for crash analysis using the orchestrator pattern.
        """
        analysis_request = f"""
        I need to analyze and fix this software crash:
        
        CRASH REPORT:
        {crash_report}
        
        REPOSITORY: {repository_path}
        
        Please coordinate the analysis and synthesis process:
        1. Use the code_analysis_agent to perform deep research
        2. Once sufficient context is gathered, use code_synthesis_agent to generate fixes
        3. Provide a comprehensive report of findings and proposed solutions
        """
        
        # Enable tool consent bypass for automation
        os.environ["BYPASS_TOOL_CONSENT"] = "true"
        
        # Call orchestrator
        response = self.orchestrator(analysis_request)
        
        return {
            'response': str(response),
            'messages': self.orchestrator.messages,
            'analysis_complete': True
        }
```
    
    def generate_fixes(self, 
                      analysis_result: 'CodeAnalysisResult') -> List[FixProposal]:
        """Generate fix proposals based on code analysis"""
        
        fixes = []
        
        # Generate fixes for each relevant file
        for file_path in analysis_result.relevant_files[:5]:  # Limit to top 5 files
            file_content = self._read_file_content(
                analysis_result.repository_path, 
                file_path
            )
            
            if file_content:
                fix_proposal = self._generate_file_fix(
                    file_path=file_path,
                    file_content=file_content,
                    analysis_context=analysis_result.alert_context,
                    symbols=analysis_result.symbol_definitions
                )
                
                if fix_proposal and fix_proposal.confidence > 0.6:
                    fixes.append(fix_proposal)
        
        return fixes
    
    def _generate_file_fix(self, 
                          file_path: str,
                          file_content: str,
                          analysis_context: Dict[str, Any],
                          symbols: List[Dict[str, Any]]) -> Optional[FixProposal]:
        """Generate fix for a specific file"""
        
        # Create context-aware prompt
        prompt = self._create_fix_prompt(
            file_path, file_content, analysis_context, symbols
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert software engineer specializing in bug fixes. Analyze the provided code and alert context to propose specific, targeted fixes."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent fixes
                max_tokens=2000
            )
            
            # Parse AI response
            fix_content = response.choices[0].message.content
            return self._parse_fix_response(file_path, file_content, fix_content)
            
        except Exception as e:
            print(f"Error generating fix for {file_path}: {e}")
            return None
    
    def _create_fix_prompt(self, 
                          file_path: str,
                          file_content: str,
                          analysis_context: Dict[str, Any],
                          symbols: List[Dict[str, Any]]) -> str:
        """Create AI prompt for fix generation"""
        
        relevant_symbols = [
            s for s in symbols 
            if s['file'] == file_path
        ]
        
        prompt = f"""
ALERT CONTEXT:
- Error Message: {analysis_context.get('error_message', 'N/A')}
- Metric: {analysis_context.get('metric_name', 'N/A')}
- Namespace: {analysis_context.get('namespace', 'N/A')}
- Keywords: {', '.join(analysis_context.get('keywords', []))}

FILE TO ANALYZE: {file_path}

RELEVANT SYMBOLS IN FILE:
{chr(10).join([f"- {s['name']} ({s['type']})" for s in relevant_symbols[:10]])}

FILE CONTENT:
```
{file_content[:5000]}  # Limit content to avoid token limits
```

TASK:
1. Analyze the file content in context of the alert
2. Identify potential bug locations related to the error
3. Propose specific code changes to fix the issue
4. Explain your reasoning

RESPONSE FORMAT:
```json
{{
    "analysis": "Your analysis of the potential bug",
    "fix_needed": true/false,
    "proposed_changes": [
        {{
            "line_start": 10,
            "line_end": 15,
            "original_code": "original code here",
            "proposed_code": "fixed code here",
            "explanation": "why this fix addresses the issue"
        }}
    ],
    "confidence": 0.8,
    "fix_type": "bug_fix"
}}
```
"""
        return prompt
    
    def _parse_fix_response(self, 
                           file_path: str,
                           original_content: str,
                           ai_response: str) -> Optional[FixProposal]:
        """Parse AI response into FixProposal object"""
        import json
        import re
        
        try:
            # Extract JSON from response
            json_match = re.search(r'```json\n(.*?)\n```', ai_response, re.DOTALL)
            if not json_match:
                return None
            
            fix_data = json.loads(json_match.group(1))
            
            if not fix_data.get('fix_needed', False):
                return None
            
            # Apply proposed changes to create new content
            new_content = self._apply_changes(
                original_content, 
                fix_data.get('proposed_changes', [])
            )
            
            return FixProposal(
                file_path=file_path,
                original_code=original_content,
                proposed_code=new_content,
                explanation=fix_data.get('analysis', ''),
                confidence=fix_data.get('confidence', 0.5),
                fix_type=fix_data.get('fix_type', 'bug_fix')
            )
            
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return None
    
    def _apply_changes(self, 
                      original_content: str, 
                      changes: List[Dict[str, Any]]) -> str:
        """Apply proposed changes to original content"""
        lines = original_content.split('\n')
        
        # Sort changes by line number (descending) to avoid index issues
        changes.sort(key=lambda x: x.get('line_start', 0), reverse=True)
        
        for change in changes:
            start_line = change.get('line_start', 1) - 1  # Convert to 0-based
            end_line = change.get('line_end', start_line + 1) - 1
            new_code = change.get('proposed_code', '').split('\n')
            
            # Replace lines
            lines[start_line:end_line + 1] = new_code
        
        return '\n'.join(lines)
    
    def _read_file_content(self, repo_path: str, file_path: str) -> Optional[str]:
        """Read file content from repository"""
        full_path = os.path.join(repo_path, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None
```

### 1.5 Main Integration Layer

```python
# src/core/code_researcher_system.py
import asyncio
import tempfile
import shutil
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ..alerts.cloudwatch_handler import CloudWatchAlertHandler, CloudWatchAlert
from ..vcs.github_handler import GitHubHandler, RepositoryConfig
from ..agents.code_research_agents import CodeResearcherOrchestrator

@dataclass
class ResearchJob:
    job_id: str
    alert: CloudWatchAlert
    repositories: List[RepositoryConfig]
    status: str  # 'pending', 'analyzing', 'generating_fixes', 'creating_prs', 'completed', 'failed'
    orchestrator_response: Dict[str, Any] = None
    pull_requests: List[str] = None
    error_message: str = None

class CodeResearcherSystem:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize handlers
        self.alert_handler = CloudWatchAlertHandler(config.get('cloudwatch', {}))
        self.github_handler = GitHubHandler(config.get('github', {}).get('access_token'))
        
        # Initialize Strands orchestrator
        self.orchestrator = CodeResearcherOrchestrator()
        
        # Job tracking
        self.active_jobs: Dict[str, ResearchJob] = {}
    
    async def process_alert(self, alert_data: Dict[str, Any]) -> str:
        """Main entry point for processing alerts"""
        
        # Parse alert
        alert = self.alert_handler.process_alert(alert_data)
        
        # Create research job
        job_id = self._generate_job_id()
        repositories = self._get_configured_repositories()
        
        job = ResearchJob(
            job_id=job_id,
            alert=alert,
            repositories=repositories,
            status='pending'
        )
        
        self.active_jobs[job_id] = job
        
        # Start async processing
        asyncio.create_task(self._process_research_job(job))
        
        return job_id
    
    async def _process_research_job(self, job: ResearchJob):
        """Process a research job through all stages using Strands agents"""
        
        try:
            # Stage 1: Identify relevant repositories
            job.status = 'analyzing'
            relevant_repos = self.github_handler.identify_relevant_repositories(
                job.alert, 
                job.repositories
            )
            
            if not relevant_repos:
                job.status = 'failed'
                job.error_message = 'No relevant repositories found'
                return
            
            # Stage 2: Use Strands orchestrator for analysis and fix generation
            for repo_config in relevant_repos[:2]:  # Limit to top 2 repos
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
                        
                    except Exception as e:
                        print(f"Error processing repository {repo_config.name}: {e}")
                        job.error_message = str(e)
            
            job.status = 'completed' if job.pull_requests else 'failed'
            
        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
    
    def _format_alert_as_crash_report(self, alert: CloudWatchAlert) -> str:
        """Format CloudWatch alert as crash report for analysis"""
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
"""
    
    def _extract_fixes_from_orchestrator_response(self, 
                                                 orchestrator_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract fix proposals from orchestrator response"""
        fixes = []
        
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
                                import json
                                result_data = json.loads(tool_result['content'])
                                if 'patches' in result_data or 'proposed_changes' in result_data:
                                    fixes.append(result_data)
                            except:
                                # If not JSON, treat as text fix
                                fixes.append({
                                    'type': 'text_fix',
                                    'content': tool_result['content']
                                })
        
        return fixes
    
    async def _create_pull_request_for_fixes(self,
                                           repo_config: RepositoryConfig,
                                           fix_proposals: List[Dict[str, Any]],
                                           alert: CloudWatchAlert,
                                           orchestrator_result: Dict[str, Any]) -> str:
        """Create pull request with Strands-generated fixes"""
        
        # Generate branch name
        branch_name = f"auto-fix/{alert.alarm_name.lower().replace(' ', '-')}-{int(time.time())}"
        
        # Generate PR description with orchestrator insights
        pr_description = self._generate_strands_pr_description(
            alert, 
            fix_proposals, 
            orchestrator_result
        )
        
        # For now, create a documentation PR with the analysis
        # In a full implementation, you'd parse the actual code changes
        files = [{
            'path': 'CODE_RESEARCHER_ANALYSIS.md',
            'content': self._format_analysis_as_markdown(orchestrator_result),
            'commit_message': 'Add automated code analysis results'
        }]
        
        # Create PR
        pr_url = self.github_handler.create_pull_request(
            repo_config=repo_config,
            branch_name=branch_name,
            title=f"🤖 Code Researcher Analysis: {alert.alarm_name}",
            description=pr_description,
            files=files
        )
        
        return pr_url
    
    def _generate_strands_pr_description(self, 
                                       alert: CloudWatchAlert, 
                                       fix_proposals: List[Dict[str, Any]],
                                       orchestrator_result: Dict[str, Any]) -> str:
        """Generate PR description with Strands orchestrator insights"""
        
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
{orchestrator_result.get('response', 'Analysis completed successfully')}

### Proposed Changes
"""
        
        for i, fix in enumerate(fix_proposals, 1):
            description += f"""
#### {i}. Analysis Result
```
{json.dumps(fix, indent=2) if isinstance(fix, dict) else str(fix)}
```
"""
        
        description += """
### 🔍 How This Was Generated
1. CloudWatch alert was received and analyzed
2. Strands orchestrator agent coordinated the analysis
3. Specialized code analysis agent performed deep research
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
- **Analysis Agent**: Performed deep code research
- **Synthesis Agent**: Generated fix proposals
"""
        
        return description
    
    def _format_analysis_as_markdown(self, orchestrator_result: Dict[str, Any]) -> str:
        """Format orchestrator analysis as markdown documentation"""
        
        markdown = f"""# Code Researcher Analysis Report

## Analysis Summary
{orchestrator_result.get('response', 'Analysis completed')}

## Agent Messages
"""
        
        messages = orchestrator_result.get('messages', [])
        for i, message in enumerate(messages):
            markdown += f"""
### Message {i + 1}
```json
{json.dumps(message, indent=2) if isinstance(message, dict) else str(message)}
```
"""
        
        markdown += f"""
## Analysis Timestamp
Generated at: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}

## Next Steps
1. Review the analysis findings
2. Validate any proposed code changes
3. Test fixes in a staging environment
4. Deploy to production after verification
"""
        
        return markdown
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a research job"""
        job = self.active_jobs.get(job_id)
        if not job:
            return None
        
        return {
            'job_id': job.job_id,
            'status': job.status,
            'alert': {
                'alarm_name': job.alert.alarm_name,
                'timestamp': job.alert.timestamp
            },
            'repositories_analyzed': len(job.repositories),
            'pull_requests_created': len(job.pull_requests or []),
            'error_message': job.error_message,
            'has_orchestrator_response': job.orchestrator_response is not None
        }
    
    def _generate_job_id(self) -> str:
        """Generate unique job ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _get_configured_repositories(self) -> List[RepositoryConfig]:
        """Get list of configured repositories"""
        repos = []
        for repo_data in self.config.get('repositories', []):
            repos.append(RepositoryConfig(**repo_data))
        return repos
```

## Phase 2: Project Structure & Setup

### 2.1 Project Structure

```
code-researcher/
├── README.md
├── LICENSE
├── requirements.txt
├── setup.py
├── config/
│   ├── config.yaml.example
│   └── docker-compose.yml
├── src/
│   ├── __init__.py
│   ├── alerts/
│   │   ├── __init__.py
│   │   ├── cloudwatch_handler.py
│   │   ├── datadog_handler.py
│   │   └── newrelic_handler.py
│   ├── vcs/
│   │   ├── __init__.py
│   │   ├── github_handler.py
│   │   └── gitlab_handler.py
│   ├── agents/
│   │   ├── __init__.py
│   │   └── code_research_agents.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── code_researcher_system.py
│   └── api/
│       ├── __init__.py
│       ├── webhook_server.py
│       └── status_api.py
├── tests/
│   ├── __init__.py
│   ├── test_alerts/
│   ├── test_vcs/
│   ├── test_agents/
│   └── test_integration/
├── docs/
│   ├── setup.md
│   ├── configuration.md
│   ├── api-reference.md
│   └── examples/
└── scripts/
    ├── setup.sh
    └── deploy.sh
```

### 2.2 Requirements & Dependencies

```python
# requirements.txt
# AWS Strands SDK
strands-agents>=0.1.0
strands-tools>=0.1.0

# AWS Services
boto3>=1.34.0
botocore>=1.34.0

# VCS Integration
PyGithub>=2.1.1
python-gitlab>=4.2.0
GitPython>=3.1.40

# Web Framework
fastapi>=0.104.1
uvicorn>=0.24.0
pydantic>=2.5.0

# Utilities
pyyaml>=6.0.1
python-dotenv>=1.0.0
asyncio-mqtt>=0.16.1
httpx>=0.25.2

# Development
pytest>=7.4.3
pytest-asyncio>=0.21.1
black>=23.11.0
flake8>=6.1.0
mypy>=1.7.1
```

### 2.3 Configuration System

```yaml
# config/config.yaml.example
# Code Researcher Configuration

# AWS Bedrock Configuration
aws:
  region: us-east-1
  bedrock_model: anthropic.claude-sonnet-4-20250514-v1:0

# Alert Integrations
alerts:
  cloudwatch:
    enabled: true
    sns_topic_arn: arn:aws:sns:us-east-1:123456789:code-researcher-alerts
    webhook_url: https://your-domain.com/webhook/cloudwatch
  
  datadog:
    enabled: false
    api_key: your-datadog-api-key
    webhook_url: https://your-domain.com/webhook/datadog
  
  newrelic:
    enabled: false
    api_key: your-newrelic-api-key
    webhook_url: https://your-domain.com/webhook/newrelic

# VCS Configuration
vcs:
  github:
    access_token: your-github-token
    repositories:
      - owner: your-org
        name: backend-service
        branch: main
        alert_keywords: ["error", "exception", "crash", "timeout"]
        file_patterns: ["**/*.py", "**/*.js", "**/*.java"]
      - owner: your-org
        name: frontend-app
        branch: main
        alert_keywords: ["javascript", "react", "ui"]
        file_patterns: ["**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx"]
  
  gitlab:
    enabled: false
    access_token: your-gitlab-token
    base_url: https://gitlab.com  # or your self-hosted instance

# Server Configuration
server:
  host: 0.0.0.0
  port: 8000
  debug: false

# Logging
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### 2.4 Docker Setup

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    ctags \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create non-root user
RUN useradd -m -u 1000 coderesearcher && \
    chown -R coderesearcher:coderesearcher /app
USER coderesearcher

# Expose port
EXPOSE 8000

# Start application
CMD ["python", "-m", "src.api.webhook_server"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  code-researcher:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AWS_DEFAULT_REGION=us-east-1
      - CONFIG_PATH=/app/config/config.yaml
    volumes:
      - ./config/config.yaml:/app/config/config.yaml:ro
      - ./logs:/app/logs
    restart: unless-stopped
    
  # Optional: Redis for job queue (future enhancement)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

## Phase 3: Implementation Roadmap

### 3.1 Milestone 1: Core Foundation (Weeks 1-2)

**Week 1: Project Setup**
- [ ] Initialize repository structure
- [ ] Set up development environment
- [ ] Implement basic configuration system
- [ ] Create Docker setup
- [ ] Set up CI/CD pipeline (GitHub Actions)

**Week 2: CloudWatch Integration**
- [ ] Implement CloudWatch alert handler
- [ ] Create SNS webhook endpoint
- [ ] Add alert parsing and normalization
- [ ] Write unit tests for alert handling
- [ ] Create example CloudWatch alarm configurations

### 3.2 Milestone 2: VCS Integration (Weeks 3-4)

**Week 3: GitHub Integration**
- [ ] Implement GitHub API client
- [ ] Add repository cloning functionality
- [ ] Create repository relevance scoring
- [ ] Implement pull request creation
- [ ] Add GitHub webhook handling

**Week 4: GitLab Integration**
- [ ] Implement GitLab API client
- [ ] Add GitLab-specific features
- [ ] Create unified VCS interface
- [ ] Write integration tests
- [ ] Document VCS configuration

### 3.3 Milestone 3: Strands Agent System (Weeks 5-6)

**Week 5: Core Agents**
- [ ] Implement code analysis tools (ctags, git grep)
- [ ] Create analysis agent with Strands SDK
- [ ] Implement synthesis agent
- [ ] Add orchestrator agent
- [ ] Test agent-to-agent communication

**Week 6: Agent Integration**
- [ ] Integrate agents with VCS handlers
- [ ] Add error handling and retries
- [ ] Implement agent conversation logging
- [ ] Create agent performance metrics
- [ ] Write agent unit tests

### 3.4 Milestone 4: End-to-End Integration (Weeks 7-8)

**Week 7: System Integration**
- [ ] Connect all components
- [ ] Implement job tracking system
- [ ] Add status API endpoints
- [ ] Create webhook server
- [ ] Test complete workflow

**Week 8: Testing & Documentation**
- [ ] Write comprehensive integration tests
- [ ] Create setup documentation
- [ ] Add API documentation
- [ ] Create example configurations
- [ ] Performance testing and optimization

## Phase 4: Open Source Launch Strategy

### 4.1 Community Building

**Documentation**
- Comprehensive README with quick start guide
- Architecture documentation with diagrams
- API reference documentation
- Configuration examples for common scenarios
- Troubleshooting guide

**Examples & Demos**
- Sample CloudWatch alarm configurations
- Example repository setups
- Demo video showing end-to-end workflow
- Integration examples with popular services

**Community Engagement**
- GitHub Discussions for Q&A
- Contributing guidelines
- Code of conduct
- Issue templates
- PR templates

### 4.2 Release Strategy

**Alpha Release (v0.1.0)**
- Core functionality working
- CloudWatch + GitHub integration
- Basic documentation
- Docker deployment

**Beta Release (v0.2.0)**
- GitLab integration
- DataDog and New Relic support
- Enhanced error handling
- Performance improvements

**Stable Release (v1.0.0)**
- Production-ready
- Comprehensive documentation
- Security audit
- Performance benchmarks

### 4.3 Future Enhancements

**Phase 5: Advanced Features**
- Support for more VCS platforms (Bitbucket, Azure DevOps)
- Additional alerting integrations (PagerDuty, Grafana)
- Custom agent plugins
- Web UI for configuration and monitoring
- Metrics and analytics dashboard

**Phase 6: Enterprise Features**
- Multi-tenant support
- RBAC and authentication
- Audit logging
- SLA monitoring
- Professional support options

## Getting Started

### Quick Start

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

5. **Configure CloudWatch**
   ```bash
   # Create SNS topic and subscribe webhook
   aws sns create-topic --name code-researcher-alerts
   aws sns subscribe --topic-arn arn:aws:sns:us-east-1:123456789:code-researcher-alerts \
     --protocol https --notification-endpoint https://your-domain.com/webhook/cloudwatch
   ```

### Development Setup

1. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. **Run tests**
   ```bash
   pytest tests/
   ```

3. **Start development server**
   ```bash
   python -m src.api.webhook_server --reload
   ```

This open source implementation provides a solid foundation for the Code Researcher project using AWS Strands SDK, with a clear path from initial development to community-driven growth and eventual SaaS transformation.
```
```
```
