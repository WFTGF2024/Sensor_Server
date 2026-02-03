#!/bin/bash

# Test runner script for Sensor_Flask

set -e

echo "=========================================="
echo "Sensor_Flask Test Runner"
echo "=========================================="

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "pytest is not installed. Installing..."
    pip install pytest pytest-cov pytest-mock
fi

# Set test environment
export FLASK_ENV=testing
export FLASK_SECRET_KEY=test-secret-key-for-testing
export DB_NAME=modality_test

# Parse arguments
TEST_TYPE="${1:-all}"
COVERAGE="${2:-false}"

echo ""
echo "Running tests..."

if [ "$TEST_TYPE" = "unit" ]; then
    echo "Running unit tests only..."
    pytest tests/unit/ -v
elif [ "$TEST_TYPE" = "integration" ]; then
    echo "Running integration tests only..."
    pytest tests/integration/ -v
elif [ "$TEST_TYPE" = "all" ]; then
    echo "Running all tests..."
    pytest tests/ -v
else
    echo "Invalid test type: $TEST_TYPE"
    echo "Usage: ./run_tests.sh [all|unit|integration] [coverage]"
    exit 1
fi

if [ "$COVERAGE" = "coverage" ]; then
    echo ""
    echo "Generating coverage report..."
    pytest tests/ --cov=. --cov-report=html --cov-report=term
    echo "Coverage report generated in htmlcov/index.html"
fi

echo ""
echo "=========================================="
echo "Tests completed successfully!"
echo "=========================================="