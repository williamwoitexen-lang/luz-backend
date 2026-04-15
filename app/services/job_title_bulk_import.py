"""
Serviço para importação em massa de job_title → role mappings
Suporta CSV, XLSX, e operações em lote
"""
import logging
import csv
import io
from typing import List, Dict, Tuple, Optional
from app.core.sqlserver import get_sqlserver_connection

logger = logging.getLogger(__name__)


class JobTitleBulkImport:
    """Importação em massa de mapeamentos de job_title → role"""
    
    @staticmethod
    def validate_csv_content(content: str, delimiter: str = ",") -> Tuple[bool, List[str], List[Dict]]:
        """
        Validar arquivo CSV.
        
        Esperado:
        - Primeira linha: headers (job_title, role)
        - Demais linhas: dados
        
        Returns:
            (is_valid, errors, rows)
        """
        errors = []
        rows = []
        
        try:
            reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
            
            if not reader.fieldnames or 'job_title' not in reader.fieldnames or 'role' not in reader.fieldnames:
                errors.append("CSV deve ter colunas: 'job_title' e 'role'")
                return False, errors, []
            
            for idx, row in enumerate(reader, start=2):  # Começa em 2 (linha 1 é header)
                job_title = row.get('job_title', '').strip()
                role = row.get('role', '').strip()
                
                if not job_title:
                    errors.append(f"Linha {idx}: job_title vazio")
                    continue
                
                if not role:
                    errors.append(f"Linha {idx}: role vazio")
                    continue
                
                rows.append({
                    'job_title': job_title,
                    'role': role
                })
            
            if not rows:
                errors.append("Nenhuma linha válida encontrada no CSV")
                return False, errors, []
            
            logger.info(f"CSV validado com sucesso: {len(rows)} linhas válidas")
            return True, errors, rows
            
        except Exception as e:
            errors.append(f"Erro ao processar CSV: {str(e)}")
            logger.error(f"CSV validation error: {e}")
            return False, errors, []
    
    @staticmethod
    def import_from_excel(file_path: str, sheet_name: str = 0) -> Tuple[int, List[str]]:
        """
        Importar de arquivo XLSX.
        
        Args:
            file_path: Caminho do arquivo XLSX
            sheet_name: Nome ou índice da aba
        
        Returns:
            (success_count, errors)
        """
        errors = []
        
        try:
            import openpyxl
            
            wb = openpyxl.load_workbook(file_path)
            ws = wb[sheet_name] if isinstance(sheet_name, str) else wb.worksheets[sheet_name]
            
            rows = []
            header_row = None
            
            for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
                if idx == 1:
                    header_row = row
                    # Validar headers
                    if 'job_title' not in [str(h).lower() for h in header_row]:
                        errors.append("XLSX deve ter coluna 'job_title'")
                        return 0, errors
                    if 'role' not in [str(h).lower() for h in header_row]:
                        errors.append("XLSX deve ter coluna 'role'")
                        return 0, errors
                    continue
                
                job_title = str(row[0]).strip() if row[0] else ""
                role = str(row[1]).strip() if row[1] else ""
                
                if job_title and role:
                    rows.append({'job_title': job_title, 'role': role})
            
            if not rows:
                errors.append("Nenhuma linha válida encontrada na aba")
                return 0, errors
            
            # Importar em lote
            success_count = JobTitleBulkImport.bulk_insert(rows)
            
            logger.info(f"XLSX importado com sucesso: {success_count}/{len(rows)} linhas")
            return success_count, errors
            
        except ImportError:
            errors.append("Biblioteca openpyxl não instalada. Use: pip install openpyxl")
            logger.error("openpyxl not installed")
            return 0, errors
        except Exception as e:
            errors.append(f"Erro ao processar XLSX: {str(e)}")
            logger.error(f"XLSX import error: {e}")
            return 0, errors
    
    @staticmethod
    def bulk_insert(rows: List[Dict], batch_size: int = 1000) -> int:
        """
        Inserir múltiplas linhas em lote.
        
        Usa transações para melhor performance.
        Ignora duplicatas (UNIQUE constraint on job_title).
        
        Args:
            rows: Lista de dicts com 'job_title' e 'role'
            batch_size: Tamanho do lote para cada INSERT
        
        Returns:
            Número total de linhas inseridas com sucesso
        """
        if not rows:
            return 0
        
        total_inserted = 0
        errors_count = 0
        
        try:
            sql = get_sqlserver_connection()
            
            # Processar em lotes para não sobrecarregar memória
            for batch_start in range(0, len(rows), batch_size):
                batch_end = min(batch_start + batch_size, len(rows))
                batch = rows[batch_start:batch_end]
                
                try:
                    # SQL Server: INSERT com ON CONFLICT via merge ou try-catch
                    # Vamos usar TRY-CATCH para ignorar duplicatas
                    
                    # Preparar valores para inserção
                    insert_query = """
                    INSERT INTO dim_job_title_roles (job_title, role, is_active)
                    VALUES (?, ?, 1)
                    """
                    
                    for row in batch:
                        try:
                            sql.execute(insert_query, [row['job_title'], row['role']])
                            total_inserted += 1
                        except Exception as row_error:
                            # Ignorar duplicatas (UNIQUE constraint)
                            if "UNIQUE" in str(row_error) or "duplicate" in str(row_error).lower():
                                logger.debug(f"Job title já existe: {row['job_title']}")
                            else:
                                logger.error(f"Erro ao inserir {row['job_title']}: {row_error}")
                                errors_count += 1
                    
                    logger.info(f"Lote {batch_start//batch_size + 1}: {total_inserted} inseridas até agora")
                    
                except Exception as batch_error:
                    logger.error(f"Erro em lote: {batch_error}")
                    errors_count += 1
            
            logger.info(f"Bulk insert concluído: {total_inserted} inseridas, {errors_count} erros")
            return total_inserted
            
        except Exception as e:
            logger.error(f"Erro em bulk_insert: {e}")
            return total_inserted
    
    @staticmethod
    def import_csv_string(csv_content: str, delimiter: str = ",") -> Tuple[int, List[str]]:
        """
        Importar de string CSV.
        
        Args:
            csv_content: Conteúdo do CSV como string
            delimiter: Delimitador (padrão: ",")
        
        Returns:
            (success_count, errors)
        """
        is_valid, errors, rows = JobTitleBulkImport.validate_csv_content(csv_content, delimiter)
        
        if not is_valid or not rows:
            return 0, errors
        
        # Fazer bulk insert
        success_count = JobTitleBulkImport.bulk_insert(rows)
        
        if success_count < len(rows):
            errors.append(f"Aviso: {len(rows) - success_count} linhas não foram inseridas (pode ser duplicatas)")
        
        return success_count, errors
    
    @staticmethod
    def get_import_stats() -> Dict:
        """Obter estatísticas da tabela"""
        try:
            sql = get_sqlserver_connection()
            
            query = """
            SELECT 
                COUNT(*) as total_mappings,
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_mappings,
                SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as inactive_mappings,
                COUNT(DISTINCT role) as unique_roles,
                MIN(created_at) as first_import,
                MAX(updated_at) as last_update
            FROM dim_job_title_roles
            """
            
            result = sql.execute(query)
            if result:
                row = result[0]
                return {
                    "total_mappings": row.get('total_mappings', 0),
                    "active_mappings": row.get('active_mappings', 0),
                    "inactive_mappings": row.get('inactive_mappings', 0),
                    "unique_roles": row.get('unique_roles', 0),
                    "first_import": row.get('first_import'),
                    "last_update": row.get('last_update')
                }
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
        
        return {
            "total_mappings": 0,
            "active_mappings": 0,
            "inactive_mappings": 0,
            "unique_roles": 0
        }
