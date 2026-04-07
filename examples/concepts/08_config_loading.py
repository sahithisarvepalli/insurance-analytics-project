#!/usr/bin/env python3
"""
Concept: Configuration Loading
Description: Load config from YAML and expand environment variables.
"""

import os

import yaml


def load_config(path="config.yaml"):
    if not os.path.exists(path):
        # Create sample config
        sample = {
            "database": {"host": "${DB_HOST}", "port": 5432, "user": "postgres"},
            "app_name": "MyApp",
        }
        with open(path, "w") as f:
            yaml.dump(sample, f)
        print(f"Created sample {path}")

    with open(path) as f:
        raw = yaml.safe_load(f) or {}

    def expand(value):
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            return os.getenv(env_var, value)  # Fallback to original if not set
        return value

    # Recursively expand
    def expand_dict(d):
        if isinstance(d, dict):
            return {k: expand_dict(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [expand_dict(item) for item in d]
        else:
            return expand(d)

    return expand_dict(raw)


def main():
    config = load_config()
    print("Loaded config:")
    print(config)


if __name__ == "__main__":
    main()
