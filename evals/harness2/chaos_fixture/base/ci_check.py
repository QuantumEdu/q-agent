#!/usr/bin/env python3
import sys
import unittest

suite = unittest.defaultTestLoader.discover("tests", pattern="test_*.py")
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
