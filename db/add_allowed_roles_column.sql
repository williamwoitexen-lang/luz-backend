-- Migração: Adicionar coluna allowed_roles para suportar múltiplos roles na ingestão
-- Data: 2026-01-14
-- Descrição: Permite especificar múltiplos roles na ingestão de documentos
--           Mantém min_role_level como fallback

ALTER TABLE documents
ADD allowed_roles NVARCHAR(MAX) NULL
    CONSTRAINT DF_documents_allowed_roles DEFAULT NULL;

-- Criar índice para performance em buscas por roles
CREATE INDEX idx_documents_allowed_roles ON documents(user_id, is_active, allowed_roles);

-- Exemplo de uso: roles como JSON array
-- Para um documento acessível por roles 'admin', 'manager', 'supervisor':
-- allowed_roles = '["admin", "manager", "supervisor"]'

-- Query para verificar documentos com roles específicos:
-- SELECT * FROM documents WHERE allowed_roles IS NOT NULL AND JSON_VALUE(allowed_roles, '$[0]') IS NOT NULL;
