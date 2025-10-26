#!/bin/bash
# Format all Python code in the project

set -e

echo "🔧 Formatting Python code..."

# Activate virtual environment
source .venv313/bin/activate

# Format with black
echo "📝 Running black formatter..."
black app/ ui/ *.py

# Sort imports with isort
echo "📦 Sorting imports with isort..."
isort app/ ui/ *.py

# Check for linting issues
echo "🔍 Running flake8 linter..."
flake8 app/ ui/ *.py

echo "✅ Code formatting complete!"
