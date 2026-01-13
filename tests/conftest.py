import sys
import os
import pytest

# Add the root directory to sys.path so we can import dance_loop_gen
# This assumes the test runner is executed from the repo root
sys.path.append(os.getcwd())

def pytest_sessionstart(session):
    """
    Called before the test session starts.
    Creates a symlink 'dance_loop_gen' pointing to current directory
    to allow imports like 'dance_loop_gen.utils'.
    """
    if not os.path.exists("dance_loop_gen"):
        try:
            os.symlink(".", "dance_loop_gen")
        except OSError:
            pass

def pytest_sessionfinish(session, exitstatus):
    """
    Called after the test session ends.
    Removes the 'dance_loop_gen' symlink.
    """
    if os.path.exists("dance_loop_gen") and os.path.islink("dance_loop_gen"):
        os.remove("dance_loop_gen")
