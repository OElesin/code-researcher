#!/usr/bin/env python3
"""
Script to render Graphviz DOT files using online services or alternative methods.
This is a workaround for when Graphviz is not installed locally.
"""

import os
import requests
import base64
from pathlib import Path

def render_with_online_service(dot_content, output_path, format='png'):
    """
    Render DOT content using an online Graphviz service.
    """
    try:
        # Using Graphviz Online API
        url = "https://quickchart.io/graphviz"
        
        params = {
            'graph': dot_content,
            'format': format
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"✅ Successfully rendered diagram to {output_path}")
            return True
        else:
            print(f"❌ Failed to render diagram. Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error rendering diagram: {e}")
        return False

def render_diagrams_in_directory(directory_path):
    """
    Find and render all DOT files in a directory.
    """
    directory = Path(directory_path)
    
    if not directory.exists():
        print(f"❌ Directory {directory_path} does not exist")
        return
    
    dot_files = list(directory.glob("*"))
    dot_files = [f for f in dot_files if f.is_file() and not f.name.endswith('.png')]
    
    if not dot_files:
        print(f"❌ No DOT files found in {directory_path}")
        return
    
    print(f"📁 Found {len(dot_files)} files to process...")
    
    for dot_file in dot_files:
        print(f"\n🔄 Processing {dot_file.name}...")
        
        try:
            with open(dot_file, 'r') as f:
                dot_content = f.read()
            
            # Check if it's a valid DOT file
            if not dot_content.strip().startswith('digraph'):
                print(f"⚠️  Skipping {dot_file.name} - doesn't appear to be a DOT file")
                continue
            
            output_path = dot_file.with_suffix('.png')
            
            if render_with_online_service(dot_content, output_path):
                print(f"✅ Rendered {dot_file.name} -> {output_path.name}")
            else:
                print(f"❌ Failed to render {dot_file.name}")
                
        except Exception as e:
            print(f"❌ Error processing {dot_file.name}: {e}")

def main():
    """
    Main function to render diagrams.
    """
    print("🎨 Code Researcher Diagram Renderer")
    print("=" * 40)
    
    # Default to generated-diagrams directory
    current_dir = Path(__file__).parent
    diagrams_dir = current_dir / "generated-diagrams"
    
    if diagrams_dir.exists():
        render_diagrams_in_directory(diagrams_dir)
    else:
        print(f"❌ Diagrams directory not found: {diagrams_dir}")
        print("Please ensure you have DOT files in the generated-diagrams directory")

if __name__ == "__main__":
    main()
