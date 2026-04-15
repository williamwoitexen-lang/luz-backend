-- Migration: Add translations support to dim_roles and dim_categories
-- Date: 2026-03-03
-- Description: NOTE: Colunas translations já existem! Este script é apenas para referência.
-- As colunas já estão criadas como NVARCHAR(MAX) com default '{}'

-- Verificar se translations já existe em dim_roles
SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'dim_roles' AND COLUMN_NAME = 'translations';

-- Verificar se translations já existe em dim_categories
SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'dim_categories' AND COLUMN_NAME = 'translations';
