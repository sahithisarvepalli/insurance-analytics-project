#!/usr/bin/env python3
"""
Concept: Logging
Description: Use Python's logging module for info and debug messages.
"""

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def process_data(data):
    logger.info(f"Processing {len(data)} items")
    # Simulate processing
    result = [x * 2 for x in data]
    logger.debug(f"Result: {result}")
    return result

def main():
    logger.info("Starting application")
    data = [1, 2, 3, 4, 5]
    result = process_data(data)
    logger.info(f"Final result: {result}")

if __name__ == "__main__":
    main()