"""Verify that the Time Series Platform is set up correctly.

This script checks:
1. Docker services are running
2. API is accessible
3. Database is initialized
4. Sample data exists
"""

import httpx
import sys
import time
from pathlib import Path


def check_api():
    """Check if API is running."""
    print("Checking API...")
    try:
        response = httpx.get("http://localhost:8000/health", timeout=5.0)
        if response.status_code == 200:
            print("✓ API is running")
            return True
        else:
            print("✗ API returned unexpected status:", response.status_code)
            return False
    except Exception as e:
        print(f"✗ API is not accessible: {e}")
        print("  Make sure to run: docker-compose up -d")
        return False


def check_web():
    """Check if web client is running."""
    print("\nChecking web client...")
    try:
        response = httpx.get("http://localhost:3000", timeout=5.0)
        if response.status_code == 200:
            print("✓ Web client is running")
            return True
        else:
            print("✗ Web client returned unexpected status:", response.status_code)
            return False
    except Exception as e:
        print(f"✗ Web client is not accessible: {e}")
        return False


def check_database():
    """Check if database is accessible."""
    print("\nChecking database...")
    try:
        response = httpx.get("http://localhost:8000/api/datasets/", timeout=5.0)
        if response.status_code == 200:
            print("✓ Database is accessible")
            return True
        else:
            print("✗ Database check failed:", response.status_code)
            return False
    except Exception as e:
        print(f"✗ Database is not accessible: {e}")
        return False


def check_sample_data():
    """Check if sample data exists."""
    print("\nChecking sample data...")
    sample_path = Path("data/sample_timeseries.csv")
    if sample_path.exists():
        size_mb = sample_path.stat().st_size / 1024 / 1024
        print(f"✓ Sample data exists ({size_mb:.2f} MB)")
        return True
    else:
        print("✗ Sample data not found")
        print("  Run: python scripts/generate_sample_data.py")
        return False


def main():
    print("="*60)
    print("Time Series Platform - Setup Verification")
    print("="*60)

    checks = [
        check_api,
        check_web,
        check_database,
        check_sample_data
    ]

    results = [check() for check in checks]

    print("\n" + "="*60)
    if all(results):
        print("SUCCESS! All checks passed.")
        print("\nNext steps:")
        print("1. Open web client: http://localhost:3000")
        print("2. View API docs: http://localhost:8000/docs")
        print("3. Run example: python examples/basic_workflow.py")
    else:
        print("FAILED! Some checks did not pass.")
        print("\nTroubleshooting:")
        print("1. Start services: docker-compose up -d")
        print("2. Check logs: docker-compose logs -f")
        print("3. Generate data: python scripts/generate_sample_data.py")
        sys.exit(1)

    print("="*60)


if __name__ == "__main__":
    main()
