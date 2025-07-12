#!/bin/bash

# Code Researcher Setup Script

set -e

echo "🤖 Code Researcher Setup"
echo "========================"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
required_version="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    echo "❌ Python 3.11+ is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Check for required system dependencies
echo "🔍 Checking system dependencies..."

check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not installed"
        return 1
    else
        echo "✅ $1 is available"
        return 0
    fi
}

missing_deps=0

check_command git || missing_deps=$((missing_deps + 1))
check_command ctags || missing_deps=$((missing_deps + 1))
check_command docker || missing_deps=$((missing_deps + 1))

if [ $missing_deps -gt 0 ]; then
    echo ""
    echo "Please install missing dependencies:"
    echo "  - git: Version control system"
    echo "  - ctags: Code indexing tool"
    echo "  - docker: Container runtime"
    echo ""
    echo "On Ubuntu/Debian: sudo apt-get install git ctags docker.io"
    echo "On macOS: brew install git ctags docker"
    exit 1
fi

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

if [ -f "requirements-dev.txt" ]; then
    echo "📦 Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

# Create configuration file if it doesn't exist
echo "⚙️  Setting up configuration..."
if [ ! -f "config/config.yaml" ]; then
    cp config/config.yaml.example config/config.yaml
    echo "✅ Configuration file created from example"
    echo "⚠️  Please edit config/config.yaml with your settings"
else
    echo "✅ Configuration file already exists"
fi

# Create logs directory
mkdir -p logs
echo "✅ Logs directory created"

# Run tests to verify installation
echo "🧪 Running tests to verify installation..."
if python -m pytest tests/ -v --tb=short; then
    echo "✅ All tests passed"
else
    echo "⚠️  Some tests failed - check your configuration"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit config/config.yaml with your AWS and GitHub credentials"
echo "2. Set up AWS credentials (aws configure or environment variables)"
echo "3. Start the server: python -m src.api.webhook_server"
echo "4. Or use Docker: docker-compose up"
echo ""
echo "For more information, see the README.md file."
