# Test file removed - tests require SQL Server and Azure dependencies
# Local DuckDB testing is no longer supported
# Use integration tests against Azure infrastructure

import pytest

@pytest.mark.skip(reason="DuckDB tests removed - use Azure integration tests instead")
def test_placeholder():
    pass

