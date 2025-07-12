# Contributing to Code Researcher

We love your input! We want to make contributing to Code Researcher as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

### Development Setup

1. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/code-researcher.git
   cd code-researcher
   ```

2. **Run setup script**
   ```bash
   ./scripts/setup.sh
   ```

3. **Activate virtual environment**
   ```bash
   source venv/bin/activate
   ```

4. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

### Code Style

We use several tools to maintain code quality:

- **Black** for code formatting
- **flake8** for linting
- **mypy** for type checking
- **isort** for import sorting

Run all checks:
```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type check
mypy src/
```

### Testing

We use pytest for testing. Run tests with:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_alerts/test_cloudwatch_handler.py
```

### Writing Tests

- Write tests for all new functionality
- Use descriptive test names
- Include both positive and negative test cases
- Mock external dependencies (AWS services, GitHub API, etc.)

Example test structure:
```python
class TestMyFeature:
    def test_feature_success_case(self):
        """Test successful execution of feature."""
        # Arrange
        # Act
        # Assert
        
    def test_feature_error_case(self):
        """Test error handling in feature."""
        # Arrange
        # Act
        # Assert
```

## Issue Reporting

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/your-org/code-researcher/issues).

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Feature Requests

We welcome feature requests! Please:

1. Check if the feature has already been requested
2. Provide a clear description of the problem you're trying to solve
3. Describe the solution you'd like
4. Consider alternative solutions
5. Provide additional context

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

Examples of behavior that contributes to creating a positive environment include:

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

### Enforcement

Project maintainers are responsible for clarifying the standards of acceptable behavior and are expected to take appropriate and fair corrective action in response to any instances of unacceptable behavior.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Getting Help

- Join our [GitHub Discussions](https://github.com/your-org/code-researcher/discussions)
- Check the [documentation](docs/)
- Look at existing [issues](https://github.com/your-org/code-researcher/issues)

## Recognition

Contributors will be recognized in our README and release notes. We appreciate all contributions, no matter how small!

Thank you for contributing to Code Researcher! 🤖
