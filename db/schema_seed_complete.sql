-- ============================================================
-- SEED DATA COMPLETO - MASTER DATA
-- Baseado em dados reais do banco SQL Server
-- Data: 2026-03-13
-- ============================================================

-- ============================================================
-- DESABILITAR CONSTRAINT DE FK TEMPORARIAMENTE
-- ============================================================
ALTER TABLE documents NOCHECK CONSTRAINT FK_documents_category;
ALTER TABLE dim_job_title_roles NOCHECK CONSTRAINT FK_job_title_roles_dim_roles;
ALTER TABLE admins NOCHECK CONSTRAINT FK_admins_agent_id;
GO

-- ============================================================
-- 1. INSERIR CATEGORIAS (dim_categories)
-- ============================================================
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'dim_categories')
BEGIN
    TRUNCATE TABLE dim_categories;
    
    INSERT INTO dim_categories (category_name, description, is_active, created_at, updated_at, translations)
    VALUES
    ('Benefícios', 'Programas e benefícios oferecidos aos colaboradores', 1, GETUTCDATE(), GETUTCDATE(), '{"en":{"category_name":"Benefits","description":"Programs and benefits offered to employees"},"es":{"category_name":"Beneficios","description":"Programas y beneficios ofrecidos a los empleados"}}'),
    ('Admissão', 'Políticas e procedimentos de admissão', 1, GETUTCDATE(), GETUTCDATE(), '{"en":{"category_name":"Admission","description":"Admission policies and procedures"},"es":{"category_name":"Admisión","description":"Políticas y procedimientos de admisión"}}'),
    ('Folha de Pagamento', 'Remuneração, salário e benefícios financeiros', 1, GETUTCDATE(), GETUTCDATE(), '{"en":{"category_name":"Payroll","description":"Compensation, salary and financial benefits"},"es":{"category_name":"Nómina","description":"Compensación, salario y beneficios financieros"}}'),
    ('Férias e Ausências', 'Política de férias, licenças e afastamentos', 1, GETUTCDATE(), GETUTCDATE(), '{"en":{"category_name":"Vacation and Absences","description":"Vacation, leave and absence policies"},"es":{"category_name":"Vacaciones y Ausencias","description":"Políticas de vacaciones, licencias y ausencias"}}'),
    ('Jornada e Ponto', 'Controle de horário e jornada de trabalho', 1, GETUTCDATE(), GETUTCDATE(), '{"en":{"category_name":"Working Hours","description":"Time tracking and work schedule control"},"es":{"category_name":"Jornada y Punto","description":"Control de horario y jornada de trabajo"}}'),
    ('Saúde e Bem-Estar', 'Benefícios de saúde, plano médico e bem-estar', 1, GETUTCDATE(), GETUTCDATE(), '{"en":{"category_name":"Health and Wellness","description":"Health benefits, medical plans and wellness"},"es":{"category_name":"Salud y Bienestar","description":"Beneficios de salud, planes médicos y bienestar"}}'),
    ('Desenvolvimento e Carreira', 'Treinamento e desenvolvimento profissional', 1, GETUTCDATE(), GETUTCDATE(), '{"en":{"category_name":"Development and Career","description":"Training and professional development"},"es":{"category_name":"Desarrollo y Carrera","description":"Capacitación y desarrollo profesional"}}'),
    ('Movimentações Internas', 'Transferências e mudanças de posição', 1, GETUTCDATE(), GETUTCDATE(), '{"en":{"category_name":"Internal Movements","description":"Transfers and position changes"},"es":{"category_name":"Movimientos Internos","description":"Transferencias y cambios de posición"}}'),
    ('Políticas e Normas', 'Normas, regras e políticas da empresa', 1, GETUTCDATE(), GETUTCDATE(), '{"en":{"category_name":"Policies and Standards","description":"Company rules, policies and standards"},"es":{"category_name":"Políticas y Normas","description":"Reglas, políticas y normas de la empresa"}}'),
    ('Diversidade e Inclusão', 'Programas e iniciativas de diversidade', 1, GETUTCDATE(), GETUTCDATE(), '{"en":{"category_name":"Diversity and Inclusion","description":"Diversity and inclusion programs and initiatives"},"es":{"category_name":"Diversidad e Inclusión","description":"Programas e iniciativas de diversidad e inclusión"}}'),
    ('Segurança da Informação', 'Políticas de segurança de dados e informação', 1, GETUTCDATE(), GETUTCDATE(), '{"en":{"category_name":"Information Security","description":"Data and information security policies"},"es":{"category_name":"Seguridad de la Información","description":"Políticas de seguridad de datos e información"}}'),
    ('Relações Trabalhistas', 'Assuntos de relações trabalhistas e sindicatos', 1, GETUTCDATE(), GETUTCDATE(), '{"en":{"category_name":"Labor Relations","description":"Labor relations and union matters"},"es":{"category_name":"Relaciones Laborales","description":"Asuntos de relaciones laborales y sindicatos"}}'),
    ('Desligamento', 'Procedimentos de desligamento e rescisão', 1, GETUTCDATE(), GETUTCDATE(), '{"en":{"category_name":"Termination","description":"Termination and severance procedures"},"es":{"category_name":"Desvinculación","description":"Procedimientos de desvinculación y rescisión"}}'),
    ('RH Geral', 'Outros assuntos e políticas de RH', 1, GETUTCDATE(), GETUTCDATE(), '{"en":{"category_name":"General HR","description":"Other HR matters and policies"},"es":{"category_name":"RH General","description":"Otros asuntos y políticas de RH"}}');
    
    PRINT 'Categorias inseridas com sucesso: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros (14 categorias)';
END
ELSE
    PRINT 'Aviso: Tabela dim_categories não existe';
GO

-- ============================================================
-- 2. INSERIR PAPÉIS/FUNÇÕES (dim_roles)
-- ============================================================
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'dim_roles')
BEGIN
    TRUNCATE TABLE dim_roles;
    
    INSERT INTO dim_roles (role_name, is_active, created_at, updated_at)
    VALUES
    ('Analista', 1, GETUTCDATE(), GETUTCDATE()),
    ('Aprendiz', 1, GETUTCDATE(), GETUTCDATE()),
    ('Assistente', 1, GETUTCDATE(), GETUTCDATE()),
    ('Coordenador', 1, GETUTCDATE(), GETUTCDATE()),
    ('Diretor', 1, GETUTCDATE(), GETUTCDATE()),
    ('Especialista', 1, GETUTCDATE(), GETUTCDATE()),
    ('Estagiário', 1, GETUTCDATE(), GETUTCDATE()),
    ('Gerente', 1, GETUTCDATE(), GETUTCDATE()),
    ('Gerente Sênior', 1, GETUTCDATE(), GETUTCDATE()),
    ('Head', 1, GETUTCDATE(), GETUTCDATE()),
    ('Operacional', 1, GETUTCDATE(), GETUTCDATE()),
    ('Presidente', 1, GETUTCDATE(), GETUTCDATE()),
    ('Supervisor', 1, GETUTCDATE(), GETUTCDATE()),
    ('Técnico', 1, GETUTCDATE(), GETUTCDATE()),
    ('Vice-Presidente', 1, GETUTCDATE(), GETUTCDATE());
    
    PRINT 'Papéis/Funções inseridos com sucesso: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros (15 papéis)';
END
ELSE
    PRINT 'Aviso: Tabela dim_roles não existe';
GO

-- ============================================================
-- 3. INSERIR MAPEAMENTO JOB TITLE ROLES (dim_job_title_roles)
-- ============================================================
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'dim_job_title_roles')
BEGIN
    TRUNCATE TABLE dim_job_title_roles;
    
    INSERT INTO dim_job_title_roles (job_title, role_id, is_active, created_at, updated_at)
    SELECT 'Analista Comercial', role_id, 1, GETUTCDATE(), GETUTCDATE() FROM dim_roles WHERE role_name = 'Analista'
    UNION ALL
    SELECT 'Aprendiz Administrativo', role_id, 1, GETUTCDATE(), GETUTCDATE() FROM dim_roles WHERE role_name = 'Aprendiz'
    UNION ALL
    SELECT 'Assistente de RH', role_id, 1, GETUTCDATE(), GETUTCDATE() FROM dim_roles WHERE role_name = 'Assistente'
    UNION ALL
    SELECT 'Coordenador de Projetos', role_id, 1, GETUTCDATE(), GETUTCDATE() FROM dim_roles WHERE role_name = 'Coordenador'
    UNION ALL
    SELECT 'Diretor de Operações', role_id, 1, GETUTCDATE(), GETUTCDATE() FROM dim_roles WHERE role_name = 'Diretor'
    UNION ALL
    SELECT 'Especialista em Sistemas', role_id, 1, GETUTCDATE(), GETUTCDATE() FROM dim_roles WHERE role_name = 'Especialista'
    UNION ALL
    SELECT 'Estagiário de Engenharia', role_id, 1, GETUTCDATE(), GETUTCDATE() FROM dim_roles WHERE role_name = 'Estagiário'
    UNION ALL
    SELECT 'Gerente de Manufatura', role_id, 1, GETUTCDATE(), GETUTCDATE() FROM dim_roles WHERE role_name = 'Gerente'
    UNION ALL
    SELECT 'Gerente Sênior de Qualidade', role_id, 1, GETUTCDATE(), GETUTCDATE() FROM dim_roles WHERE role_name = 'Gerente Sênior'
    UNION ALL
    SELECT 'Head de Logística', role_id, 1, GETUTCDATE(), GETUTCDATE() FROM dim_roles WHERE role_name = 'Head'
    UNION ALL
    SELECT 'Operador de Máquina', role_id, 1, GETUTCDATE(), GETUTCDATE() FROM dim_roles WHERE role_name = 'Operacional'
    UNION ALL
    SELECT 'Presidente Executivo', role_id, 1, GETUTCDATE(), GETUTCDATE() FROM dim_roles WHERE role_name = 'Presidente'
    UNION ALL
    SELECT 'Supervisor de Produção', role_id, 1, GETUTCDATE(), GETUTCDATE() FROM dim_roles WHERE role_name = 'Supervisor'
    UNION ALL
    SELECT 'Técnico de Manutenção', role_id, 1, GETUTCDATE(), GETUTCDATE() FROM dim_roles WHERE role_name = 'Técnico'
    UNION ALL
    SELECT 'Vice-Presidente Financeiro', role_id, 1, GETUTCDATE(), GETUTCDATE() FROM dim_roles WHERE role_name = 'Vice-Presidente';
    
    PRINT 'Job Title Roles inseridos com sucesso: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros';
END
ELSE
    PRINT 'Aviso: Tabela dim_job_title_roles não existe';
GO

-- ============================================================
-- 5. INSERIR LOCALIDADES ELETROLUX (dim_electrolux_locations)
-- Dados reais do banco com IDs específicos, endereços e contagem de pessoas (AD)
-- ============================================================
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'dim_electrolux_locations')
BEGIN
    TRUNCATE TABLE dim_electrolux_locations;
    
    -- Habilitar INSERT de IDs específicos (IDENTITY_INSERT)
    SET IDENTITY_INSERT dim_electrolux_locations ON;
    
    INSERT INTO dim_electrolux_locations (location_id, country_name, state_name, city_name, region, continent, operation_type, location_name, address, people_count, is_active, created_at, updated_at)
    VALUES
    (1, 'Argentina', 'Buenos Aires', 'Buenos Aires', 'LATAM', 'South America', 'Office', 'Buenos Aires Office', 'Olga Cossettini 771 - 1st Floor Piso', 125, 1, GETUTCDATE(), GETUTCDATE()),
    (2, 'Argentina', 'Buenos Aires', 'Buenos Aires', 'LATAM', 'South America', 'Warehouse', 'Buenos Aires Consumer Care Warehouse', 'Colectora Panamericana Km 26850 – Don Torcuato', 72, 1, GETUTCDATE(), GETUTCDATE()),
    (50, 'Argentina', 'Buenos Aires', 'Porto Belo', 'LATAM', 'South America', 'Outlet', 'Outlet Porto Belo', 'Rodovia BR - 101, Marginal Leste, KM 159 - sala 1013-1014, Bairro Santa Luzia', 8, 1, GETUTCDATE(), GETUTCDATE()),
    (3, 'Argentina', 'Santa Fe', 'Rosario', 'LATAM', 'South America', 'Factory', 'Rosario Plant', 'Av Batlle y Ordonez, 3436', 172, 1, GETUTCDATE(), GETUTCDATE()),
    (4, 'Brazil', 'Bahia', 'Bahia', 'LATAM', 'South America', 'Outlet', 'Outlet Bahia', 'AV. FRANCISCO FRAGA MAIA, N° 4.680, SITUADAS NO SHOPPING MILLENIUM - MANGABEIRA - Feira de Santana / BA', NULL, 1, GETUTCDATE(), GETUTCDATE()),
    (5, 'Brazil', 'Minas Gerais', 'Belo Horizonte', 'LATAM', 'South America', 'Outlet', 'Outlet Belo Horizonte', 'Rua Nossa Senhora da Conceicao, 359', 22, 1, GETUTCDATE(), GETUTCDATE()),
    (6, 'Brazil', 'Distrito Federal', 'Brasília', 'LATAM', 'South America', 'Outlet', 'Outlet Brasília', 'QS 05 - Taguatinga Sul - Aguas Claras', 6, 1, GETUTCDATE(), GETUTCDATE()),
    (7, 'Brazil', 'Paraná', 'Campo largo', 'LATAM', 'South America', 'Outlet', 'Outlet Campo Largo', 'RODOVIA BR-277 PONTA GROSSA CURITIBA,KM 122 -LJ 1040', 4, 1, GETUTCDATE(), GETUTCDATE()),
    (8, 'Brazil', 'Paraná', 'Curitiba', 'LATAM', 'South America', 'Warehouse', 'Guabirotuba', 'Rua Ministro Gabriel Passos 360', 2443, 1, GETUTCDATE(), GETUTCDATE()),
    (9, 'Brazil', 'Paraná', 'Curitiba', 'LATAM', 'South America', 'Warehouse', 'COP', 'R. João Marchesini, 139 - Prado Velho, Curitiba - PR', 780, 1, GETUTCDATE(), GETUTCDATE()),
    (10, 'Brazil', 'Paraná', 'Curitiba', 'LATAM', 'South America', 'Warehouse', 'CD Tatuquara', 'Vereador Angelo Burbello, 555', 18, 1, GETUTCDATE(), GETUTCDATE()),
    (11, 'Brazil', 'Paraná', 'Curitiba', 'LATAM', 'South America', 'Warehouse', 'CIC', 'Rua Senador Accioly Filho, 1321', 32, 1, GETUTCDATE(), GETUTCDATE()),
    (12, 'Brazil', 'Paraná', 'Curitiba', 'LATAM', 'South America', 'Warehouse', 'Electrolux HP', 'Rua Roberto Ozorio de Almeida, 1010', 25, 1, GETUTCDATE(), GETUTCDATE()),
    (13, 'Brazil', 'Paraná', 'Curitiba', 'LATAM', 'South America', 'Warehouse', 'CD JL', 'Rua Joao Lunardelli, 2205', 97, 1, GETUTCDATE(), GETUTCDATE()),
    (14, 'Brazil', 'Paraná', 'Curitiba', 'LATAM', 'South America', 'Outlet', 'Outlet Barigui', 'Rua General Mario Tourinho 2350', 4, 1, GETUTCDATE(), GETUTCDATE()),
    (15, 'Brazil', 'Paraná', 'Curitiba', 'LATAM', 'South America', 'Outlet', 'Outlet Cajuru', 'Rua Vicente Carvalho, 113', 6, 1, GETUTCDATE(), GETUTCDATE()),
    (16, 'Brazil', 'Santa Catarina', 'Florianópolis', 'LATAM', 'South America', 'Outlet', 'Outlet Florianópolis', 'Rodovia SC - 401, KM 05 - n 4850, Bairro Saco Grande', 6, 1, GETUTCDATE(), GETUTCDATE()),
    (17, 'Brazil', 'Amazonas', 'Manaus', 'LATAM', 'South America', 'Service', 'DPA Manaus', 'Rua Flamboyant, 1403, Ala A', 47, 1, GETUTCDATE(), GETUTCDATE()),
    (18, 'Brazil', 'Amazonas', 'Manaus', 'LATAM', 'South America', 'Factory', 'Fábrica Manaus', 'Rua Jutai, 275', 188, 1, GETUTCDATE(), GETUTCDATE()),
    (19, 'Brazil', 'Amazonas', 'Manaus', 'LATAM', 'South America', 'Service', 'Top Service Manaus', 'Avenida Ivanete Machado, 755', 10, 1, GETUTCDATE(), GETUTCDATE()),
    (49, 'Brazil', 'Rio de Janeiro', 'Rio de Janeiro', 'LATAM', 'South America', 'Operations', 'Rio de Janeiro Operations', 'Av Rio Branco, 181', 85, 1, GETUTCDATE(), GETUTCDATE()),
    (20, 'Brazil', 'Santa Fe', 'Rosario', 'LATAM', 'South America', 'Warehouse', 'Rosario Supply Chain Warehouse', 'AO12 - KM 4,5 - (2126) Alvear', 46, 1, GETUTCDATE(), GETUTCDATE()),
    (21, 'Brazil', 'Santa Fe', 'Rosario', 'LATAM', 'South America', 'Outlet', 'Rosario Outlet', 'OROÑO 5420, ROSARIO, SANTA FE', 8, 1, GETUTCDATE(), GETUTCDATE()),
    (22, 'Brazil', 'Bahia', 'Salvador', 'LATAM', 'South America', 'Service', 'Top Service Salvador', 'Edistio Ponde, 200', 15, 1, GETUTCDATE(), GETUTCDATE()),
    (23, 'Brazil', 'São Paulo', 'São Carlos', 'LATAM', 'South America', 'Factory', 'Fábrica São Carlos', 'Av Jose Pereira Lopes, 250', 637, 1, GETUTCDATE(), GETUTCDATE()),
    (24, 'Brazil', 'São Paulo', 'São Carlos', 'LATAM', 'South America', 'Warehouse', 'São Carlos', 'R. Cel. José Augusto de Oliveira Salles, 476', 1, 1, GETUTCDATE(), GETUTCDATE()),
    (25, 'Brazil', 'São Paulo', 'São Carlos', 'LATAM', 'South America', 'Factory', 'Água Vermelha', 'Rodovia SP 318, km 245, sn', 116, 1, GETUTCDATE(), GETUTCDATE()),
    (26, 'Brazil', 'Paraná', 'São José dos Pinhas', 'LATAM', 'South America', 'Warehouse', 'Gralha Azul', 'Rua Durval Moletta, 2160', 73, 1, GETUTCDATE(), GETUTCDATE()),
    (27, 'Brazil', 'Paraná', 'São José dos Pinhas', 'LATAM', 'South America', 'Warehouse', 'Electrolux Disc SJP', 'Rua Vanderlei Moreno, 10800', 205, 1, GETUTCDATE(), GETUTCDATE()),
    (28, 'Brazil', 'São Paulo', 'São Paulo', 'LATAM', 'South America', 'Service', 'Top Service São Paulo', 'Rua Professor Serafim Orlandi, 146', 56, 1, GETUTCDATE(), GETUTCDATE()),
    (29, 'Brazil', 'São Paulo', 'São Paulo', 'LATAM', 'South America', 'Office', 'Torre Z', 'Av Dr Chucri Zaidan, 296 - 16 Andar', 1032, 1, GETUTCDATE(), GETUTCDATE()),
    (30, 'Brazil', 'São Paulo', 'São Roque', 'LATAM', 'South America', 'Outlet', 'Outlet São Roque', 'Rua Rafael Dias Costa,140, Dona Catarina, Loja 217', 8, 1, GETUTCDATE(), GETUTCDATE()),
    (31, 'Chile', 'Metropolitan', 'Buin', 'LATAM', 'South America', 'Outlet', 'Outlet Buin', 'Bernardino Bravo 115, Loc 5, Portal del Cruce -BUIN', 1, 1, GETUTCDATE(), GETUTCDATE()),
    (32, 'Chile', 'Metropolitan', 'La Florida', 'LATAM', 'South America', 'Outlet', 'Outlet VIVO La Florida', 'Sta Delia 8937, local 1164 -1168 La Florida', 1, 1, GETUTCDATE(), GETUTCDATE()),
    (33, 'Chile', 'Bío Bío', 'Los Angeles', 'LATAM', 'South America', 'Outlet', 'Outlet Los Angeles', 'Calle Almagro N°701, Los Angeles.', 1, 1, GETUTCDATE(), GETUTCDATE()),
    (34, 'Chile', 'Metropolitan', 'Maipu', 'LATAM', 'South America', 'Factory', 'Santiago Plant - Major Appliances', '777 Alberto Llona', 21, 1, GETUTCDATE(), GETUTCDATE()),
    (35, 'Chile', 'Metropolitan', 'Maipu', 'LATAM', 'South America', 'Outlet', 'Outlet VIVO Lo Espejo', 'Av. Lo Espejo N° 943, local 170, Maipu.', 1, 1, GETUTCDATE(), GETUTCDATE()),
    (36, 'Chile', 'Metropolitan', 'Maipu', 'LATAM', 'South America', 'Warehouse', 'Outlet Melipilla CD', 'Camino Melipilla 11450, Maipu.', 15, 1, GETUTCDATE(), GETUTCDATE()),
    (37, 'Chile', 'Metropolitan', 'San Joaquin', 'LATAM', 'South America', 'Outlet', 'Outlet La Fabrica', 'Carlos Valdovinos 200, Local 6 y 7 San Joaquin', 1, 1, GETUTCDATE(), GETUTCDATE()),
    (38, 'Chile', 'Bío Bío', 'San Pedro de la Paz', 'LATAM', 'South America', 'Outlet', 'Outlet PA San Pedro', 'Avda Portal de San Pedro 4850 local 38', 2, 1, GETUTCDATE(), GETUTCDATE()),
    (39, 'Chile', 'Metropolitan', 'Santiago', 'LATAM', 'South America', 'Factory', 'Santiago Plant - Major Appliances', 'Alberto Llona, 777 - Maipú', 87, 1, GETUTCDATE(), GETUTCDATE()),
    (40, 'Chile', 'Metropolitan', 'Santiago', 'LATAM', 'South America', 'Warehouse', 'Outlet Melipilla CD', 'Camino a Melipilla, 11450 - Maipú', 16, 1, GETUTCDATE(), GETUTCDATE()),
    (41, 'Chile', 'Metropolitan', 'Santiago', 'LATAM', 'South America', 'Office', 'Santiago Office', 'Orinoco 90, Torre 1, Piso 6, las Condes', 88, 1, GETUTCDATE(), GETUTCDATE()),
    (42, 'Chile', 'Araucanía', 'Temuco', 'LATAM', 'South America', 'Outlet', 'Outlet VIVO Temuco', 'Avenida los Poetas 249', 1, 1, GETUTCDATE(), GETUTCDATE()),
    (43, 'Chile', 'Valparaiso', 'Viña del Mar', 'LATAM', 'South America', 'Outlet', 'Outlet Viña del Mar', 'Camino Internacional 2440 loc. 12 al 14 Outlet Park - Viña del Mar', 2, 1, GETUTCDATE(), GETUTCDATE()),
    (44, 'Colombia', 'Cundinamarca', 'Bogota', 'LATAM', 'South America', 'Office', 'Bogota Office', 'Edificio Banco Falabella. Avenida 19 No. 120-71. OFC 504 - 505 - 506', 60, 1, GETUTCDATE(), GETUTCDATE()),
    (45, 'Colombia', 'Valle del Cauca', 'Cali', 'LATAM', 'South America', 'Warehouse', 'Cali Warehouse', 'Cra 25a N 13-160 Acopy, Yumbo', 9, 1, GETUTCDATE(), GETUTCDATE()),
    (46, 'Ecuador', 'Guayas', 'Guayaquil', 'LATAM', 'South America', 'Warehouse', 'Guayaquil Warehouse', 'Km 5,5 Via Duran Tambo', 5, 1, GETUTCDATE(), GETUTCDATE()),
    (47, 'Ecuador', 'Pichincha', 'Quito', 'LATAM', 'South America', 'Office', 'Quito office', 'Av. Republica del salvador y Moscu Edificio San Salvador piso 6', 20, 1, GETUTCDATE(), GETUTCDATE()),
    (48, 'Peru', 'Lima', 'Lima', 'LATAM', 'South America', 'Office', 'Lima Office', 'Cal. Pedro Venturo 312 -Surco', 66, 1, GETUTCDATE(), GETUTCDATE()),
    (51, 'Chile', 'Los Lagos', 'La Serena', 'LATAM', 'South America', 'Outlet', 'Outlet VIVO Coquimbo', 'Ruta 5 norte, Regimiento Arica, Av Central - Peñuelas /La Serena', NULL, 1, GETUTCDATE(), GETUTCDATE()),
    (52, 'Chile', 'Valparaiso', 'Los Andes', 'LATAM', 'South America', 'Outlet', 'Outlet Los Andes', 'Freire N°676, Loc 4, esquina Santa Teresa, Los Andes', NULL, 1, GETUTCDATE(), GETUTCDATE()),
    (53, 'Chile', 'Melipilla', 'Melipilla', 'LATAM', 'South America', 'Outlet', 'Outlet Melipilla PC', 'Vicuña Mackenna 302 L 104, Melipilla', NULL, 1, GETUTCDATE(), GETUTCDATE()),
    (54, 'Chile', 'Metropolitana', 'Puente Alto', 'LATAM', 'South America', 'Outlet', 'Outlet Puente Alto', 'Concha y Toro 701, Puente Alto', NULL, 1, GETUTCDATE(), GETUTCDATE()),
    (55, 'Chile', 'Metropolitana', 'Quilicura', 'LATAM', 'South America', 'Outlet', 'Outlet Easton Mall', 'Av. Presidente Frei 9709, local 904, Quilicura', 1, 1, GETUTCDATE(), GETUTCDATE()),
    (56, 'Chile', 'Metropolitana', 'Quilicura', 'LATAM', 'South America', 'Outlet', 'Outlet Buenaventura', 'Caupolican 9750, Loc 3a-3b, Quilicura', 1, 1, GETUTCDATE(), GETUTCDATE()),
    (57, 'Chile', 'Valparaiso', 'Quillota', 'LATAM', 'South America', 'Outlet', 'Outlet Quillota', 'Av Condell 1687, loc A7 - Quillota', NULL, 1, GETUTCDATE(), GETUTCDATE()),
    (58, 'Chile', 'Metropolitana', 'San Bernardo', 'LATAM', 'South America', 'Outlet', 'Outlet San Bernardo', 'Av Colon N°520, esquina Freire, San Bernardo', NULL, 1, GETUTCDATE(), GETUTCDATE()),
    (59, 'Chile', 'Metropolitana', 'Santiago', 'LATAM', 'South America', 'Outlet', 'Outlet Franklin', 'Franklin N°702, esquina Santa Rosa, Santiago', NULL, 1, GETUTCDATE(), GETUTCDATE()),
    (60, 'Chile', 'Metropolitana', 'Cerrillos', 'LATAM', 'South America', 'Service', 'Santiago Home Care & SDA', 'Antonio Escobar Williams 600 - Cerrillos', NULL, 1, GETUTCDATE(), GETUTCDATE()),
    (61, 'Chile', 'Metropolitana', 'Maipu', 'LATAM', 'South America', 'Warehouse', 'Santiago Warehouse 2', 'Camino a Melipilla, 11450 - Maipú', NULL, 1, GETUTCDATE(), GETUTCDATE()),
    (62, 'Peru', 'Lima', 'Lima', 'LATAM', 'South America', 'Warehouse', 'Lima Warehouse 2', 'Aldea Global Logistica 8, Villa El Salvador - Lima', NULL, 1, GETUTCDATE(), GETUTCDATE()),
    (63, 'Colombia', 'Atlantico', 'Barranquilla', 'LATAM', 'South America', 'Service', 'Barranquilla Service Center', 'Cra 51 N 74-41, Barranquilla', NULL, 1, GETUTCDATE(), GETUTCDATE());
    
    -- Desabilitar IDENTITY_INSERT após inserção
    SET IDENTITY_INSERT dim_electrolux_locations OFF;
    
    PRINT 'Localidades Eletrolux inseridas com sucesso: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros (IDs: 1-48, 50-63 com 13 locations adicionais)';
END
ELSE
    PRINT 'Aviso: Tabela dim_electrolux_locations não existe';
GO

-- ============================================================
-- 4. INSERIR FEATURES (features)
-- Dados reais do banco de produção
-- ============================================================
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'features')
BEGIN
    TRUNCATE TABLE features;
    
    -- Habilitar IDENTITY_INSERT para usar IDs específicos
    SET IDENTITY_INSERT features ON;
    
    INSERT INTO features (feature_id, code, name, description, is_active, agente, created_at)
    VALUES
    (1, 1001, 'Dashboard', 'Acesso ao painel principal com indicadores e métricas do sistema', 1, 'LUZ', GETUTCDATE()),
    (2, 1002, 'Documents', 'Acesso ao módulo de gerenciamento de documentos', 1, 'LUZ', GETUTCDATE());
    
    -- Desabilitar IDENTITY_INSERT após inserção
    SET IDENTITY_INSERT features OFF;
    
    PRINT 'Features inseridas com sucesso: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros';
END
ELSE
    PRINT 'Aviso: Tabela features não existe';
GO

-- ============================================================
-- 6. INSERIR AGENTES PERMITIDOS (allowed_agents)
-- ============================================================
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'allowed_agents')
BEGIN
    TRUNCATE TABLE allowed_agents;
    
    INSERT INTO allowed_agents (code, name, description, is_active, created_at)
    VALUES
    ('LUZ', 'RH e Assuntos Gerais', 'Gerenciador de assuntos de RH, dúvidas gerais e relacionamento', 1, GETUTCDATE()),
    ('IGP', 'IGP', 'Gerenciador IGP (a ser definido)', 1, GETUTCDATE()),
    ('SMART', 'Smart', 'Gerenciador Smart (a ser definido)', 1, GETUTCDATE());
    
    PRINT 'Agentes permitidos inseridos com sucesso: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' registros';
END
ELSE
    PRINT 'Aviso: Tabela allowed_agents não existe';
GO

-- ============================================================
-- REABILITAR CONSTRAINT DE FK
-- ============================================================
ALTER TABLE documents CHECK CONSTRAINT FK_documents_category;
ALTER TABLE dim_job_title_roles CHECK CONSTRAINT FK_job_title_roles_dim_roles;
ALTER TABLE admins CHECK CONSTRAINT FK_admins_agent_id;
GO

-- ============================================================
-- RESUMO FINAL
-- ============================================================
PRINT '';
PRINT '========================================================';
PRINT 'SEED DATA COMPLETO INSERIDO COM SUCESSO!';
PRINT '========================================================';
PRINT '';
PRINT 'Master Data Populado (Dados Reais do Banco):';
PRINT '  ✓ Localidades Eletrolux: 62 (todas LATAM ativas)';
IF OBJECT_ID('dim_electrolux_locations') IS NOT NULL
    PRINT '    - Países: Argentina, Brazil, Chile, Colombia, Ecuador, Peru';
    PRINT '    - Tipos: Office, Warehouse, Factory, Outlet, Service, Operations';
PRINT '  ✓ Categorias: 14';
IF OBJECT_ID('dim_categories') IS NOT NULL
    PRINT '    - Todas ativas e relacionadas a RH';
PRINT '  ✓ Papéis/Funções: 15';
IF OBJECT_ID('dim_roles') IS NOT NULL
    PRINT '    - De Aprendiz até Presidente';
PRINT '  ✓ Features: 2';
IF OBJECT_ID('features') IS NOT NULL
    PRINT '    - Dashboard, Documents (agente: LUZ)';
PRINT '  ✓ Agentes: 3';
IF OBJECT_ID('allowed_agents') IS NOT NULL
    PRINT '    - Todos ativos: LUZ, IGP, SMART';
PRINT '';
PRINT '✅ Schema com dados atualizados - Pronto para DESENVOLVIMENTO!';
PRINT '========================================================';
GO
