# Diagram Rendering Guide

This guide explains how to render diagrams in the Code Researcher project when Graphviz is not available locally.

## Problem

The `diagrams` Python package generates Graphviz DOT files but requires Graphviz to be installed locally to render them as PNG/SVG images. When Graphviz installation fails due to system constraints (disk space, dependencies, etc.), we need an alternative solution.

## Solution

We've implemented an online diagram rendering system that uses web services to convert DOT files to images without requiring local Graphviz installation.

## Components

### 1. Diagram Renderer Module (`src/utils/diagram_renderer.py`)

A comprehensive utility class that:
- Renders DOT content to images using online services
- Handles multiple fallback services for reliability
- Provides both programmatic and file-based interfaces
- Includes validation and error handling

### 2. Simple Renderer Script (`render_diagrams.py`)

A standalone script for quick diagram rendering:
```bash
python render_diagrams.py
```

### 3. Test Suite (`test_diagram_renderer.py`)

Validates the rendering functionality:
```bash
python test_diagram_renderer.py
```

## Usage

### Basic Usage

```python
from src.utils.diagram_renderer import render_diagram

# Render DOT content directly
dot_content = '''
digraph G {
    A -> B;
    B -> C;
}
'''

success = render_diagram(dot_content, "output.png")
```

### File-based Rendering

```python
from src.utils.diagram_renderer import render_diagram_file

# Render a DOT file
success = render_diagram_file("diagram.dot", "diagram.png")
```

### Batch Rendering

```python
from src.utils.diagram_renderer import DiagramRenderer

renderer = DiagramRenderer()
results = renderer.render_directory("generated-diagrams/")
```

### Integration with Diagrams Package

When using the `diagrams` package, you can now render the generated DOT files:

```python
from diagrams import Diagram
from diagrams.aws.compute import Lambda
from diagrams.aws.integration import SNS
from src.utils.diagram_renderer import render_diagram_file

# Generate diagram (creates DOT file)
with Diagram("My Architecture", filename="my_arch", show=False):
    lambda_fn = Lambda("Function")
    sns = SNS("Topic")
    sns >> lambda_fn

# Render the DOT file to PNG
render_diagram_file("my_arch", "my_arch.png")
```

## Online Services

The renderer currently uses:

1. **QuickChart Graphviz API**
   - URL: `https://quickchart.io/graphviz`
   - Method: GET
   - Formats: PNG, SVG
   - Limitations: Public service, rate limits may apply

## Configuration

### Timeout Settings

```python
renderer = DiagramRenderer(timeout=60)  # 60 second timeout
```

### Adding New Services

To add additional online rendering services, modify the `online_services` list in `DiagramRenderer.__init__()`:

```python
self.online_services.append({
    'name': 'New Service',
    'url': 'https://api.example.com/render',
    'method': 'POST',
    'params_key': 'dot_content'
})
```

## Error Handling

The renderer includes comprehensive error handling:

- **Network errors**: Automatic fallback to alternative services
- **Invalid DOT content**: Validation before rendering
- **File system errors**: Proper error messages and logging
- **Service failures**: Graceful degradation

## Limitations

1. **Internet dependency**: Requires internet connection
2. **Service availability**: Dependent on third-party services
3. **File size limits**: Online services may have size restrictions
4. **Rate limiting**: Public services may impose rate limits

## Troubleshooting

### Common Issues

1. **No internet connection**
   ```
   Error: All rendering services failed
   ```
   Solution: Check internet connectivity

2. **Invalid DOT content**
   ```
   Error: Invalid DOT content in file.dot
   ```
   Solution: Verify DOT file syntax

3. **Service unavailable**
   ```
   Warning: Service returned status code: 503
   ```
   Solution: Try again later or add alternative services

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.INFO)

from src.utils.diagram_renderer import DiagramRenderer
renderer = DiagramRenderer()
```

## Performance

- **Rendering time**: 2-10 seconds per diagram (network dependent)
- **File size**: Supports diagrams up to ~1MB DOT content
- **Concurrent rendering**: Not implemented (sequential processing)

## Security Considerations

- DOT content is sent to third-party services
- Avoid including sensitive information in diagrams
- Consider using private rendering services for sensitive content

## Future Improvements

1. **Local fallback**: Attempt local Graphviz if available
2. **Caching**: Cache rendered images to avoid re-rendering
3. **Async rendering**: Support concurrent diagram rendering
4. **Private services**: Support for private/enterprise rendering services
5. **Format options**: Support for additional output formats (PDF, EPS, etc.)

## Dependencies

- `requests>=2.32.0`: HTTP client for online services
- `pathlib`: File path handling (built-in)
- `logging`: Error reporting (built-in)

## Examples

See the `test_diagram_renderer.py` file for complete examples of:
- Simple diagram rendering
- Batch processing
- Error handling
- Integration patterns

## Support

For issues with diagram rendering:
1. Check the troubleshooting section
2. Verify internet connectivity
3. Test with simple diagrams first
4. Check service status at https://quickchart.io/
