import subprocess
import sys

# Try to create the database using psql
try:
    result = subprocess.run(
        ["psql", "-U", "postgres", "-c", "CREATE DATABASE retail_kpi;"],
        capture_output=True,
        text=True,
        timeout=10
    )
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
except Exception as e:
    print(f"Error: {e}")
    # Try using alter instead
    try:
        result = subprocess.run(
            ["psql", "-U", "postgres", "-c", "SELECT datname FROM pg_database WHERE datname='retail_kpi';"],
            capture_output=True,
            text=True,
            timeout=10
        )
        print("Database check:", result.stdout)
    except Exception as e2:
        print(f"Check error: {e2}")