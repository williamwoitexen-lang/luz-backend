#!/usr/bin/env python3
"""
Script para executar scripts SQL no SQL Server.
Uso: python db/run_schema.py [schema_sqlserver|schema_dimensions]
"""

import sys
import os
import logging
from pathlib import Path

# Adicionar parent directory ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.sqlserver import SQLServerConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_sql_file(filename: str) -> str:
    """Ler arquivo SQL"""
    db_dir = Path(__file__).parent
    filepath = db_dir / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"SQL file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def split_sql_statements(sql_content: str) -> list[str]:
    """
    Dividir conteúdo SQL em statements individuais.
    Trata GO como separador de batch.
    """
    # Primeiro, dividir por GO (case-insensitive)
    batches = []
    current = []
    
    for line in sql_content.split('\n'):
        # Verificar se a linha é só GO (ignorando comentários)
        clean_line = line.strip()
        
        # Remover comentários SQL
        if '--' in clean_line:
            clean_line = clean_line[:clean_line.index('--')].strip()
        
        if clean_line.upper() == 'GO':
            # Finalizar batch
            if current:
                batch_text = '\n'.join(current).strip()
                if batch_text:
                    batches.append(batch_text)
                current = []
        else:
            current.append(line)
    
    # Adicionar último batch
    if current:
        batch_text = '\n'.join(current).strip()
        if batch_text:
            batches.append(batch_text)
    
    return batches


def execute_sql_file(filename: str, verbose: bool = False):
    """Executar arquivo SQL no SQL Server"""
    try:
        sql_content = read_sql_file(filename)
        
        logger.info(f"Connecting to SQL Server...")
        conn = SQLServerConnection()
        
        if not conn.conn:
            raise RuntimeError("Failed to connect to SQL Server")
        
        # Dividir em statements
        statements = split_sql_statements(sql_content)
        logger.info(f"Found {len(statements)} SQL batches to execute")
        
        for i, statement in enumerate(statements, 1):
            if verbose:
                preview = statement.replace('\n', ' ')[:100]
                logger.info(f"[{i}/{len(statements)}] Executing: {preview}...")
            
            try:
                conn.execute(statement)
                logger.info(f"[{i}/{len(statements)}] OK")
            except Exception as e:
                logger.warning(f"[{i}/{len(statements)}] Error: {e}")
                preview = statement.replace('\n', ' ')[:200]
                logger.warning(f"Failed statement: {preview}...")
                # Continuar com próximas statements
                continue
        
        logger.info(f"Completed execution of {filename}")
        conn.close()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python db/run_schema.py [schema_sqlserver|schema_dimensions] [--verbose]")
        sys.exit(1)
    
    filename = sys.argv[1]
    verbose = '--verbose' in sys.argv
    
    # Adicionar .sql se não tiver
    if not filename.endswith('.sql'):
        filename = f"{filename}.sql"
    
    logger.info(f"Executing {filename}...")
    execute_sql_file(filename, verbose=verbose)
