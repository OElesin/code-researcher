"""GitHub integration handler for repository operations."""

import os
import git
import github
import logging
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RepositoryConfig:
    """Configuration for a repository."""
    owner: str
    name: str
    access_token: str
    branch: str = "main"
    file_patterns: List[str] = field(default_factory=lambda: ["**/*.py", "**/*.js", "**/*.java", "**/*.go"])
    alert_keywords: List[str] = field(default_factory=list)
    priority: str = "medium"  # low, medium, high
    
    @property
    def full_name(self) -> str:
        """Get full repository name."""
        return f"{self.owner}/{self.name}"


class GitHubHandler:
    """Handler for GitHub repository operations."""
    
    def __init__(self, access_token: str):
        """Initialize GitHub handler.
        
        Args:
            access_token: GitHub personal access token
        """
        self.access_token = access_token
        self.github = github.Github(access_token)
        
    def clone_repository(self, repo_config: RepositoryConfig, workspace_path: str) -> str:
        """Clone repository to local workspace.
        
        Args:
            repo_config: Repository configuration
            workspace_path: Local path to clone repository
            
        Returns:
            Path to cloned repository
        """
        try:
            repo_url = f"https://{self.access_token}@github.com/{repo_config.full_name}.git"
            
            logger.info(f"Cloning repository {repo_config.full_name} to {workspace_path}")
            
            # Clone repository
            repo = git.Repo.clone_from(
                repo_url,
                workspace_path,
                branch=repo_config.branch,
                depth=1  # Shallow clone for faster operation
            )
            
            logger.info(f"Successfully cloned {repo_config.full_name}")
            return workspace_path
            
        except Exception as e:
            logger.error(f"Error cloning repository {repo_config.full_name}: {e}")
            raise
    
    def identify_relevant_repositories(self, 
                                     alert: Any, 
                                     repo_configs: List[RepositoryConfig]) -> List[Tuple[RepositoryConfig, float]]:
        """Identify which repositories are relevant to the alert.
        
        Args:
            alert: Alert object with keywords
            repo_configs: List of repository configurations
            
        Returns:
            List of tuples (repo_config, relevance_score) sorted by relevance
        """
        try:
            # Extract keywords from alert
            alert_keywords = self._extract_alert_keywords(alert)
            logger.info(f"Alert keywords: {alert_keywords}")
            
            relevant_repos = []
            
            for repo_config in repo_configs:
                relevance_score = self._calculate_relevance_score(
                    alert_keywords, 
                    repo_config
                )
                
                if relevance_score > 0.1:  # Minimum threshold for relevance
                    relevant_repos.append((repo_config, relevance_score))
                    logger.info(f"Repository {repo_config.full_name} relevance: {relevance_score:.2f}")
            
            # Sort by relevance score (descending) and return top 3
            relevant_repos.sort(key=lambda x: x[1], reverse=True)
            return relevant_repos[:3]
            
        except Exception as e:
            logger.error(f"Error identifying relevant repositories: {e}")
            return []
    
    def create_pull_request(self, 
                          repo_config: RepositoryConfig,
                          branch_name: str,
                          title: str,
                          description: str,
                          files: List[Dict[str, str]]) -> str:
        """Create pull request with proposed fixes.
        
        Args:
            repo_config: Repository configuration
            branch_name: Name of the branch to create
            title: Pull request title
            description: Pull request description
            files: List of files to commit (path, content, commit_message)
            
        Returns:
            URL of created pull request
        """
        try:
            repo = self.github.get_repo(repo_config.full_name)
            
            # Get base branch
            base_branch = repo.get_branch(repo_config.branch)
            
            # Create new branch
            logger.info(f"Creating branch {branch_name} in {repo_config.full_name}")
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
                        message=file_info.get('commit_message', 'Auto-fix: Bug fix'),
                        content=file_info['content'],
                        sha=existing_file.sha,
                        branch=branch_name
                    )
                    logger.info(f"Updated file {file_info['path']}")
                    
                except github.UnknownObjectException:
                    # File doesn't exist, create new
                    repo.create_file(
                        path=file_info['path'],
                        message=file_info.get('commit_message', 'Auto-fix: Bug fix'),
                        content=file_info['content'],
                        branch=branch_name
                    )
                    logger.info(f"Created file {file_info['path']}")
            
            # Create pull request
            logger.info(f"Creating pull request in {repo_config.full_name}")
            pr = repo.create_pull(
                title=title,
                body=description,
                head=branch_name,
                base=repo_config.branch
            )
            
            # Add labels
            try:
                pr.add_to_labels("automated-fix", "needs-review", "code-researcher")
            except Exception as e:
                logger.warning(f"Could not add labels to PR: {e}")
            
            logger.info(f"Created pull request: {pr.html_url}")
            return pr.html_url
            
        except Exception as e:
            logger.error(f"Error creating pull request in {repo_config.full_name}: {e}")
            raise
    
    def get_repository_info(self, repo_config: RepositoryConfig) -> Dict[str, Any]:
        """Get repository information and metadata.
        
        Args:
            repo_config: Repository configuration
            
        Returns:
            Dictionary with repository information
        """
        try:
            repo = self.github.get_repo(repo_config.full_name)
            
            return {
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description,
                'language': repo.language,
                'languages': repo.get_languages(),
                'topics': repo.get_topics(),
                'default_branch': repo.default_branch,
                'size': repo.size,
                'stargazers_count': repo.stargazers_count,
                'forks_count': repo.forks_count,
                'open_issues_count': repo.open_issues_count,
                'created_at': repo.created_at.isoformat(),
                'updated_at': repo.updated_at.isoformat(),
                'pushed_at': repo.pushed_at.isoformat() if repo.pushed_at else None
            }
            
        except Exception as e:
            logger.error(f"Error getting repository info for {repo_config.full_name}: {e}")
            return {}
    
    def _extract_alert_keywords(self, alert: Any) -> List[str]:
        """Extract searchable keywords from alert.
        
        Args:
            alert: Alert object
            
        Returns:
            List of keywords extracted from the alert
        """
        keywords = []
        
        # Try to extract keywords using different methods based on alert type
        if hasattr(alert, 'extract_keywords'):
            # CloudWatch alert with extract_keywords method
            keywords = alert.extract_keywords()
        elif hasattr(alert, 'alarm_name'):
            # CloudWatch alert object
            keywords.extend(self._extract_words_from_text(alert.alarm_name))
            if hasattr(alert, 'namespace') and alert.namespace:
                keywords.extend(self._extract_words_from_text(alert.namespace))
            if hasattr(alert, 'metric_name') and alert.metric_name:
                keywords.extend(self._extract_words_from_text(alert.metric_name))
        elif isinstance(alert, dict):
            # Dictionary-based alert
            for key in ['alarm_name', 'metric_name', 'namespace', 'message', 'title']:
                if key in alert and alert[key]:
                    keywords.extend(self._extract_words_from_text(str(alert[key])))
        else:
            # Fallback: convert to string and extract words
            keywords.extend(self._extract_words_from_text(str(alert)))
        
        # Remove duplicates and filter short words
        return list(set([word for word in keywords if len(word) > 2]))
    
    def _extract_words_from_text(self, text: str) -> List[str]:
        """Extract meaningful words from text.
        
        Args:
            text: Input text
            
        Returns:
            List of extracted words
        """
        import re
        
        # Convert to lowercase and split on non-alphanumeric characters
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common stop words and short words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        return [word for word in words if word not in stop_words and len(word) > 2]
    
    def _calculate_relevance_score(self, 
                                 alert_keywords: List[str], 
                                 repo_config: RepositoryConfig) -> float:
        """Calculate relevance score between alert and repository.
        
        Args:
            alert_keywords: Keywords extracted from alert
            repo_config: Repository configuration
            
        Returns:
            Relevance score between 0 and 1
        """
        if not alert_keywords:
            return 0.0
        
        score = 0.0
        
        # Base score for having any keywords
        if repo_config.alert_keywords:
            # Calculate keyword overlap
            alert_set = set(alert_keywords)
            repo_set = set([kw.lower() for kw in repo_config.alert_keywords])
            
            overlap = alert_set & repo_set
            if overlap:
                score += len(overlap) / len(alert_set) * 0.8
        else:
            # If no specific keywords configured, give default relevance
            score = 0.3
        
        # Boost score based on repository priority
        priority_boost = {
            'high': 0.2,
            'medium': 0.1,
            'low': 0.0
        }
        score += priority_boost.get(repo_config.priority, 0.0)
        
        # Boost score if alert keywords match repository name
        repo_name_words = self._extract_words_from_text(repo_config.name)
        name_overlap = set(alert_keywords) & set(repo_name_words)
        if name_overlap:
            score += len(name_overlap) / len(alert_keywords) * 0.3
        
        return min(score, 1.0)  # Cap at 1.0
