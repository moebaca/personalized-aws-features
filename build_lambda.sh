#!/bin/bash
# Build Lambda deployment package using Poetry

set -e

# Clean up any previous builds
rm -rf dist package terraform/lambda_function.zip

# Build the wheel
echo "Building wheel with Poetry..."
poetry build -f wheel

# Create package directory and install the wheel
echo "Installing dependencies and wheel..."
mkdir -p package
pip install --upgrade -t package dist/*.whl

# Copy the Lambda handler to the package root
echo "Copying Lambda handler..."
cp src/personalized_aws_features/lambda_function.py package/

# Create ZIP package
echo "Creating ZIP archive..."
cd package
zip -r ../terraform/lambda_function.zip . -x '*.pyc'
cd ..

echo "Lambda package created at terraform/lambda_function.zip"