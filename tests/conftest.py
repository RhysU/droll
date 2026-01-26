# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""Pytest configuration for mutation testing compatibility."""
import sys
import pytest

# Skip tests that are incompatible with mutmut's code instrumentation
# (mutmut's transformation loses docstrings which test_help relies on)
def pytest_collection_modifyitems(config, items):
    # Check if mutmut instrumented code is in sys.path
    is_mutmut = any("mutants" in p for p in sys.path)
    if is_mutmut:
        skip_mutmut = pytest.mark.skip(
            reason="Test incompatible with mutmut instrumentation"
        )
        for item in items:
            if item.name == "test_help":
                item.add_marker(skip_mutmut)
