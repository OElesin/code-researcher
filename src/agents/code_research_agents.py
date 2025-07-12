"""Strands agents for automated code research and fix generation."""

import os
import json
import subprocess
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from strands import Agent, tool
from strands.models import BedrockModel

logger = logging.getLogger(__name__)


@dataclass
class FixProposal:
    """Data structure for fix proposals."""
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

Always be thorough in your analysis and use multiple tools to gather comprehensive context.
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

Focus on creating safe, targeted fixes that address the root cause without introducing new issues.
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
Ensure thorough analysis before moving to synthesis phase.
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
        # Use environment variable if repository_path not provided
        if not repository_path:
            repository_path = os.environ.get('CURRENT_REPO_PATH', '.')
        
        logger.info(f"Searching for symbol '{symbol_name}' in {repository_path}")
        
        # Generate ctags if not exists
        ctags_file = os.path.join(repository_path, 'tags')
        if not os.path.exists(ctags_file):
            logger.info("Generating ctags...")
            subprocess.run([
                'ctags', '-R', '--fields=+iaS', '--extra=+q', '.'
            ], cwd=repository_path, check=True, capture_output=True)
        
        # Search for symbol
        results = []
        if os.path.exists(ctags_file):
            with open(ctags_file, 'r') as f:
                for line in f:
                    if not line.startswith('!') and symbol_name in line:
                        parts = line.strip().split('\t')
                        if len(parts) >= 3 and parts[0] == symbol_name:
                            # Get file content around the definition
                            file_path = os.path.join(repository_path, parts[1])
                            context = _get_file_context(file_path, parts[2])
                            
                            results.append({
                                'symbol': parts[0],
                                'file': parts[1],
                                'pattern': parts[2],
                                'type': parts[3] if len(parts) > 3 else 'unknown',
                                'context': context
                            })
        
        logger.info(f"Found {len(results)} definitions for '{symbol_name}'")
        return json.dumps(results, indent=2)
        
    except Exception as e:
        logger.error(f"Error searching for symbol '{symbol_name}': {e}")
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
        # Use environment variable if repository_path not provided
        if not repository_path:
            repository_path = os.environ.get('CURRENT_REPO_PATH', '.')
        
        logger.info(f"Searching for pattern '{pattern}' in {repository_path}")
        
        result = subprocess.run([
            'git', 'grep', '-n', f'-C{context_lines}', pattern
        ], cwd=repository_path, capture_output=True, text=True)
        
        if result.returncode == 0:
            matches = []
            current_file = None
            current_match = {'file': '', 'lines': []}
            
            for line in result.stdout.split('\n'):
                if ':' in line and line.strip():
                    parts = line.split(':', 2)
                    if len(parts) >= 2:
                        file_part = parts[0]
                        line_num = parts[1] if len(parts) > 2 else ''
                        content = parts[2] if len(parts) > 2 else parts[1]
                        
                        if file_part != current_file:
                            if current_match['lines']:
                                matches.append(current_match)
                            current_file = file_part
                            current_match = {'file': file_part, 'lines': []}
                        
                        current_match['lines'].append({
                            'line_number': line_num,
                            'content': content
                        })
            
            if current_match['lines']:
                matches.append(current_match)
            
            logger.info(f"Found {len(matches)} matches for pattern '{pattern}'")
            return json.dumps(matches, indent=2)
        else:
            logger.info(f"No matches found for pattern '{pattern}'")
            return json.dumps({'message': 'No matches found'})
            
    except Exception as e:
        logger.error(f"Error searching for pattern '{pattern}': {e}")
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
        # Use environment variable if repository_path not provided
        if not repository_path:
            repository_path = os.environ.get('CURRENT_REPO_PATH', '.')
        
        logger.info(f"Searching commits for '{query}' in {repository_path}")
        
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
                        
                        # Get diff summary for this commit
                        diff_result = subprocess.run([
                            'git', 'show', '--stat', '--format=', commit_hash
                        ], cwd=repository_path, capture_output=True, text=True)
                        
                        commits.append({
                            'hash': commit_hash,
                            'message': parts[1],
                            'author': parts[2],
                            'date': parts[3],
                            'diff_summary': diff_result.stdout[:1000] if diff_result.returncode == 0 else ''
                        })
        
        logger.info(f"Found {len(commits)} commits for query '{query}'")
        return json.dumps(commits, indent=2)
        
    except Exception as e:
        logger.error(f"Error searching commits for '{query}': {e}")
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
        # Use environment variable if repository_path not provided
        if not repository_path:
            repository_path = os.environ.get('CURRENT_REPO_PATH', '.')
        
        logger.info(f"Generating patch for {file_path}")
        
        # Read file content
        full_path = os.path.join(repository_path, file_path)
        if not os.path.exists(full_path):
            return json.dumps({'error': f'File {file_path} not found'})
        
        with open(full_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # Parse analysis context
        try:
            context = json.loads(analysis_context)
        except json.JSONDecodeError:
            context = {'analysis': analysis_context}
        
        # Create a simple patch generation agent
        patch_agent = Agent(
            system_prompt="""You are a code patch generator. Based on the analysis context and file content,
            generate a specific patch to fix the identified issue. Return your response as JSON with:
            - analysis: your understanding of the issue
            - fix_needed: true/false
            - proposed_changes: list of specific line changes
            - explanation: why this fix addresses the root cause
            - confidence: confidence score 0-1""",
            model=BedrockModel(model_id="anthropic.claude-sonnet-4-20250514-v1:0")
        )
        
        prompt = f"""
        ANALYSIS CONTEXT:
        {json.dumps(context, indent=2)}
        
        FILE TO PATCH: {file_path}
        FILE CONTENT:
        {file_content[:3000]}  # Limit to avoid token limits
        
        Generate a patch to fix the identified issue. Respond with valid JSON only.
        """
        
        response = patch_agent(prompt)
        logger.info(f"Generated patch for {file_path}")
        return str(response)
        
    except Exception as e:
        logger.error(f"Error generating patch for {file_path}: {e}")
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
        logger.info(f"Starting code analysis for repository: {repository_path}")
        
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
        Focus on finding relevant code patterns, symbols, and historical fixes.
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
        
        logger.info("Code analysis completed successfully")
        return json.dumps(analysis_context, indent=2)
        
    except Exception as e:
        logger.error(f"Error in code analysis: {e}")
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
        logger.info(f"Starting code synthesis for repository: {repository_path}")
        
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
        
        Use the generate_patch tool to create specific code changes.
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
        
        logger.info("Code synthesis completed successfully")
        return json.dumps(synthesis_result, indent=2)
        
    except Exception as e:
        logger.error(f"Error in code synthesis: {e}")
        return json.dumps({'error': str(e)})


# Main Orchestrator Agent
class CodeResearcherOrchestrator:
    """Main orchestrator for code research using Strands agents."""
    
    def __init__(self):
        """Initialize the orchestrator with specialized agents."""
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
    
    async def analyze_crash(self, crash_report: str, repository_path: str) -> Dict[str, Any]:
        """
        Main entry point for crash analysis using the orchestrator pattern.
        
        Args:
            crash_report: The crash report to analyze
            repository_path: Path to the repository
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            logger.info(f"Starting orchestrated analysis for crash in {repository_path}")
            
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
            
            result = {
                'response': str(response),
                'messages': self.orchestrator.messages,
                'analysis_complete': True,
                'repository_path': repository_path
            }
            
            logger.info("Orchestrated analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in orchestrated analysis: {e}")
            return {
                'response': f"Error: {str(e)}",
                'messages': [],
                'analysis_complete': False,
                'error': str(e)
            }


def _get_file_context(file_path: str, pattern: str, context_lines: int = 3) -> str:
    """Get context around a pattern in a file.
    
    Args:
        file_path: Path to the file
        pattern: Pattern to search for
        context_lines: Number of context lines
        
    Returns:
        Context around the pattern
    """
    try:
        if not os.path.exists(file_path):
            return "File not found"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find the pattern in the file
        for i, line in enumerate(lines):
            if pattern.strip('/^$') in line:  # Remove regex anchors
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                context = ''.join(lines[start:end])
                return context
        
        return "Pattern not found in file"
        
    except Exception as e:
        return f"Error reading file: {e}"
