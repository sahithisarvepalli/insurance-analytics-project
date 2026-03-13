#!/usr/bin/env python3
"""
Concept: Command-Line Argument Parsing
Description: Use argparse to handle command-line arguments for a simple script.
Example: Run with --name "Alice" --age 30
"""

import argparse

def main(name, age):
    print(f"Hello, {name}! You are {age} years old.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Greet a person with name and age.")
    parser.add_argument("--name", type=str, required=True, help="The person's name")
    parser.add_argument("--age", type=int, required=True, help="The person's age")
    args = parser.parse_args()
    main(args.name, args.age)