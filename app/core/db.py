# DuckDB support removed - using SQL Server only
# This file is kept for backward compatibility but should not be used

raise RuntimeError(
    "DuckDB is no longer supported. This application requires Azure SQL Server. "
    "Configure SQL_SERVER_CONNECTION_STRING environment variable."
)
