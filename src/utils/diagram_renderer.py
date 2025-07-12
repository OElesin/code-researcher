"""
Diagram rendering utilities for Code Researcher.

This module provides functionality to render Graphviz DOT files to images
using online services when Graphviz is not available locally.
"""

import os
import requests
import logging
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

class DiagramRenderer:
    """
    A utility class for rendering Graphviz DOT files to images.
    """
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the diagram renderer.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.online_services = [
            {
                'name': 'QuickChart Graphviz',
                'url': 'https://quickchart.io/graphviz',
                'method': 'GET',
                'params_key': 'graph'
            }
        ]
    
    def render_dot_to_image(
        self, 
        dot_content: str, 
        output_path: Union[str, Path], 
        format: str = 'png'
    ) -> bool:
        """
        Render DOT content to an image file.
        
        Args:
            dot_content: The Graphviz DOT content
            output_path: Path where the image should be saved
            format: Output format (png, svg, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        output_path = Path(output_path)
        
        # Try each online service
        for service in self.online_services:
            try:
                logger.info(f"Attempting to render using {service['name']}")
                
                if self._render_with_service(dot_content, output_path, format, service):
                    logger.info(f"Successfully rendered diagram using {service['name']}")
                    return True
                    
            except Exception as e:
                logger.warning(f"Failed to render with {service['name']}: {e}")
                continue
        
        logger.error("All rendering services failed")
        return False
    
    def _render_with_service(
        self, 
        dot_content: str, 
        output_path: Path, 
        format: str, 
        service: dict
    ) -> bool:
        """
        Render using a specific online service.
        
        Args:
            dot_content: The DOT content
            output_path: Output file path
            format: Output format
            service: Service configuration
            
        Returns:
            True if successful, False otherwise
        """
        if service['method'] == 'GET':
            params = {
                service['params_key']: dot_content,
                'format': format
            }
            response = requests.get(
                service['url'], 
                params=params, 
                timeout=self.timeout
            )
        else:
            # For POST requests (if needed in future)
            data = {
                service['params_key']: dot_content,
                'format': format
            }
            response = requests.post(
                service['url'], 
                data=data, 
                timeout=self.timeout
            )
        
        if response.status_code == 200:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            logger.warning(f"Service returned status code: {response.status_code}")
            return False
    
    def render_file(
        self, 
        dot_file_path: Union[str, Path], 
        output_path: Optional[Union[str, Path]] = None,
        format: str = 'png'
    ) -> bool:
        """
        Render a DOT file to an image.
        
        Args:
            dot_file_path: Path to the DOT file
            output_path: Output path (defaults to same name with .png extension)
            format: Output format
            
        Returns:
            True if successful, False otherwise
        """
        dot_file_path = Path(dot_file_path)
        
        if not dot_file_path.exists():
            logger.error(f"DOT file not found: {dot_file_path}")
            return False
        
        if output_path is None:
            output_path = dot_file_path.with_suffix(f'.{format}')
        else:
            output_path = Path(output_path)
        
        try:
            with open(dot_file_path, 'r') as f:
                dot_content = f.read()
            
            # Validate DOT content
            if not self._is_valid_dot_content(dot_content):
                logger.error(f"Invalid DOT content in {dot_file_path}")
                return False
            
            return self.render_dot_to_image(dot_content, output_path, format)
            
        except Exception as e:
            logger.error(f"Error reading DOT file {dot_file_path}: {e}")
            return False
    
    def _is_valid_dot_content(self, content: str) -> bool:
        """
        Check if content appears to be valid DOT format.
        
        Args:
            content: The content to validate
            
        Returns:
            True if valid, False otherwise
        """
        content = content.strip()
        return (
            content.startswith('digraph') or 
            content.startswith('graph') or 
            content.startswith('strict digraph') or
            content.startswith('strict graph')
        )
    
    def render_directory(
        self, 
        directory_path: Union[str, Path], 
        pattern: str = "*",
        format: str = 'png'
    ) -> dict:
        """
        Render all DOT files in a directory.
        
        Args:
            directory_path: Directory containing DOT files
            pattern: File pattern to match
            format: Output format
            
        Returns:
            Dictionary with results for each file
        """
        directory_path = Path(directory_path)
        results = {}
        
        if not directory_path.exists():
            logger.error(f"Directory not found: {directory_path}")
            return results
        
        # Find DOT files
        dot_files = []
        for file_path in directory_path.glob(pattern):
            if file_path.is_file():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    if self._is_valid_dot_content(content):
                        dot_files.append(file_path)
                except:
                    continue
        
        logger.info(f"Found {len(dot_files)} DOT files to render")
        
        for dot_file in dot_files:
            logger.info(f"Rendering {dot_file.name}")
            success = self.render_file(dot_file, format=format)
            results[str(dot_file)] = success
            
            if success:
                logger.info(f"✅ Successfully rendered {dot_file.name}")
            else:
                logger.error(f"❌ Failed to render {dot_file.name}")
        
        return results


# Convenience functions
def render_diagram(
    dot_content: str, 
    output_path: Union[str, Path], 
    format: str = 'png'
) -> bool:
    """
    Convenience function to render a diagram from DOT content.
    
    Args:
        dot_content: The Graphviz DOT content
        output_path: Where to save the rendered image
        format: Output format (png, svg, etc.)
        
    Returns:
        True if successful, False otherwise
    """
    renderer = DiagramRenderer()
    return renderer.render_dot_to_image(dot_content, output_path, format)


def render_diagram_file(
    dot_file_path: Union[str, Path], 
    output_path: Optional[Union[str, Path]] = None,
    format: str = 'png'
) -> bool:
    """
    Convenience function to render a diagram from a DOT file.
    
    Args:
        dot_file_path: Path to the DOT file
        output_path: Output path (optional)
        format: Output format
        
    Returns:
        True if successful, False otherwise
    """
    renderer = DiagramRenderer()
    return renderer.render_file(dot_file_path, output_path, format)
