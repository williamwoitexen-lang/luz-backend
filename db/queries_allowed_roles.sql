-- Queries úteis para trabalhar com allowed_roles JSON

-- =====================================================
-- 1. VER DOCUMENTOS COM ROLES ESPECÍFICOS
-- =====================================================

-- Documentos que têm allowed_roles definido
SELECT document_id, title, user_id, min_role_level, allowed_roles
FROM documents
WHERE allowed_roles IS NOT NULL
ORDER BY created_at DESC;


-- =====================================================
-- 2. EXTRAIR ROLES COM JSON_VALUE (SQL Server)
-- =====================================================

-- Ver primeiro role de um documento
SELECT 
    document_id, 
    title,
    JSON_VALUE(allowed_roles, '$[0]') AS first_role,
    JSON_VALUE(allowed_roles, '$[1]') AS second_role,
    JSON_VALUE(allowed_roles, '$[2]') AS third_role
FROM documents
WHERE allowed_roles IS NOT NULL;


-- =====================================================
-- 3. FILTRAR DOCUMENTOS POR ROLE (usando LIKE)
-- =====================================================

-- Documentos que incluem role 'admin'
SELECT document_id, title, allowed_roles
FROM documents
WHERE allowed_roles LIKE '%"admin"%'
ORDER BY created_at DESC;

-- Documentos que incluem role 'manager'
SELECT document_id, title, allowed_roles
FROM documents
WHERE allowed_roles LIKE '%"manager"%'
ORDER BY created_at DESC;


-- =====================================================
-- 4. FILTRAR POR MÚLTIPLOS CRITÉRIOS
-- =====================================================

-- Documentos ativos de um user que têm allowed_roles definido
SELECT document_id, title, user_id, is_active, allowed_roles
FROM documents
WHERE user_id = 'admin@company.com'
  AND is_active = 1
  AND allowed_roles IS NOT NULL
ORDER BY created_at DESC;


-- =====================================================
-- 5. MIGRAÇÃO: PREENCHER allowed_roles BASEADO EM min_role_level
-- =====================================================

-- Exemplo: Converter min_role_level=1 em allowed_roles com roles padrão
-- (Apenas após validar a lógica de mapeamento)

-- UPDATE documents
-- SET allowed_roles = '["standard_user", "manager", "admin"]'
-- WHERE min_role_level = 1 AND allowed_roles IS NULL;


-- =====================================================
-- 6. COMPARAR min_role_level vs allowed_roles
-- =====================================================

-- Documentos usando AMBOS (allowed_roles tem prioridade)
SELECT 
    document_id, 
    title, 
    min_role_level,
    allowed_roles,
    CASE 
        WHEN allowed_roles IS NOT NULL THEN 'allowed_roles (specific roles)'
        ELSE 'min_role_level (fallback)'
    END AS access_method
FROM documents
ORDER BY created_at DESC;


-- =====================================================
-- 7. VALIDAR JSON VÁLIDO
-- =====================================================

-- Documentos com allowed_roles inválidos (não é JSON válido)
SELECT document_id, title, allowed_roles
FROM documents
WHERE allowed_roles IS NOT NULL
  AND ISJSON(allowed_roles) = 0;

-- Documentos com allowed_roles válido
SELECT document_id, title, allowed_roles
FROM documents
WHERE allowed_roles IS NOT NULL
  AND ISJSON(allowed_roles) = 1;


-- =====================================================
-- 8. ATUALIZAR ALLOWED_ROLES
-- =====================================================

-- Adicionar novo role a um documento existente
-- Nota: Converter JSON → array → adicionar → converter JSON

UPDATE documents
SET allowed_roles = '["admin", "manager", "supervisor", "coordinator"]'
WHERE document_id = 'seu-uuid-aqui';


-- =====================================================
-- 9. LIMPAR ALLOWED_ROLES
-- =====================================================

-- Remover allowed_roles de um documento (voltar para min_role_level)
UPDATE documents
SET allowed_roles = NULL
WHERE document_id = 'seu-uuid-aqui';


-- =====================================================
-- 10. ESTATÍSTICAS
-- =====================================================

-- Contar documentos por método de acesso
SELECT 
    CASE 
        WHEN allowed_roles IS NOT NULL THEN 'allowed_roles'
        WHEN min_role_level IS NOT NULL THEN 'min_role_level'
        ELSE 'none (public)'
    END AS access_method,
    COUNT(*) AS document_count
FROM documents
WHERE is_active = 1
GROUP BY 
    CASE 
        WHEN allowed_roles IS NOT NULL THEN 'allowed_roles'
        WHEN min_role_level IS NOT NULL THEN 'min_role_level'
        ELSE 'none (public)'
    END
ORDER BY document_count DESC;
