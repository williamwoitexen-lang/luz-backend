-- ============================================================
-- SEED DATA - MASTER DATA ELECTROLUX
-- Apenas LATAM ativo, outros desativados
-- ============================================================

-- ============================================================
-- TABELA DE LOCALIDADES (se não existir)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'dim_electrolux_locations')
BEGIN
    CREATE TABLE dim_electrolux_locations (
        location_id INT IDENTITY(1,1) PRIMARY KEY,
        country_name NVARCHAR(100) NOT NULL,
        state_name NVARCHAR(100) NOT NULL,
        city_name NVARCHAR(100) NOT NULL,
        region NVARCHAR(50) NOT NULL,
        continent NVARCHAR(50) NOT NULL,
        operation_type NVARCHAR(50) NOT NULL,
        is_active BIT DEFAULT 1,
        created_at DATETIME2 DEFAULT GETUTCDATE(),
        updated_at DATETIME2 DEFAULT GETUTCDATE()
    );
    
    CREATE INDEX idx_country_region ON dim_electrolux_locations(country_name, region);
    CREATE INDEX idx_is_active ON dim_electrolux_locations(is_active);
END
GO

-- ============================================================
-- INSERIR LOCALIDADES - LATAM (ativo)
-- ============================================================

-- LATAM. Brasil
IF NOT EXISTS (SELECT 1 FROM dim_electrolux_locations WHERE country_name = 'Brazil' AND city_name = 'São Paulo')
INSERT INTO dim_electrolux_locations (country_name, state_name, city_name, region, continent, operation_type, is_active) VALUES
('Brazil', 'São Paulo', 'São Paulo', 'LATAM', 'South America', 'HQ', 1),
('Brazil', 'Paraná', 'Curitiba', 'LATAM', 'South America', 'Factory', 1),
('Brazil', 'Amazonas', 'Manaus', 'LATAM', 'South America', 'Factory', 1),
('Brazil', 'São Paulo', 'São Carlos', 'LATAM', 'South America', 'Factory', 1),
('Brazil', 'Espírito Santo', 'Linhares', 'LATAM', 'South America', 'Factory', 1),
('Brazil', 'Santa Catarina', 'Joinville', 'LATAM', 'South America', 'Operations', 1);
GO

-- LATAM. Outros Países
IF NOT EXISTS (SELECT 1 FROM dim_electrolux_locations WHERE city_name = 'Rosario')
INSERT INTO dim_electrolux_locations (country_name, state_name, city_name, region, continent, operation_type, is_active) VALUES
('Argentina', 'Santa Fe', 'Rosario', 'LATAM', 'South America', 'Factory', 1),
('Chile', 'Santiago Metropolitan', 'Santiago', 'LATAM', 'South America', 'Office', 1),
('Mexico', 'Chihuahua', 'Juárez', 'LATAM', 'North America', 'Factory', 1),
('Mexico', 'Tamaulipas', 'Ciudad Victoria', 'LATAM', 'North America', 'Factory', 1),
('Mexico', 'Nuevo León', 'Monterrey', 'LATAM', 'North America', 'Operations', 1);
GO

-- ============================================================
-- INSERIR LOCALIDADES - OUTRAS REGIÕES (desativo - is_active = 0)
-- ============================================================

-- North America (DESATIVADO)
IF NOT EXISTS (SELECT 1 FROM dim_electrolux_locations WHERE city_name = 'Charlotte')
INSERT INTO dim_electrolux_locations (country_name, state_name, city_name, region, continent, operation_type, is_active) VALUES
('United States', 'North Carolina', 'Charlotte', 'NA', 'North America', 'HQ', 0),
('United States', 'South Carolina', 'Anderson', 'NA', 'North America', 'Factory', 0),
('United States', 'Tennessee', 'Springfield', 'NA', 'North America', 'Factory', 0),
('United States', 'North Carolina', 'Kinston', 'NA', 'North America', 'Factory', 0);
GO

-- EMEA. Europa (DESATIVADO)
IF NOT EXISTS (SELECT 1 FROM dim_electrolux_locations WHERE city_name = 'Stockholm')
INSERT INTO dim_electrolux_locations (country_name, state_name, city_name, region, continent, operation_type, is_active) VALUES
('Sweden', 'Stockholm County', 'Stockholm', 'EMEA', 'Europe', 'Global HQ', 0),
('Italy', 'Friuli-Venezia Giulia', 'Pordenone', 'EMEA', 'Europe', 'Factory', 0),
('Italy', 'Emilia-Romagna', 'Forlì', 'EMEA', 'Europe', 'Factory', 0),
('Poland', 'Silesian', 'Siewierz', 'EMEA', 'Europe', 'Factory', 0),
('Poland', 'Lower Silesian', 'Żarów', 'EMEA', 'Europe', 'Factory', 0),
('Hungary', 'Jász-Nagykun-Szolnok', 'Jászberény', 'EMEA', 'Europe', 'Factory', 0),
('France', 'Ardennes', 'Revin', 'EMEA', 'Europe', 'Factory', 0),
('Spain', 'Aragon', 'Zaragoza', 'EMEA', 'Europe', 'Factory', 0),
('United Kingdom', 'England', 'Luton', 'EMEA', 'Europe', 'Office', 0);
GO

-- APAC (DESATIVADO)
IF NOT EXISTS (SELECT 1 FROM dim_electrolux_locations WHERE city_name = 'Shanghai')
INSERT INTO dim_electrolux_locations (country_name, state_name, city_name, region, continent, operation_type, is_active) VALUES
('China', 'Shanghai', 'Shanghai', 'APAC', 'Asia', 'Office', 0),
('China', 'Hunan', 'Changsha', 'APAC', 'Asia', 'Factory', 0),
('Thailand', 'Rayong', 'Rayong', 'APAC', 'Asia', 'Factory', 0),
('India', 'Maharashtra', 'Pune', 'APAC', 'Asia', 'Office', 0),
('Australia', 'New South Wales', 'Sydney', 'APAC', 'Oceania', 'Office', 0),
('Australia', 'South Australia', 'Adelaide', 'APAC', 'Oceania', 'Factory', 0);
GO

-- ============================================================
-- CATEGORIAS (Tipos de Benefício/Documento) - Nível de Categorização
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM dim_categories WHERE category_name = 'Benefícios')
BEGIN
    INSERT INTO dim_categories (category_name, description, is_active) VALUES
    ('Benefícios', 'Programas e benefícios oferecidos aos colaboradores', 1),
    ('Admissão', 'Políticas e procedimentos de admissão', 1),
    ('Folha de Pagamento', 'Remuneração, salário e benefícios financeiros', 1),
    ('Férias e Ausências', 'Política de férias, licenças e afastamentos', 1),
    ('Jornada e Ponto', 'Controle de horário e jornada de trabalho', 1),
    ('Saúde e Bem-Estar', 'Benefícios de saúde, plano médico e bem-estar', 1),
    ('Desenvolvimento e Carreira', 'Treinamento e desenvolvimento profissional', 1),
    ('Movimentações Internas', 'Transferências e mudanças de posição', 1),
    ('Políticas e Normas', 'Normas, regras e políticas da empresa', 1),
    ('Diversidade e Inclusão', 'Programas e iniciativas de diversidade', 1),
    ('Segurança da Informação', 'Políticas de segurança de dados e informação', 1),
    ('Relações Trabalhistas', 'Assuntos de relações trabalhistas e sindicatos', 1),
    ('Desligamento', 'Procedimentos de desligamento e rescisão', 1),
    ('RH Geral', 'Outros assuntos e políticas de RH', 1);
END
GO

-- ============================================================
-- ROLES / NÍVEIS DE CARGO - Nível de Cargo
-- ============================================================
IF NOT EXISTS (SELECT 1 FROM dim_roles WHERE role_name = 'Analista')
BEGIN
    INSERT INTO dim_roles (role_name, is_active) VALUES
    ('Analista', 1),
    ('Aprendiz', 1),
    ('Assistente', 1),
    ('Coordenador', 1),
    ('Diretor', 1),
    ('Especialista', 1),
    ('Estagiário', 1),
    ('Gerente', 1),
    ('Gerente Sênior', 1),
    ('Head', 1),
    ('Operacional', 1),
    ('Presidente', 1),
    ('Supervisor', 1),
    ('Técnico', 1),
    ('Vice-Presidente', 1);
END
GO

-- ============================================================
-- RESUMO DOS DADOS CARREGADOS
-- ============================================================
PRINT '';
PRINT '========================================================';
PRINT 'SEED DATA CARREGADO COM SUCESSO!';
PRINT '========================================================';
PRINT '';
PRINT 'Localidades:';
PRINT '  - LATAM (ativo): ' + CAST((SELECT COUNT(*) FROM dim_electrolux_locations WHERE region = 'LATAM' AND is_active = 1) AS VARCHAR);
PRINT '  - Outras regiões (inativo): ' + CAST((SELECT COUNT(*) FROM dim_electrolux_locations WHERE region != 'LATAM' AND is_active = 0) AS VARCHAR);
PRINT '  - Total: ' + CAST((SELECT COUNT(*) FROM dim_electrolux_locations) AS VARCHAR);
PRINT '';
PRINT 'Categorias: ' + CAST((SELECT COUNT(*) FROM dim_categories) AS VARCHAR);
PRINT 'Roles: ' + CAST((SELECT COUNT(*) FROM dim_roles) AS VARCHAR);
PRINT '';
GO
