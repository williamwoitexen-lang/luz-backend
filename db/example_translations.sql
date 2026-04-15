-- Example: Adding translations to dim_roles and dim_categories
-- This script shows how to populate the translations JSON column
-- NOTE: SQL Server uses JSON strings, not JSON_OBJECT function (that's MySQL)

-- ============================================================
-- ROLES TRANSLATIONS EXAMPLES
-- ============================================================

-- Example 1: Analista
UPDATE dim_roles SET translations = '{"en": {"role_name": "Analyst"}, "es": {"role_name": "Analista"}}' WHERE role_id = 1;

-- Example 2: Administrador
UPDATE dim_roles SET translations = '{"en": {"role_name": "Administrator"}, "es": {"role_name": "Administrador"}}' WHERE role_id = 2;

-- Example 3: Assistente
UPDATE dim_roles SET translations = '{"en": {"role_name": "Assistant"}, "es": {"role_name": "Asistente"}}' WHERE role_id = 3;

-- Example 4: Coordenador
UPDATE dim_roles SET translations = '{"en": {"role_name": "Coordinator"}, "es": {"role_name": "Coordinador"}}' WHERE role_id = 4;

-- Example 5: Diretor
UPDATE dim_roles SET translations = '{"en": {"role_name": "Director"}, "es": {"role_name": "Director"}}' WHERE role_id = 5;

-- Example 6: Especialista
UPDATE dim_roles SET translations = '{"en": {"role_name": "Specialist"}, "es": {"role_name": "Especialista"}}' WHERE role_id = 6;

-- Example 7: Estagiário
UPDATE dim_roles SET translations = '{"en": {"role_name": "Intern"}, "es": {"role_name": "Pasante"}}' WHERE role_id = 7;

-- Example 8: Gerente
UPDATE dim_roles SET translations = '{"en": {"role_name": "Manager"}, "es": {"role_name": "Gerente"}}' WHERE role_id = 8;

-- Example 9: Gerente Sênior
UPDATE dim_roles SET translations = '{"en": {"role_name": "Senior Manager"}, "es": {"role_name": "Gerente Senior"}}' WHERE role_id = 9;

-- Example 10: Head (Executivo)
UPDATE dim_roles SET translations = '{"en": {"role_name": "Head"}, "es": {"role_name": "Director Ejecutivo"}}' WHERE role_id = 10;

-- Example 11: Operacional
UPDATE dim_roles SET translations = '{"en": {"role_name": "Operational"}, "es": {"role_name": "Operacional"}}' WHERE role_id = 11;

-- Example 12: Presidente
UPDATE dim_roles SET translations = '{"en": {"role_name": "President"}, "es": {"role_name": "Presidente"}}' WHERE role_id = 12;

-- Example 13: Supervisor
UPDATE dim_roles SET translations = '{"en": {"role_name": "Supervisor"}, "es": {"role_name": "Supervisor"}}' WHERE role_id = 13;

-- Example 14: Técnico
UPDATE dim_roles SET translations = '{"en": {"role_name": "Technician"}, "es": {"role_name": "Técnico"}}' WHERE role_id = 14;

-- Example 15: Vice-Presidente
UPDATE dim_roles SET translations = '{"en": {"role_name": "Vice President"}, "es": {"role_name": "Vicepresidente"}}' WHERE role_id = 15;

-- ============================================================
-- CATEGORIES TRANSLATIONS EXAMPLES
-- ============================================================

-- Example 1: Health Insurance
UPDATE dim_categories SET translations = '{"en": {"category_name": "Health Insurance", "description": "Medical and health coverage"}, "es": {"category_name": "Seguro de Salud", "description": "Cobertura médica y de salud"}}' WHERE category_id = 1;

-- Example 2: Dental Plan
UPDATE dim_categories SET translations = '{"en": {"category_name": "Dental Plan", "description": "Dental coverage and orthodontics"}, "es": {"category_name": "Plan Dental", "description": "Cobertura dental y ortodoncia"}}' WHERE category_id = 2;

-- Example 3: Vision Plan
UPDATE dim_categories SET translations = '{"en": {"category_name": "Vision Plan", "description": "Eye care and glasses coverage"}, "es": {"category_name": "Plan de Visión", "description": "Cuidado de los ojos y cobertura de gafas"}}' WHERE category_id = 3;

-- Example 4: Retirement Plan
UPDATE dim_categories SET translations = '{"en": {"category_name": "Retirement Plan", "description": "401k and pension benefits"}, "es": {"category_name": "Plan de Jubilación", "description": "Beneficios 401k y pensión"}}' WHERE category_id = 4;

-- Example 5: Life Insurance
UPDATE dim_categories SET translations = '{"en": {"category_name": "Life Insurance", "description": "Life insurance coverage"}, "es": {"category_name": "Seguro de Vida", "description": "Cobertura de seguro de vida"}}' WHERE category_id = 5;

-- Example 6: Disability Insurance
UPDATE dim_categories SET translations = '{"en": {"category_name": "Disability Insurance", "description": "Short and long-term disability"}, "es": {"category_name": "Seguro de Incapacidad", "description": "Incapacidad a corto y largo plazo"}}' WHERE category_id = 6;

-- Example 7: Flexible Spending Account
UPDATE dim_categories SET translations = '{"en": {"category_name": "Flexible Spending Account", "description": "FSA for healthcare and dependent care"}, "es": {"category_name": "Cuenta Flexible de Gastos", "description": "FSA para cuidado de la salud y dependientes"}}' WHERE category_id = 7;

-- Example 8: Stock Options
UPDATE dim_categories SET translations = '{"en": {"category_name": "Stock Options", "description": "Employee stock purchase plan"}, "es": {"category_name": "Opciones de Acciones", "description": "Plan de compra de acciones de empleados"}}' WHERE category_id = 8;

-- Example 9: Tuition Reimbursement
UPDATE dim_categories SET translations = '{"en": {"category_name": "Tuition Reimbursement", "description": "Education and professional development"}, "es": {"category_name": "Reembolso de Matrícula", "description": "Educación y desarrollo profesional"}}' WHERE category_id = 9;

-- Example 10: Commuter Benefits
UPDATE dim_categories SET translations = '{"en": {"category_name": "Commuter Benefits", "description": "Public transit and parking benefits"}, "es": {"category_name": "Beneficios de Transporte", "description": "Beneficios de transporte público y estacionamiento"}}' WHERE category_id = 10;

-- Example 11: Holiday and Time Off
UPDATE dim_categories SET translations = '{"en": {"category_name": "Holiday and Time Off", "description": "Vacation, sick leave, and paid time off"}, "es": {"category_name": "Feriados y Licencias", "description": "Vacaciones, licencia por enfermedad y tiempo libre"}}' WHERE category_id = 11;

-- Example 12: Desk and Office
UPDATE dim_categories SET translations = '{"en": {"category_name": "Desk and Office", "description": "Office setup and ergonomic equipment"}, "es": {"category_name": "Escritorio y Oficina", "description": "Configuración de oficina y equipamiento ergonómico"}}' WHERE category_id = 12;

-- Example 13: Internal Transfers
UPDATE dim_categories SET translations = '{"en": {"category_name": "Internal Transfers", "description": "Internal job transfers and promotions"}, "es": {"category_name": "Transferencias Internas", "description": "Transferencias y promociones laborales internas"}}' WHERE category_id = 13;

-- Example 14: Policies and Rules
UPDATE dim_categories SET translations = '{"en": {"category_name": "Policies and Rules", "description": "Company policies and business rules"}, "es": {"category_name": "Políticas y Normas", "description": "Políticas de la empresa y reglas comerciales"}}' WHERE category_id = 14;

-- ============================================================
-- TESTING TRANSLATIONS
-- ============================================================

-- Test: Query with translations
/*
SELECT 
  role_id, 
  role_name, 
  translations,
  JSON_VALUE(translations, '$.en.role_name') as name_en,
  JSON_VALUE(translations, '$.es.role_name') as name_es
FROM dim_roles
WHERE role_id = 1;

-- Result should show:
-- role_id | role_name | translations | name_en | name_es
-- 1 | Analista | {...} | Analyst | Analista
*/

-- ============================================================
-- API USAGE EXAMPLES
-- ============================================================

/*
Portuguese (default - no parameter needed):
GET /api/v1/master-data/roles
GET /api/v1/master-data/categories

English:
GET /api/v1/master-data/roles?language=en
GET /api/v1/master-data/categories?language=en

Spanish:
GET /api/v1/master-data/roles?language=es
GET /api/v1/master-data/categories?language=es

With filtering:
GET /api/v1/master-data/roles?language=es&active_only=true
GET /api/v1/master-data/categories?language=en&active_only=true
*/
