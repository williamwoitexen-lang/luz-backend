"""
Service para gerenciar admins e seus grupos de acesso.
"""
import logging
from typing import List, Dict, Optional, Any
from uuid import uuid4
from datetime import datetime
from app.core.sqlserver import get_sqlserver_connection
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)


class AdminService:
    """CRUD operations para admins."""
    
    @staticmethod
    def create_admin(email: str, agent_id: int = 1, feature_ids: Optional[List[int]] = None, 
                    name: Optional[str] = None, job_title: Optional[str] = None, 
                    city: Optional[str] = None, created_by: Optional[str] = None) -> Dict[str, Any]:
        """
        Criar novo admin.
        
        Args:
            email: Email do admin
            agent_id: ID do agente (1=LUZ, 2=IGP, 3=SMART)
            feature_ids: Lista de IDs de features permitidas. Se None, adiciona TODAS do agente
            name: Nome completo do colaborador
            job_title: Cargo do colaborador
            city: Cidade para desambiguar colaboradores
            created_by: Nome do usuário que criou o admin
        
        Returns:
            Dict com dados do admin criado
            
        Raises:
            ValueError: Se agent_id não é válido
        """
        try:
            # Validar agent_id
            if not AgentService.is_agent_valid_by_id(agent_id):
                raise ValueError(f"Agent ID inválido: {agent_id}. IDs válidos: 1 (LUZ), 2 (IGP), 3 (SMART)")
            
            # Obter agente para saber o nome
            agent = AgentService.get_agent_by_id(agent_id)
            agent_name = agent.get("name") if agent else f"ID:{agent_id}"
            
            sql = get_sqlserver_connection()
            
            # Verificar se admin já existe com mesma combinação (email, agent_id)
            existing_admin = AdminService.get_admin_by_email_and_agent(email, agent_id)
            if existing_admin:
                if existing_admin.get("is_active"):
                    error_msg = f"Admin com email '{email}' já existe no agente '{agent_name}' e está ATIVO"
                    logger.warning(f"[CREATE_ADMIN] ⚠️ {error_msg}")
                    raise ValueError(error_msg)
                else:
                    error_msg = f"Admin com email '{email}' já existe no agente '{agent_name}' mas foi DELETADO. Use PUT para reativá-lo ou use DELETE para removê-lo permanentemente"
                    logger.warning(f"[CREATE_ADMIN] ⚠️ {error_msg}")
                    raise ValueError(error_msg)
            
            admin_id = str(uuid4())
            now = datetime.utcnow()
            
            # Se não foi passado feature_ids, adiciona TODAS as features do agente
            if feature_ids is None or len(feature_ids) == 0:
                logger.info(f"[CREATE_ADMIN] 📋 feature_ids não fornecido, adicionando TODAS as features para agente '{agent_name}'...")
                agent_features = AdminService.list_features(active_only=True, agente=agent_name)
                feature_ids = [f.get("feature_id") for f in agent_features]
                logger.info(f"[CREATE_ADMIN] ✅ {len(feature_ids)} features encontradas para agente '{agent_name}': {feature_ids}")
            else:
                # Se passou feature_ids, valida se existem e estão ativas (mas não restringe ao agente)
                logger.info(f"[CREATE_ADMIN] 🔍 Validando {len(feature_ids)} features...")
                all_features = AdminService.list_features(active_only=True)
                valid_feature_ids = [f.get("feature_id") for f in all_features]
                
                invalid_features = [fid for fid in feature_ids if fid not in valid_feature_ids]
                if invalid_features:
                    error_msg = f"Features {invalid_features} não existem no sistema ou estão inativas. Features válidas: {valid_feature_ids}"
                    logger.warning(f"[CREATE_ADMIN] ⚠️ {error_msg}")
                    raise ValueError(error_msg)
                
                logger.info(f"[CREATE_ADMIN] ✅ Todas as {len(feature_ids)} features existem e estão ativas")
            
            query = """
            INSERT INTO admins (admin_id, email, name, job_title, city, agent_id, is_active, created_at, updated_at, created_by, updated_by)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
            """
            
            sql.execute(query, (admin_id, email, name, job_title, city, agent_id, now, now, created_by, created_by))
            
            # Inserir features
            for fid in feature_ids:
                sql.execute(
                    "INSERT INTO admin_features (admin_id, feature_id, created_at) VALUES (?, ?, ?)",
                    (admin_id, fid, now)
                )

            logger.info(f"[CREATE_ADMIN] ✅ Admin criado: {email} ({name or 'sem nome'}) - {city or 'sem cidade'} (agent={agent_name}, {len(feature_ids)} features) por {created_by}")
            
            # Registrar auditoria
            try:
                from app.services.admin_audit_service import AdminAuditService
                admin_data = {
                    "email": email,
                    "name": name,
                    "job_title": job_title,
                    "city": city,
                    "agent_id": agent_id,
                    "feature_ids": feature_ids,
                    "is_active": True
                }
                AdminAuditService.log_create(admin_id, admin_data, created_by)
            except Exception as audit_error:
                logger.warning(f"[CREATE_ADMIN] ⚠️ Erro ao registrar auditoria: {audit_error}")
            
            return {
                "admin_id": admin_id,
                "email": email,
                "name": name,
                "job_title": job_title,
                "city": city,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "feature_ids": feature_ids,
                "is_active": True,
                "created_at": now,
                "created_by": created_by,
                "updated_at": now,
                "updated_by": created_by
            }
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"[CREATE_ADMIN] ❌ Erro ao criar admin: {e}", exc_info=True)
            raise
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar admin: {e}")
            raise
    
    
    @staticmethod
    def get_admin_by_id(admin_id: str) -> Optional[Dict[str, Any]]:
        """Obter admin por ID com detalhes completos de suas features e agente."""
        try:
            sql = get_sqlserver_connection()
            
            logger.debug(f"[GET_ADMIN_BY_ID] 🔍 Buscando admin com ID: {admin_id} (tipo: {type(admin_id)})")
            
            query = """
            SELECT 
                a.admin_id, a.email, a.name, a.job_title, a.city, a.agent_id, a.is_active, a.created_at, a.updated_at, a.created_by, a.updated_by,
                aa.agent_id as aa_agent_id, aa.code, aa.name as agent_name, aa.description, aa.is_active as agent_active
            FROM admins a
            LEFT JOIN allowed_agents aa ON a.agent_id = aa.agent_id
            WHERE a.admin_id = ?
            """
            
            result = sql.execute_single(query, (admin_id,))
            
            logger.debug(f"[GET_ADMIN_BY_ID] 📊 Query result: {result is not None}")
            
            if not result:
                logger.warning(f"[GET_ADMIN_BY_ID] ⚠️ Nenhum admin encontrado para ID: {admin_id}")
                return None
            
            logger.debug(f"[GET_ADMIN_BY_ID] ✅ Admin encontrado: {result.get('email', 'sem email')}")
            
            # Buscar features com detalhes completos
            feature_query = """
            SELECT 
                f.feature_id,
                f.agente,
                f.code,
                f.name,
                f.description,
                f.is_active,
                f.created_at
            FROM admin_features af
            JOIN features f ON af.feature_id = f.feature_id
            WHERE af.admin_id = ?
            """
            feature_rows = sql.execute(feature_query, (admin_id,))
            features = [dict(r) for r in feature_rows]
            
            logger.debug(f"[GET_ADMIN_BY_ID] 📊 Features encontradas: {len(features)}")
            
            admin_dict = AdminService._parse_admin_row(result)
            admin_dict["features"] = features
            return admin_dict
            
        except Exception as e:
            logger.error(f"[GET_ADMIN_BY_ID] ❌ Erro ao buscar admin: {e}", exc_info=True)
            raise
    
    
    @staticmethod
    def get_admin_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Obter admin por email com detalhes completos de suas features e agente."""
        try:
            sql = get_sqlserver_connection()
            
            # Limpar email (remover espaços)
            email_clean = email.strip() if email else ""
            logger.info(f"[GET_ADMIN_BY_EMAIL] 🔍 Procurando admin com email: '{email_clean}'")
            
            query = """
            SELECT 
                a.admin_id, a.email, a.name, a.job_title, a.city, a.agent_id, a.is_active, a.created_at, a.updated_at, a.created_by, a.updated_by,
                aa.agent_id as aa_agent_id, aa.code, aa.name as agent_name, aa.description, aa.is_active as agent_active
            FROM admins a
            LEFT JOIN allowed_agents aa ON a.agent_id = aa.agent_id
            WHERE LOWER(TRIM(a.email)) = LOWER(TRIM(?))
            """
            
            result = sql.execute_single(query, (email_clean,))
            
            if not result:
                logger.warning(f"[GET_ADMIN_BY_EMAIL] ⚠️ Admin não encontrado com email: {email_clean}")
                # Debug: Listar todos os emails para debugging
                debug_query = "SELECT TOP 5 email FROM admins ORDER BY created_at DESC"
                debug_results = sql.execute(debug_query, ())
                debug_emails = [str(r.get("email")) for r in debug_results]
                logger.debug(f"[GET_ADMIN_BY_EMAIL] 🔍 Últimos 5 emails no banco: {debug_emails}")
                return None
            
            logger.info(f"[GET_ADMIN_BY_EMAIL] ✅ Admin encontrado: {result.get('admin_id')} - {result.get('email')}")
            
            # Buscar features com detalhes completos
            feature_query = """
            SELECT 
                f.feature_id,
                f.agente,
                f.code,
                f.name,
                f.description,
                f.is_active,
                f.created_at
            FROM admin_features af
            JOIN features f ON af.feature_id = f.feature_id
            WHERE af.admin_id = ?
            """
            feature_rows = sql.execute(feature_query, (result["admin_id"],))
            features = [dict(r) for r in feature_rows]
            
            logger.info(f"[GET_ADMIN_BY_EMAIL] 📋 {len(features)} features encontradas")
            
            admin_dict = AdminService._parse_admin_row(result)
            admin_dict["features"] = features
            return admin_dict
            
        except Exception as e:
            logger.error(f"[GET_ADMIN_BY_EMAIL] ❌ Erro ao buscar admin por email ({email}): {e}", exc_info=True)
            raise
    
    
    @staticmethod
    def get_admin_by_email_and_agent(email: str, agent_id: int) -> Optional[Dict[str, Any]]:
        """
        Obter admin por email E agent_id (combinação única).
        
        Permite o mesmo email em agentes diferentes, mas rejeita duplicatas 
        do mesmo email no mesmo agente.
        
        Args:
            email: Email do admin
            agent_id: ID do agente (1=LUZ, 2=IGP, 3=SMART)
        
        Returns:
            Dict com dados do admin, ou None se não encontrado
        """
        try:
            sql = get_sqlserver_connection()
            query = """
            SELECT 
                a.admin_id, a.email, a.name, a.job_title, a.city, a.agent_id, a.is_active, a.created_at, a.updated_at, a.created_by, a.updated_by,
                aa.agent_id as aa_agent_id, aa.code, aa.name as agent_name, aa.description, aa.is_active as agent_active
            FROM admins a
            LEFT JOIN allowed_agents aa ON a.agent_id = aa.agent_id
            WHERE a.email = ? AND a.agent_id = ?
            """
            
            result = sql.execute_single(query, (email, agent_id))
            
            if not result:
                logger.debug(f"Admin não encontrado: email={email}, agent_id={agent_id}")
                return None
            
            # Buscar features com detalhes completos
            feature_query = """
            SELECT 
                f.feature_id,
                f.agente,
                f.code,
                f.name,
                f.description,
                f.is_active,
                f.created_at
            FROM admin_features af
            JOIN features f ON af.feature_id = f.feature_id
            WHERE af.admin_id = ?
            """
            feature_rows = sql.execute(feature_query, (result["admin_id"],))
            features = [dict(r) for r in feature_rows]
            
            admin_dict = AdminService._parse_admin_row(result)
            admin_dict["features"] = features
            return admin_dict
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar admin por (email, agent_id): {e}")
            raise
    
    
    @staticmethod
    def get_admin_by_email_and_agent_active(email: str, agent_id: int) -> Optional[Dict[str, Any]]:
        """
        Obter admin por email E agent_id, apenas se ATIVO.
        
        Permite recriação de combinação (email, agent_id) se o admin anterior foi deletado.
        
        Args:
            email: Email do admin
            agent_id: ID do agente (1=LUZ, 2=IGP, 3=SMART)
        
        Returns:
            Dict com dados do admin, ou None se não encontrado OU se inativo
        """
        try:
            sql = get_sqlserver_connection()
            query = """
            SELECT 
                a.admin_id, a.email, a.name, a.job_title, a.city, a.agent_id, a.is_active, a.created_at, a.updated_at, a.created_by, a.updated_by,
                aa.agent_id as aa_agent_id, aa.code, aa.name as agent_name, aa.description, aa.is_active as agent_active
            FROM admins a
            LEFT JOIN allowed_agents aa ON a.agent_id = aa.agent_id
            WHERE a.email = ? AND a.agent_id = ? AND a.is_active = 1
            """
            
            result = sql.execute_single(query, (email, agent_id))
            
            if not result:
                logger.debug(f"Admin ATIVO não encontrado: email={email}, agent_id={agent_id}")
                return None
            
            # Buscar features com detalhes completos
            feature_query = """
            SELECT 
                f.feature_id,
                f.agente,
                f.code,
                f.name,
                f.description,
                f.is_active,
                f.created_at
            FROM admin_features af
            JOIN features f ON af.feature_id = f.feature_id
            WHERE af.admin_id = ?
            """
            feature_rows = sql.execute(feature_query, (result["admin_id"],))
            features = [dict(r) for r in feature_rows]
            
            admin_dict = AdminService._parse_admin_row(result)
            admin_dict["features"] = features
            return admin_dict
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar admin ATIVO por (email, agent_id): {e}")
            raise
    
    
        """
        Listar admins com paginação.
        
        Args:
            active_only: Se True, retorna apenas admins ativos
            limit: Quantidade de resultados
            offset: Offset para paginação
        
        Returns:
            Dict com 'admins' (list) e 'total' (int)
        """
        try:
            sql = get_sqlserver_connection()
            
            # Query com WHERE condicional
            where_clause = "WHERE a.is_active = 1" if active_only else ""
            
            query_count = f"SELECT COUNT(*) as total FROM admins a {where_clause}"
            count_result = sql.execute_single(query_count)
            total = count_result["total"] if count_result else 0
            
            query_list = f"""
            SELECT 
                a.admin_id, a.email, a.name, a.job_title, a.city, a.agent_id, a.is_active, a.created_at, a.updated_at, a.created_by, a.updated_by,
                aa.agent_id as aa_agent_id, aa.code, aa.name as agent_name, aa.description, aa.is_active as agent_active
            FROM admins a
            LEFT JOIN allowed_agents aa ON a.agent_id = aa.agent_id
            {where_clause}
            ORDER BY a.created_at DESC
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
            """
            
            results = sql.execute(query_list, (offset, limit))
            admins = []
            for r in results:
                admin_dict = AdminService._parse_admin_row(r)
                
                # Buscar features com detalhes
                feature_query = """
                SELECT 
                    f.feature_id,
                    f.agente,
                    f.code,
                    f.name,
                    f.description,
                    f.is_active,
                    f.created_at
                FROM admin_features af
                JOIN features f ON af.feature_id = f.feature_id
                WHERE af.admin_id = ?
                """
                feature_rows = sql.execute(feature_query, (r["admin_id"],))
                admin_dict["features"] = [dict(f) for f in feature_rows]
                admins.append(admin_dict)
            
            logger.info(f"📋 Listados {len(admins)} admins (total: {total})")
            
            return {
                "admins": admins,
                "total": total
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar admins: {e}")
            raise
    
    
    @staticmethod
    def list_admins(active_only: bool = True, email: Optional[str] = None, name: Optional[str] = None, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Listar TODOS os admins (de todos os agentes).
        
        Args:
            active_only: Se True, retorna apenas admins ativos. Se False, retorna inativos. Se None, retorna ambos
            email: (Opcional) Filtrar por email específico (busca por substring case-insensitive)
            name: (Opcional) Filtrar por nome (busca por substring case-insensitive)
            limit: Quantidade de resultados
            offset: Offset para paginação
        
        Returns:
            Dict com 'admins' (list) e 'total' (int)
        """
        try:
            sql = get_sqlserver_connection()
            
            where_clause = "WHERE 1=1"
            params = []
            
            # Filtro de ativo/inativo
            if active_only is True:
                where_clause += " AND a.is_active = 1"
            elif active_only is False:
                where_clause += " AND a.is_active = 0"
            # Se None, retorna ambos (não adiciona filtro)
            
            # Filtro de email
            if email:
                where_clause += " AND LOWER(TRIM(a.email)) LIKE LOWER(TRIM(?))"
                params.append(f"%{email}%")
                logger.info(f"[LIST_ADMINS] 🔍 Filtrando por email: {email}")
            
            # Filtro de nome
            if name:
                where_clause += " AND LOWER(TRIM(a.name)) LIKE LOWER(TRIM(?))"
                params.append(f"%{name}%")
                logger.info(f"[LIST_ADMINS] 🔍 Filtrando por nome: {name}")
            
            query_count = f"SELECT COUNT(*) as total FROM admins a {where_clause}"
            count_result = sql.execute_single(query_count, params)
            total = count_result["total"] if count_result else 0
            
            query_list = f"""
            SELECT 
                a.admin_id, a.email, a.name, a.job_title, a.city, a.agent_id, a.is_active, a.created_at, a.updated_at, a.created_by, a.updated_by,
                aa.agent_id as aa_agent_id, aa.code, aa.name as agent_name, aa.description, aa.is_active as agent_active
            FROM admins a
            LEFT JOIN allowed_agents aa ON a.agent_id = aa.agent_id
            {where_clause}
            ORDER BY a.created_at DESC
            OFFSET {offset} ROWS
            FETCH NEXT {limit} ROWS ONLY
            """
            
            results = sql.execute(query_list, params)
            admins = []
            for r in results:
                admin_dict = AdminService._parse_admin_row(r)
                
                # Buscar features com detalhes
                feature_query = """
                SELECT 
                    f.feature_id,
                    f.agente,
                    f.code,
                    f.name,
                    f.description,
                    f.is_active,
                    f.created_at
                FROM admin_features af
                JOIN features f ON af.feature_id = f.feature_id
                WHERE af.admin_id = ?
                """
                feature_rows = sql.execute(feature_query, (r["admin_id"],))
                admin_dict["features"] = [dict(f) for f in feature_rows]
                admins.append(admin_dict)
            
            status_msg = "ativos" if active_only is True else ("inativos" if active_only is False else "ambos")
            logger.info(f"[LIST_ADMINS] 📋 Listados {len(admins)} admins {status_msg} (total: {total})")
            
            return {
                "admins": admins,
                "total": total
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar admins: {e}")
            raise
    
    @staticmethod
    def search_admin_by_email_all_agents(email: str) -> Optional[List[Dict[str, Any]]]:
        """
        Buscar usuário por email em TODOS os agentes.
        Útil para verificar se uma pessoa já é admin em algum lugar.
        
        Args:
            email: Email a buscar (case-insensitive)
        
        Returns:
            Lista de dicts com todas as ocorrências (pode ser multiple agentes)
            ou None se não encontrado em nenhum agente
        """
        try:
            sql = get_sqlserver_connection()
            
            query = """
            SELECT 
                a.admin_id, a.email, a.name, a.job_title, a.city, a.agent_id, a.is_active, a.created_at, a.updated_at, a.created_by, a.updated_by,
                aa.agent_id as aa_agent_id, aa.code, aa.name as agent_name, aa.description, aa.is_active as agent_active
            FROM admins a
            LEFT JOIN allowed_agents aa ON a.agent_id = aa.agent_id
            WHERE LOWER(TRIM(a.email)) = LOWER(TRIM(?))
            ORDER BY a.created_at DESC
            """
            
            results = sql.execute(query, (email,))
            
            if not results:
                logger.debug(f"[SEARCH_ADMIN] Admin não encontrado em nenhum agente: {email}")
                return None
            
            admins = []
            for r in results:
                admin_dict = AdminService._parse_admin_row(r)
                
                # Buscar features com detalhes
                feature_query = """
                SELECT 
                    f.feature_id,
                    f.agente,
                    f.code,
                    f.name,
                    f.description,
                    f.is_active,
                    f.created_at
                FROM admin_features af
                JOIN features f ON af.feature_id = f.feature_id
                WHERE af.admin_id = ?
                """
                feature_rows = sql.execute(feature_query, (r["admin_id"],))
                admin_dict["features"] = [dict(f) for f in feature_rows]
                admins.append(admin_dict)
            
            logger.info(f"[SEARCH_ADMIN] 🔍 Encontrado(s) {len(admins)} registro(s) para email: {email}")
            return admins
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar admin por email: {e}")
            raise
    
    @staticmethod
    def list_admins_by_agent_id(agent_id: int, active_only: bool = True, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Listar admins de um agent_id específico.
        
        Args:
            agent_id: ID do agente (1=LUZ, 2=IGP, 3=SMART)
            active_only: Se True, retorna apenas admins ativos
            limit: Quantidade de resultados
            offset: Offset para paginação
        
        Returns:
            Dict com 'admins' (list) e 'total' (int)
        """
        try:
            sql = get_sqlserver_connection()
            
            where_clause = f"WHERE a.agent_id = ?"
            params = [agent_id]
            
            if active_only:
                where_clause += " AND a.is_active = 1"
            
            query_count = f"SELECT COUNT(*) as total FROM admins a {where_clause}"
            count_result = sql.execute_single(query_count, params)
            total = count_result["total"] if count_result else 0
            
            query_list = f"""
            SELECT 
                a.admin_id, a.email, a.agent_id, a.is_active, a.created_at, a.updated_at,
                aa.agent_id as aa_agent_id, aa.code, aa.name, aa.description, aa.is_active as agent_active
            FROM admins a
            LEFT JOIN allowed_agents aa ON a.agent_id = aa.agent_id
            {where_clause}
            ORDER BY a.created_at DESC
            OFFSET ? ROWS
            FETCH NEXT ? ROWS ONLY
            """
            
            params.extend([offset, limit])
            results = sql.execute(query_list, params)
            admins = []
            for r in results:
                admin_dict = AdminService._parse_admin_row(r)
                
                # Buscar features com detalhes
                feature_query = """
                SELECT 
                    f.feature_id,
                    f.agente,
                    f.code,
                    f.name,
                    f.description,
                    f.is_active,
                    f.created_at
                FROM admin_features af
                JOIN features f ON af.feature_id = f.feature_id
                WHERE af.admin_id = ?
                """
                feature_rows = sql.execute(feature_query, (r["admin_id"],))
                admin_dict["features"] = [dict(f) for f in feature_rows]
                admins.append(admin_dict)
            
            logger.info(f"📋 Listados {len(admins)} admins do agent_id {agent_id} (total: {total})")
            
            return {
                "agent_id": agent_id,
                "admins": admins,
                "total": total
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar admins: {e}")
            raise
    
    
    @staticmethod
    def update_admin(admin_id: str, agent_id: Optional[int] = None, feature_ids: Optional[List[int]] = None, 
                     name: Optional[str] = None, job_title: Optional[str] = None, city: Optional[str] = None,
                     updated_by: Optional[str] = None) -> Dict[str, Any]:
        """
        Atualizar admin.
        
        Args:
            admin_id: ID do admin
            agent_id: Novo agent_id (opcional) - (1=LUZ, 2=IGP, 3=SMART)
            feature_ids: Novas features (opcional)
            name: Nome do admin (opcional)
            job_title: Cargo do admin (opcional)
            city: Cidade do admin (opcional)
            updated_by: Nome do usuário que atualizou (opcional)
        
        Returns:
            Admin atualizado
            
        Raises:
            ValueError: Se tentar criar duplicata de (email, agent_id)
        """
        try:
            # Validar agent_id se fornecido
            if agent_id is not None:
                if not AgentService.is_agent_valid_by_id(agent_id):
                    raise ValueError(f"Agent ID inválido: {agent_id}")
            
            sql = get_sqlserver_connection()
            
            # Verificar se admin existe
            admin = AdminService.get_admin_by_id(admin_id)
            if not admin:
                logger.warning(f"⚠️ Admin não encontrado: {admin_id}")
                return None
            
            # Se mudando agent_id, validar que não terá duplicata de (email, agent_id) com admin ATIVO
            if agent_id is not None and agent_id != admin.get("agent_id"):
                email = admin.get("email")
                existing_with_new_agent = AdminService.get_admin_by_email_and_agent_active(email, agent_id)
                if existing_with_new_agent:
                    raise ValueError(f"Já existe um admin ATIVO com email {email} para o agente {agent_id}")
            
            updates = []
            params = []
            
            if agent_id is not None:
                updates.append("agent_id = ?")
                params.append(agent_id)
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            
            if job_title is not None:
                updates.append("job_title = ?")
                params.append(job_title)
            
            if city is not None:
                updates.append("city = ?")
                params.append(city)
            
            if updated_by is not None:
                updates.append("updated_by = ?")
                params.append(updated_by)
            
            # Sempre atualizar updated_at
            updates.append("updated_at = GETUTCDATE()")
            
            # Adicionar admin_id ao final dos params para o WHERE
            params.append(admin_id)
            
            if len(updates) > 1:  # Tem algo além de updated_at
                query = f"""
                UPDATE admins
                SET {', '.join(updates)}
                WHERE admin_id = ?
                """
                
                sql.execute(query, params)
                logger.info(f"✅ Admin atualizado: {admin_id} por {updated_by}")
            
            # Atualizar features se fornecidas
            if feature_ids is not None:
                sql.execute("DELETE FROM admin_features WHERE admin_id = ?", (admin_id,))
                now = datetime.utcnow()
                for fid in feature_ids:
                    sql.execute(
                        "INSERT INTO admin_features (admin_id, feature_id, created_at) VALUES (?, ?, ?)",
                        (admin_id, fid, now)
                    )
                logger.info(f"✅ Features atualizadas para admin {admin_id}")
            
            # Retornar admin atualizado
            updated_admin = AdminService.get_admin_by_id(admin_id)
            
            # Registrar auditoria se houve mudanças
            if len(updates) > 1 and updated_by:  # Tem algo além de updated_at
                try:
                    from app.services.admin_audit_service import AdminAuditService
                    
                    # Construir dicts de antes/depois
                    old_values = {
                        "agent_id": admin.get("agent_id"),
                        "name": admin.get("name"),
                        "job_title": admin.get("job_title"),
                        "city": admin.get("city")
                    }
                    new_values = {
                        "agent_id": updated_admin.get("agent_id"),
                        "name": updated_admin.get("name"),
                        "job_title": updated_admin.get("job_title"),
                        "city": updated_admin.get("city")
                    }
                    
                    AdminAuditService.log_update(
                        admin_id=admin_id,
                        old_values=old_values,
                        new_values=new_values,
                        updated_by=updated_by
                    )
                except Exception as audit_error:
                    logger.error(f"❌ Erro ao registrar auditoria de UPDATE: {audit_error}")
                    # Não interromper a operação se auditoria falhar
            
            return updated_admin
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar admin: {e}")
            raise
    
    
    @staticmethod
    def update_admin_by_email(email: str, name: Optional[str] = None, job_title: Optional[str] = None, 
                            city: Optional[str] = None, agent_id: Optional[int] = None, 
                            feature_ids: Optional[List[int]] = None, updated_by: Optional[str] = None) -> Dict[str, Any]:
        """
        Atualizar admin por email.
        
        Args:
            email: Email do admin
            name: Novo nome (opcional)
            job_title: Novo cargo (opcional)
            city: Nova cidade (opcional)
            agent_id: Novo agent_id (opcional) - (1=LUZ, 2=IGP, 3=SMART)
            feature_ids: Novas features (opcional)
            updated_by: Nome do usuário que atualizou (opcional)
        
        Returns:
            Admin atualizado
        """
        try:
            # Validar agent_id se fornecido
            if agent_id is not None:
                if not AgentService.is_agent_valid_by_id(agent_id):
                    raise ValueError(f"Agent ID inválido: {agent_id}")
            
            sql = get_sqlserver_connection()
            
            # Buscar admin por email
            admin = AdminService.get_admin_by_email(email)
            if not admin:
                logger.warning(f"⚠️ Admin não encontrado: {email}")
                return None
            
            admin_id = admin["admin_id"]
            
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            
            if job_title is not None:
                updates.append("job_title = ?")
                params.append(job_title)
            
            if city is not None:
                updates.append("city = ?")
                params.append(city)
            
            if agent_id is not None:
                updates.append("agent_id = ?")
                params.append(agent_id)
            
            if updated_by is not None:
                updates.append("updated_by = ?")
                params.append(updated_by)
            
            # Sempre atualizar updated_at
            updates.append("updated_at = GETUTCDATE()")
            
            # Adicionar admin_id ao final dos params para o WHERE
            params.append(admin_id)
            
            if len(updates) > 1:  # Tem algo além de updated_at
                query = f"""
                UPDATE admins
                SET {', '.join(updates)}
                WHERE admin_id = ?
                """
                
                sql.execute(query, params)
                logger.info(f"✅ Admin atualizado: {email} por {updated_by}")
            
            # Atualizar features se fornecidas
            if feature_ids is not None:
                sql.execute("DELETE FROM admin_features WHERE admin_id = ?", (admin_id,))
                now = datetime.utcnow()
                for fid in feature_ids:
                    sql.execute(
                        "INSERT INTO admin_features (admin_id, feature_id, created_at) VALUES (?, ?, ?)",
                        (admin_id, fid, now)
                    )
                logger.info(f"✅ Features atualizadas para admin {email}")
            
            # Retornar admin atualizado
            updated_admin = AdminService.get_admin_by_email(email)
            
            # Registrar auditoria se houve mudanças
            if len(updates) > 1 and updated_by:  # Tem algo além de updated_at
                try:
                    from app.services.admin_audit_service import AdminAuditService
                    
                    # Construir dicts de antes/depois
                    old_values = {
                        "name": admin.get("name"),
                        "job_title": admin.get("job_title"),
                        "city": admin.get("city"),
                        "agent_id": admin.get("agent_id")
                    }
                    new_values = {
                        "name": updated_admin.get("name"),
                        "job_title": updated_admin.get("job_title"),
                        "city": updated_admin.get("city"),
                        "agent_id": updated_admin.get("agent_id")
                    }
                    
                    AdminAuditService.log_update(
                        admin_id=admin_id,
                        old_values=old_values,
                        new_values=new_values,
                        updated_by=updated_by
                    )
                except Exception as audit_error:
                    logger.error(f"❌ Erro ao registrar auditoria de UPDATE: {audit_error}")
                    # Não interromper a operação se auditoria falhar
            
            return updated_admin
            
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar admin: {e}")
            raise

    @staticmethod
    def deactivate_admin(admin_id: str, deactivated_by: Optional[str] = None) -> bool:
        """
        Inativar admin (marca is_active = 0).
        
        Mantém o registro no banco e seu histórico de auditoria.
        Permite reativação depois.
        
        Args:
            admin_id: ID do admin
            deactivated_by: Usuário que inativou (para auditoria)
        
        Returns:
            True se inativado, False se não encontrado
        """
        try:
            sql = get_sqlserver_connection()
            
            logger.info(f"[DEACTIVATE_ADMIN] ℹ️ Inativando admin_id: {admin_id}")
            
            # Verificar se existe
            check_query = "SELECT admin_id, email, is_active FROM admins WHERE admin_id = ?"
            check_result = sql.execute_single(check_query, (admin_id,))
            
            if not check_result:
                logger.warning(f"[DEACTIVATE_ADMIN] ⚠️ Admin não encontrado: {admin_id}")
                return False
            
            admin_email = check_result.get("email", "desconhecido")
            logger.info(f"[DEACTIVATE_ADMIN] ✅ Admin encontrado: {admin_email}")
            
            # Executar o UPDATE
            update_query = """
            UPDATE admins
            SET is_active = 0, updated_at = GETUTCDATE()
            WHERE admin_id = ?
            """
            
            sql.execute(update_query, (admin_id,))
            logger.info(f"[DEACTIVATE_ADMIN] ✅ Admin inativado")
            
            # Registrar auditoria
            if deactivated_by:
                try:
                    from app.services.admin_audit_service import AdminAuditService
                    
                    admin_data = {
                        "email": admin_email,
                        "name": check_result.get("name"),
                        "job_title": check_result.get("job_title"),
                        "city": check_result.get("city"),
                        "agent_id": check_result.get("agent_id"),
                        "is_active": check_result.get("is_active", True)
                    }
                    
                    AdminAuditService.log_delete(
                        admin_id=admin_id,
                        admin_data=admin_data,
                        deleted_by=deactivated_by
                    )
                except Exception as audit_error:
                    logger.error(f"[DEACTIVATE_ADMIN] ❌ Erro ao registrar auditoria: {audit_error}")
            
            logger.info(f"[DEACTIVATE_ADMIN] ✅ Admin inativado: {admin_id} ({admin_email})")
            return True
            
        except Exception as e:
            logger.error(f"[DEACTIVATE_ADMIN] ❌ Erro ao inativar admin: {e}", exc_info=True)
            raise
    
    
    @staticmethod
    def permanent_delete_admin(admin_id: str) -> bool:
        """
        Deletar admin PERMANENTEMENTE (hard delete com todas as dependências).
        
        Deleta:
        - admin_features (features do admin)
        - admin_audit_log (histórico de auditoria)
        - admins (o próprio admin)
        
        **CUIDADO: Não pode ser desfeito!**
        
        Args:
            admin_id: ID do admin a deletar permanentemente
        
        Returns:
            True se deletado, False se não encontrado
        """
        try:
            sql = get_sqlserver_connection()
            
            logger.warning(f"[PERMANENT_DELETE_ADMIN] 🔴 Iniciando DELETE PERMANENTE para admin_id: {admin_id}")
            
            # Verificar se existe
            check_query = "SELECT admin_id, email FROM admins WHERE admin_id = ?"
            check_result = sql.execute_single(check_query, (admin_id,))
            
            if not check_result:
                logger.warning(f"[PERMANENT_DELETE_ADMIN] ⚠️ Admin não encontrado: {admin_id}")
                return False
            
            admin_email = check_result.get("email", "desconhecido")
            logger.info(f"[PERMANENT_DELETE_ADMIN] 🔴 Deletando permanentemente: {admin_email}")
            
            # DELETE CASCADE order:
            # 1. admin_features (child of admins)
            sql.execute("DELETE FROM admin_features WHERE admin_id = ?", (admin_id,))
            logger.debug(f"[PERMANENT_DELETE_ADMIN] ✅ admin_features deletadas")
            
            # 2. admin_audit_log (child of admins - se existir FK)
            sql.execute("DELETE FROM admin_audit_log WHERE admin_id = ?", (admin_id,))
            logger.debug(f"[PERMANENT_DELETE_ADMIN] ✅ admin_audit_log deletados")
            
            # 3. admins (parent)
            sql.execute("DELETE FROM admins WHERE admin_id = ?", (admin_id,))
            logger.debug(f"[PERMANENT_DELETE_ADMIN] ✅ admin deletado")
            
            logger.warning(f"[PERMANENT_DELETE_ADMIN] 🔴 DELETE PERMANENTE CONCLUÍDO: {admin_email}")
            return True
            
        except Exception as e:
            logger.error(f"[PERMANENT_DELETE_ADMIN] ❌ Erro ao deletar permanentemente: {e}", exc_info=True)
            raise
    
    
        """Converter row do banco em dict de admin com dados do colaborador e agente."""
        agent_id = row.get("agent_id")  # agent_id da coluna admins.agent_id
        agent_name = row.get("agent_name")  # name da tabela allowed_agents (LUZ, IGP, SMART)
        
        return {
            "admin_id": row["admin_id"],
            "email": row["email"],
            "name": row.get("name"),  # Nome do colaborador
            "job_title": row.get("job_title"),  # Cargo do colaborador
            "city": row.get("city"),  # Cidade do colaborador
            "agent_id": agent_id,
            "agent_name": agent_name,
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"],
            "created_by": row.get("created_by"),  # Nome do usuário que criou
            "updated_at": row["updated_at"],
            "updated_by": row.get("updated_by")  # Nome do usuário que atualizou
        }
    
    
    @staticmethod
    def add_feature_to_admin(admin_id: str, feature_id: int) -> Optional[Dict[str, Any]]:
        """
        Adicionar feature a um admin.
        
        Args:
            admin_id: ID do admin
            feature_id: ID da feature
        
        Returns:
            Admin atualizado com features
            
        Raises:
            ValueError: Se a feature não existe ou está inativa
        """
        try:
            sql = get_sqlserver_connection()
            
            admin = AdminService.get_admin_by_id(admin_id)
            if not admin:
                logger.warning(f"⚠️ Admin não encontrado: {admin_id}")
                return None
            
            # Validar se feature existe e está ativa
            logger.info(f"[ADD_FEATURE] 🔍 Validando se feature {feature_id} existe e está ativa...")
            all_features = AdminService.list_features(active_only=True)
            valid_feature_ids = [f.get("feature_id") for f in all_features]
            
            if feature_id not in valid_feature_ids:
                error_msg = f"Feature {feature_id} não existe ou está inativa. Features válidas: {valid_feature_ids}"
                logger.warning(f"[ADD_FEATURE] ⚠️ {error_msg}")
                raise ValueError(error_msg)
            
            logger.info(f"[ADD_FEATURE] ✅ Feature {feature_id} é válida")
            
            # Verificar se já existe
            existing = sql.execute_single(
                "SELECT 1 FROM admin_features WHERE admin_id = ? AND feature_id = ?",
                (admin_id, feature_id)
            )
            
            if existing:
                logger.info(f"[ADD_FEATURE] ℹ️ Feature já existe para admin {admin_id}: {feature_id}")
                return admin
            
            # Inserir
            sql.execute(
                "INSERT INTO admin_features (admin_id, feature_id, created_at) VALUES (?, ?, ?)",
                (admin_id, feature_id, datetime.utcnow())
            )
            
            logger.info(f"[ADD_FEATURE] ✅ Feature {feature_id} adicionada ao admin {admin_id}")
            return AdminService.get_admin_by_id(admin_id)
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar feature: {e}")
            raise
    
    
    @staticmethod
    def remove_feature_from_admin(admin_id: str, feature_id: int) -> Optional[Dict[str, Any]]:
        """
        Remover feature de um admin.
        
        Args:
            admin_id: ID do admin
            feature_id: ID da feature a remover
        
        Returns:
            Admin atualizado com features
        """
        try:
            sql = get_sqlserver_connection()
            
            admin = AdminService.get_admin_by_id(admin_id)
            if not admin:
                logger.warning(f"⚠️ Admin não encontrado: {admin_id}")
                return None
            
            # Deletar
            sql.execute(
                "DELETE FROM admin_features WHERE admin_id = ? AND feature_id = ?",
                (admin_id, feature_id)
            )
            
            logger.info(f"➖ Feature removida do admin {admin_id}: {feature_id}")
            return AdminService.get_admin_by_id(admin_id)
            
        except Exception as e:
            logger.error(f"❌ Erro ao remover feature: {e}")
            raise
    
    
    @staticmethod
    def list_features(active_only: bool = False, agente: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Listar todas as features disponíveis.
        
        Args:
            active_only: Se True, retorna apenas features ativas
            agente: Se fornecido, filtra features por agente (ex: 'LUZ', 'IGP', 'SMART')
        
        Returns:
            Lista de features com detalhes completos
        """
        try:
            sql = get_sqlserver_connection()
            
            where_clauses = []
            if active_only:
                where_clauses.append("is_active = 1")
            if agente:
                where_clauses.append(f"agente = '{agente}'")
            
            where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            query = f"""
            SELECT 
                feature_id,
                agente,
                code,
                name,
                description,
                is_active,
                created_at
            FROM features
            {where_clause}
            ORDER BY agente, name
            """
            
            results = sql.execute(query, ())
            features = [dict(r) for r in results]
            
            if agente:
                logger.info(f"📋 Listadas {len(features)} features para agente '{agente}'")
            else:
                logger.info(f"📋 Listadas {len(features)} features")
            return features
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar features: {e}")
            raise
    
    @staticmethod
    def _parse_admin_row(row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converter row do banco em dict de admin com dados formatados.
        
        Converte valores SQL para tipos Python apropriados:
        - is_active: 1/0 → True/False
        - agent_id: NULL → None
        - agent_name: NULL quando não há agente associado
        
        Args:
            row: Dicionário com dados do admin da query SQL
            
        Returns:
            Dicionário formatado com tipos Python corretos
        """
        return {
            "admin_id": row.get("admin_id"),
            "email": row.get("email"),
            "name": row.get("name"),
            "job_title": row.get("job_title"),
            "city": row.get("city"),
            "agent_id": row.get("agent_id"),
            "agent_name": row.get("agent_name"),
            "is_active": bool(row.get("is_active", 0)),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at")
        }
