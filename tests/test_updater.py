import pytest
from systemmonitor.utils.updater import is_newer_version

def test_is_newer_version_basic():
    # Newer remote versions
    assert is_newer_version("2.0.0", "2.0.1") is True
    assert is_newer_version("2.0.0", "v2.1.0") is True
    assert is_newer_version("v2.0.0", "2.0.10") is True
    assert is_newer_version("2.0.0", "3.0.0") is True
    
    # Older remote versions
    assert is_newer_version("2.0.0", "1.9.9") is False
    assert is_newer_version("2.0.0", "2.0.0") is False
    assert is_newer_version("2.0.0", "v2.0") is False
    
    # Padding and format variations
    assert is_newer_version("2.0", "2.0.1") is True
    assert is_newer_version("2.0.0.0", "2.0.1") is True
    assert is_newer_version("2.1", "2.0.9") is False
    
    # Invalid strings should return False gracefully
    assert is_newer_version("2.0.0", "invalid-version") is False
    assert is_newer_version("invalid", "2.0.0") is False
