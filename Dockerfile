# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies needed for building (minimizados)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        ca-certificates \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Install ODBC driver 18 for SQL Server
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Copy e install Python dependencies (layer separado para cache)
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime (imagem final menor)
FROM python:3.11-slim

WORKDIR /app

# Install ODBC runtime + dependencies for pyodbc
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        odbcinst \
        libodbc2 \
    && rm -rf /var/lib/apt/lists/*

# Copy ODBC libs do builder
COPY --from=builder /opt/microsoft /opt/microsoft
COPY --from=builder /usr/share/keyrings /usr/share/keyrings
COPY --from=builder /etc/odbc* /etc/

# Copy Python packages do builder (includes compiled pyodbc wheels)
COPY --from=builder /root/.local /root/.local

# Set PATH para usar pip packages + ODBC
ENV PATH=/root/.local/bin:$PATH \
    LD_LIBRARY_PATH=/opt/microsoft/msodbcsql18/lib64:$LD_LIBRARY_PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy application code
COPY . .

# Create directories for local storage
RUN mkdir -p storage/documents storage/temp

# Expose port
EXPOSE 8000

# Run with optimizações de memória
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--loop", "uvloop"]
