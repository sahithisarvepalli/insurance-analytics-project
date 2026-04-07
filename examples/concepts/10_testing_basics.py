#!/usr/bin/env python3
"""
Concept: Testing Basics
Description: Use pytest to write and run simple tests.
Run with: pytest 10_testing_basics.py
"""


def add_numbers(a, b):
    return a + b


def test_add_positive():
    assert add_numbers(2, 3) == 5


def test_add_negative():
    assert add_numbers(-1, 1) == 0


def test_add_zero():
    assert add_numbers(0, 0) == 0


if __name__ == "__main__":
    # Run tests manually if not using pytest
    test_add_positive()
    test_add_negative()
    test_add_zero()
    print("All tests passed!")
