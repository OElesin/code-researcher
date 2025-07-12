# Technical Implementation Plan: Code Researcher with AWS Strands Agents

## Overview
This document outlines the technical implementation of the Code Researcher system using AWS Strands Agents SDK, based on the research paper analysis and Strands SDK examples.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                 Code Researcher Agent System                │
├─────────────────┬───────────────────┬─────────────────────┤
│ Orchestrator    │   Analysis Agent  │   Synthesis Agent   │
│ Agent           │   (Deep Research) │   (Patch Gen)       │
│ (Strands)       │   (Strands)       │   (Strands)         │
└─────────────────┴───────────────────┴─────────────────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
    ┌────────────────────────┼────────────────────────┐
    │                        │                        │
┌───────────┐    ┌──────────────────┐    ┌─────────────────┐
│Git Tools  │    │  Build Tools     │    │ Analysis Tools  │
│(Lambda)   │    │  (CodeBuild)     │    │   (Lambda)      │
└───────────┘    └──────────────────┘    └─────────────────┘
```

## Core Components

### 1. Agent Architecture (Multi-Agent with Agents-as-Tools Pattern)

Based on the Strands examples, we'll implement a hierarchical agent system:

#### A. Orchestrator Agent
```python
from strands import Agent, tool
from strands.models import BedrockModel

class CodeResearcherOrchestrator(Agent):
    def __init__(self):
        self.model = BedrockModel(
            model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            additional_request_fields={
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": 4096,
                }
            }
        )
        
        super().__init__(
            model=self.model,
            system_prompt=self._get_orchestrator_prompt(),
            tools=[
                self._create_analysis_agent_tool(),
                self._create_synthesis_agent_tool(),
                self._create_build_test_tool()
            ]
        )
    
    def _get_orchestrator_prompt(self):
        return """
        You are the Code Researcher Orchestrator, managing a team of specialized agents
        to analyze and fix complex software crashes.
        
        Your workflow:
        1. Receive crash report and repository information
        2. Delegate deep analysis to the Analysis Agent
        3. Once sufficient context is gathered, delegate patch generation to Synthesis Agent
        4. Coordinate build and testing of proposed fixes
        
        Available specialist agents:
        - analysis_agent: Deep code exploration and context gathering
        - synthesis_agent: Hypothesis generation and patch creation
        - build_test_agent: Code building and crash reproduction
        """
```

#### B. Analysis Agent (Deep Research Specialist)
```python
class CodeAnalysisAgent(Agent):
    def __init__(self):
        self.model = BedrockModel(
            model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            temperature=0.1  # Lower temperature for precise analysis
        )
        
        super().__init__(
            model=self.model,
            system_prompt=self._get_analysis_prompt(),
            tools=[
                SearchDefinitionTool(),
                SearchCodeTool(),
                SearchCommitsTool(),
                AnalyzeSymbolsTool()
            ]
        )
    
    def _get_analysis_prompt(self):
        return """
        You are a Code Analysis Specialist focused on deep research and context gathering.
        
        Your expertise:
        - Symbol definition analysis using ctags
        - Code pattern searching with git grep
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
```

#### C. Synthesis Agent (Patch Generation Specialist)
```python
class CodeSynthesisAgent(Agent):
    def __init__(self):
        self.model = BedrockModel(
            model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            temperature=0.3  # Slightly higher for creative solutions
        )
        
        super().__init__(
            model=self.model,
            system_prompt=self._get_synthesis_prompt(),
            tools=[
                GeneratePatchTool(),
                ValidatePatchTool(),
                ExplainFixTool()
            ]
        )
    
    def _get_synthesis_prompt(self):
        return """
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
```

### 2. Tool Implementation (AWS Lambda Functions)

#### A. Search Definition Tool
```python
@tool
def search_definition(symbol_name: str, file_path: str = None) -> str:
    """
    Search for symbol definitions using ctags in the codebase.
    
    Args:
        symbol_name: Name of the symbol to search for
        file_path: Optional specific file to search in
        
    Returns:
        JSON string containing symbol definitions with file locations and content
    """
    import boto3
    
    lambda_client = boto3.client('lambda')
    
    payload = {
        'action': 'search_definition',
        'symbol_name': symbol_name,
        'file_path': file_path,
        'repository_path': os.environ.get('REPO_PATH')
    }
    
    response = lambda_client.invoke(
        FunctionName='code-analysis-function',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    return json.dumps(result)
```

#### B. Search Code Tool
```python
@tool
def search_code(regex_pattern: str, context_lines: int = 2) -> str:
    """
    Search code patterns using git grep with context.
    
    Args:
        regex_pattern: Regular expression pattern to search
        context_lines: Number of context lines to include
        
    Returns:
        JSON string containing matching code snippets with context
    """
    import boto3
    
    lambda_client = boto3.client('lambda')
    
    payload = {
        'action': 'search_code',
        'pattern': regex_pattern,
        'context_lines': context_lines,
        'repository_path': os.environ.get('REPO_PATH')
    }
    
    response = lambda_client.invoke(
        FunctionName='code-analysis-function',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    return json.dumps(result)
```

#### C. Search Commits Tool
```python
@tool
def search_commits(query: str, search_type: str = "both") -> str:
    """
    Search git commit history for relevant changes.
    
    Args:
        query: Search query for commits
        search_type: "message", "code", or "both"
        
    Returns:
        JSON string containing relevant commits with diffs
    """
    import boto3
    
    lambda_client = boto3.client('lambda')
    
    payload = {
        'action': 'search_commits',
        'query': query,
        'search_type': search_type,
        'repository_path': os.environ.get('REPO_PATH')
    }
    
    response = lambda_client.invoke(
        FunctionName='git-operations-function',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    return json.dumps(result)
```

### 3. Agent-as-Tools Implementation

Following the Strands pattern for creating agents as tools:

```python
@tool
def analysis_agent(crash_report: str, repository_path: str) -> str:
    """
    Perform deep analysis of a crash report using specialized analysis agent.
    
    Args:
        crash_report: The crash report to analyze
        repository_path: Path to the code repository
        
    Returns:
        JSON string containing comprehensive analysis context
    """
    # Initialize analysis agent
    analysis_agent = CodeAnalysisAgent()
    
    # Set repository context
    os.environ['REPO_PATH'] = repository_path
    
    # Perform analysis
    analysis_prompt = f"""
    Analyze this crash report and gather comprehensive context:
    
    CRASH REPORT:
    {crash_report}
    
    REPOSITORY: {repository_path}
    
    Perform systematic analysis using your available tools.
    Continue until you have sufficient context to understand the root cause.
    """
    
    result = analysis_agent(analysis_prompt)
    
    # Extract analysis context from agent's conversation
    analysis_context = {
        'crash_report': crash_report,
        'repository_path': repository_path,
        'analysis_steps': [],
        'symbols_found': [],
        'relevant_commits': [],
        'root_cause_hypothesis': result.content
    }
    
    # Parse agent messages to extract tool usage
    for message in analysis_agent.messages:
        for content in message.get('content', []):
            if 'toolUse' in content:
                analysis_context['analysis_steps'].append({
                    'tool': content['toolUse']['name'],
                    'input': content['toolUse']['input']
                })
    
    return json.dumps(analysis_context)

@tool
def synthesis_agent(analysis_context: str) -> str:
    """
    Generate patches based on analysis context using specialized synthesis agent.
    
    Args:
        analysis_context: JSON string containing analysis results
        
    Returns:
        JSON string containing hypothesis and patches
    """
    # Initialize synthesis agent
    synthesis_agent = CodeSynthesisAgent()
    
    # Parse analysis context
    context = json.loads(analysis_context)
    
    # Generate synthesis prompt
    synthesis_prompt = f"""
    Based on the comprehensive analysis, generate a fix for this crash:
    
    ANALYSIS CONTEXT:
    {json.dumps(context, indent=2)}
    
    Provide:
    1. Root cause hypothesis
    2. Proposed patch with justification
    3. Explanation of how the fix addresses the root cause
    """
    
    result = synthesis_agent(synthesis_prompt)
    
    # Extract patch information
    synthesis_result = {
        'hypothesis': result.content,
        'patches': [],
        'justification': result.content
    }
    
    return json.dumps(synthesis_result)
```

### 4. Main Orchestrator Implementation

```python
class CodeResearcherSystem:
    def __init__(self):
        self.orchestrator = CodeResearcherOrchestrator()
        
    async def analyze_crash(self, crash_report: str, repository_path: str):
        """
        Main entry point for crash analysis using the orchestrator pattern.
        """
        
        # Create analysis request
        analysis_request = f"""
        I need to analyze and fix this software crash:
        
        CRASH REPORT:
        {crash_report}
        
        REPOSITORY: {repository_path}
        
        Please coordinate the analysis and synthesis process:
        1. Use the analysis_agent to perform deep research
        2. Once sufficient context is gathered, use synthesis_agent to generate fixes
        3. Provide a comprehensive report of findings and proposed solutions
        """
        
        # Stream the orchestrator's response
        async for event in self.orchestrator.stream_async(analysis_request):
            if event.type == "tool_use":
                print(f"Orchestrator calling: {event.tool_name}")
                print(f"Input: {event.tool_input}")
            elif event.type == "tool_result":
                print(f"Tool result: {event.content}")
            elif event.type == "content":
                print(f"Orchestrator: {event.content}")
                
        return self.orchestrator.messages[-1]['content']
```

### 5. Deployment Configuration

#### A. Serverless Framework Configuration
```yaml
# serverless.yml
service: code-researcher-strands

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  environment:
    PYTHONPATH: /opt/python
  
functions:
  orchestrator:
    handler: handlers/orchestrator.lambda_handler
    timeout: 900
    memorySize: 3008
    layers:
      - arn:aws:lambda:us-east-1:123456789:layer:strands-agents:1
    environment:
      BEDROCK_REGION: us-east-1
      
  code-analysis:
    handler: handlers/code_analysis.lambda_handler
    timeout: 300
    memorySize: 2048
    layers:
      - arn:aws:lambda:us-east-1:123456789:layer:git-tools:1
      
  git-operations:
    handler: handlers/git_operations.lambda_handler
    timeout: 300
    memorySize: 1024
    
  build-test:
    handler: handlers/build_test.lambda_handler
    timeout: 600
    memorySize: 2048

resources:
  Resources:
    AnalysisContextTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: ${self:service}-analysis-context
        BillingMode: PAY_PER_REQUEST
        AttributeDefinitions:
          - AttributeName: session_id
            AttributeType: S
        KeySchema:
          - AttributeName: session_id
            KeyType: HASH
        TimeToLiveSpecification:
          AttributeName: ttl
          Enabled: true
```

#### B. Lambda Layer for Strands Agents
```dockerfile
# Dockerfile for Strands layer
FROM public.ecr.aws/lambda/python:3.11

COPY requirements.txt .
RUN pip install -r requirements.txt -t /opt/python/

# requirements.txt
strands-agents>=0.1.0
strands-tools>=0.1.0
boto3>=1.34.0
```

### 6. Integration with Amazon Q Developer CLI

The system integrates with Amazon Q Developer CLI through:

#### A. CLI Command Interface
```python
# cli/code_researcher.py
import click
import asyncio
from code_researcher_system import CodeResearcherSystem

@click.command()
@click.option('--crash-report', required=True, help='Path to crash report file')
@click.option('--repository', required=True, help='Path to code repository')
@click.option('--output', help='Output file for results')
def analyze_crash(crash_report, repository, output):
    """Analyze and fix software crashes using Code Researcher."""
    
    # Read crash report
    with open(crash_report, 'r') as f:
        crash_content = f.read()
    
    # Initialize system
    system = CodeResearcherSystem()
    
    # Run analysis
    result = asyncio.run(system.analyze_crash(crash_content, repository))
    
    # Output results
    if output:
        with open(output, 'w') as f:
            json.dump(result, f, indent=2)
    else:
        print(json.dumps(result, indent=2))

if __name__ == '__main__':
    analyze_crash()
```

#### B. Q Developer Integration
```python
# Integration with Q Developer's MCP server
from mcp import Server
from code_researcher_system import CodeResearcherSystem

server = Server("code-researcher")

@server.tool()
async def analyze_kernel_crash(crash_report: str, repository_path: str):
    """Analyze Linux kernel crashes using Code Researcher agents."""
    system = CodeResearcherSystem()
    return await system.analyze_crash(crash_report, repository_path)

@server.tool()
async def get_analysis_status(session_id: str):
    """Get the status of an ongoing analysis."""
    # Implementation for status checking
    pass
```

## Key Implementation Benefits

1. **Modular Architecture**: Each agent has specialized responsibilities
2. **Scalable**: Can handle multiple concurrent analyses
3. **AWS Native**: Leverages Lambda, DynamoDB, and Bedrock
4. **Strands Integration**: Uses proven agent patterns and tools
5. **Q Developer Compatible**: Integrates with existing Q CLI workflows

## Next Steps

1. Implement core agent classes
2. Deploy Lambda functions and infrastructure
3. Create Strands agent tools
4. Integrate with Q Developer CLI
5. Test with real kernel crash scenarios
6. Optimize performance and cost

This implementation plan provides a solid foundation for building the Code Researcher system using AWS Strands Agents while maintaining the core research capabilities described in the original paper.
