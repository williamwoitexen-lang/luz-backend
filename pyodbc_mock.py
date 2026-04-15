"""
Simple mock for pyodbc for development/testing purposes.
"""

class MockConnection:
    """Mock database connection."""
    def __init__(self, *args, **kwargs):
        pass
    
    def cursor(self):
        return MockCursor()
    
    def close(self):
        pass
    
    def commit(self):
        pass
    
    def rollback(self):
        pass
    
    def setdecoding(self, ctype, encoding=None):
        """Mock setdecoding method (no-op)."""
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


class MockCursor:
    """Mock database cursor."""
    def __init__(self):
        self.rowcount = 0
        self.description = None
    
    def execute(self, query, *args, **kwargs):
        self.rowcount = 0
        return self
    
    def executemany(self, query, seq):
        return self
    
    def fetchone(self):
        return None
    
    def fetchall(self):
        return []
    
    def fetchmany(self, size):
        return []
    
    def close(self):
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
    
    def __iter__(self):
        return iter([])


def connect(*args, **kwargs):
    """Create a mock connection."""
    return MockConnection(*args, **kwargs)


# pyodbc constants (for compatibility)
SQL_CHAR = -1
SQL_VARCHAR = 12
SQL_WCHAR = -8
SQL_WVARCHAR = -9

# Export for compatibility
__all__ = ['connect', 'MockConnection', 'MockCursor', 'SQL_CHAR', 'SQL_VARCHAR', 'SQL_WCHAR', 'SQL_WVARCHAR']
