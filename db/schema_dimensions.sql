-- ============================================================
-- DIMENSION TABLES FOR MASTER DATA
-- ============================================================

-- Countries
CREATE TABLE dim_countries (
    country_id INT IDENTITY(1,1) PRIMARY KEY,
    country_name VARCHAR(100) NOT NULL UNIQUE,
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);

-- Regions (LATAM, EMEA, NA, APAC)
CREATE TABLE dim_regions (
    region_id INT IDENTITY(1,1) PRIMARY KEY,
    region_name VARCHAR(50) NOT NULL UNIQUE,
    continent VARCHAR(50),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);

-- States/Provinces
CREATE TABLE dim_states (
    state_id INT IDENTITY(1,1) PRIMARY KEY,
    country_id INT NOT NULL,
    state_name VARCHAR(100) NOT NULL,
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (country_id) REFERENCES dim_countries(country_id),
    UNIQUE(country_id, state_name)
);

-- Cities
CREATE TABLE dim_cities (
    city_id INT IDENTITY(1,1) PRIMARY KEY,
    state_id INT NOT NULL,
    country_id INT NOT NULL,
    region_id INT NOT NULL,
    city_name VARCHAR(100) NOT NULL,
    operation_type VARCHAR(50),  -- HQ, Factory, Office, Operations, etc.
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (state_id) REFERENCES dim_states(state_id),
    FOREIGN KEY (country_id) REFERENCES dim_countries(country_id),
    FOREIGN KEY (region_id) REFERENCES dim_regions(region_id),
    UNIQUE(state_id, city_name)
);

-- Job Roles/Levels
CREATE TABLE dim_roles (
    role_id INT IDENTITY(1,1) PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL UNIQUE,
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);

-- Benefit Categories
CREATE TABLE dim_categories (
    category_id INT IDENTITY(1,1) PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    is_active BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);

-- ============================================================
-- SEED DATA
-- ============================================================

-- Insert Regions
INSERT INTO dim_regions (region_name, continent, is_active) VALUES
('LATAM', 'South America', 1),
('NA', 'North America', 1),
('EMEA', 'Europe', 1),
('APAC', 'Asia', 1);

-- Insert Countries
INSERT INTO dim_countries (country_name, is_active) VALUES
('Brazil', 1),
('Argentina', 1),
('Chile', 1),
('Mexico', 1),
('United States', 1),
('Sweden', 1),
('Italy', 1),
('Poland', 1),
('Hungary', 1),
('France', 1),
('Spain', 1),
('United Kingdom', 1),
('China', 1),
('Thailand', 1),
('India', 1),
('Australia', 1);

-- Insert States for Brazil
INSERT INTO dim_states (country_id, state_name, is_active) VALUES
((SELECT country_id FROM dim_countries WHERE country_name = 'Brazil'), 'São Paulo', 1),
((SELECT country_id FROM dim_countries WHERE country_name = 'Brazil'), 'Paraná', 1),
((SELECT country_id FROM dim_countries WHERE country_name = 'Brazil'), 'Amazonas', 1),
((SELECT country_id FROM dim_countries WHERE country_name = 'Brazil'), 'Espírito Santo', 1),
((SELECT country_id FROM dim_countries WHERE country_name = 'Brazil'), 'Santa Catarina', 1),

-- Insert States for Argentina
((SELECT country_id FROM dim_countries WHERE country_name = 'Argentina'), 'Santa Fe', 1),

-- Insert States for Chile
((SELECT country_id FROM dim_countries WHERE country_name = 'Chile'), 'Santiago Metropolitan', 1),

-- Insert States for Mexico
((SELECT country_id FROM dim_countries WHERE country_name = 'Mexico'), 'Chihuahua', 1),
((SELECT country_id FROM dim_countries WHERE country_name = 'Mexico'), 'Tamaulipas', 1),
((SELECT country_id FROM dim_countries WHERE country_name = 'Mexico'), 'Nuevo León', 1),

-- Insert States for United States
((SELECT country_id FROM dim_countries WHERE country_name = 'United States'), 'North Carolina', 1),
((SELECT country_id FROM dim_countries WHERE country_name = 'United States'), 'South Carolina', 1),
((SELECT country_id FROM dim_countries WHERE country_name = 'United States'), 'Tennessee', 1),

-- Insert States for Sweden
((SELECT country_id FROM dim_countries WHERE country_name = 'Sweden'), 'Stockholm County', 1),

-- Insert States for Italy
((SELECT country_id FROM dim_countries WHERE country_name = 'Italy'), 'Friuli-Venezia Giulia', 1),
((SELECT country_id FROM dim_countries WHERE country_name = 'Italy'), 'Emilia-Romagna', 1),

-- Insert States for Poland
((SELECT country_id FROM dim_countries WHERE country_name = 'Poland'), 'Silesian', 1),
((SELECT country_id FROM dim_countries WHERE country_name = 'Poland'), 'Lower Silesian', 1),

-- Insert States for Hungary
((SELECT country_id FROM dim_countries WHERE country_name = 'Hungary'), 'Jász-Nagykun-Szolnok', 1),

-- Insert States for France
((SELECT country_id FROM dim_countries WHERE country_name = 'France'), 'Ardennes', 1),

-- Insert States for Spain
((SELECT country_id FROM dim_countries WHERE country_name = 'Spain'), 'Aragon', 1),

-- Insert States for UK
((SELECT country_id FROM dim_countries WHERE country_name = 'United Kingdom'), 'England', 1),

-- Insert States for China
((SELECT country_id FROM dim_countries WHERE country_name = 'China'), 'Shanghai', 1),
((SELECT country_id FROM dim_countries WHERE country_name = 'China'), 'Hunan', 1),

-- Insert States for Thailand
((SELECT country_id FROM dim_countries WHERE country_name = 'Thailand'), 'Rayong', 1),

-- Insert States for India
((SELECT country_id FROM dim_countries WHERE country_name = 'India'), 'Maharashtra', 1),

-- Insert States for Australia
((SELECT country_id FROM dim_countries WHERE country_name = 'Australia'), 'New South Wales', 1),
((SELECT country_id FROM dim_countries WHERE country_name = 'Australia'), 'South Australia', 1);

-- Insert Cities (with LATAM only active initially)
-- LATAM. Brasil
INSERT INTO dim_cities (state_id, country_id, region_id, city_name, operation_type, is_active) 
SELECT 
    (SELECT state_id FROM dim_states WHERE state_name = 'São Paulo' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Brazil')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Brazil'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'LATAM'),
    'São Paulo', 'HQ', 1
UNION ALL SELECT 
    (SELECT state_id FROM dim_states WHERE state_name = 'Paraná' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Brazil')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Brazil'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'LATAM'),
    'Curitiba', 'Factory', 1
UNION ALL SELECT 
    (SELECT state_id FROM dim_states WHERE state_name = 'Amazonas' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Brazil')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Brazil'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'LATAM'),
    'Manaus', 'Factory', 1
UNION ALL SELECT 
    (SELECT state_id FROM dim_states WHERE state_name = 'São Paulo' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Brazil')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Brazil'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'LATAM'),
    'São Carlos', 'Factory', 1
UNION ALL SELECT 
    (SELECT state_id FROM dim_states WHERE state_name = 'Espírito Santo' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Brazil')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Brazil'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'LATAM'),
    'Linhares', 'Factory', 1
UNION ALL SELECT 
    (SELECT state_id FROM dim_states WHERE state_name = 'Santa Catarina' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Brazil')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Brazil'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'LATAM'),
    'Joinville', 'Operations', 1;

-- LATAM. Argentina
INSERT INTO dim_cities (state_id, country_id, region_id, city_name, operation_type, is_active)
SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Santa Fe' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Argentina')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Argentina'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'LATAM'),
    'Rosario', 'Factory', 1;

-- LATAM. Chile
INSERT INTO dim_cities (state_id, country_id, region_id, city_name, operation_type, is_active)
SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Santiago Metropolitan' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Chile')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Chile'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'LATAM'),
    'Santiago', 'Office', 1;

-- LATAM. Mexico
INSERT INTO dim_cities (state_id, country_id, region_id, city_name, operation_type, is_active)
SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Chihuahua' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Mexico')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Mexico'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'LATAM'),
    'Juárez', 'Factory', 1
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Tamaulipas' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Mexico')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Mexico'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'LATAM'),
    'Ciudad Victoria', 'Factory', 1
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Nuevo León' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Mexico')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Mexico'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'LATAM'),
    'Monterrey', 'Operations', 1;

-- North America (set is_active to 0 as only LATAM should be active)
INSERT INTO dim_cities (state_id, country_id, region_id, city_name, operation_type, is_active)
SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'North Carolina' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'United States')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'United States'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'NA'),
    'Charlotte', 'HQ', 0
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'South Carolina' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'United States')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'United States'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'NA'),
    'Anderson', 'Factory', 0
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Tennessee' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'United States')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'United States'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'NA'),
    'Springfield', 'Factory', 0
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'North Carolina' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'United States')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'United States'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'NA'),
    'Kinston', 'Factory', 0;

-- EMEA (set is_active to 0)
INSERT INTO dim_cities (state_id, country_id, region_id, city_name, operation_type, is_active)
SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Stockholm County' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Sweden')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Sweden'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'EMEA'),
    'Stockholm', 'Global HQ', 0
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Friuli-Venezia Giulia' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Italy')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Italy'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'EMEA'),
    'Pordenone', 'Factory', 0
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Emilia-Romagna' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Italy')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Italy'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'EMEA'),
    'Forlì', 'Factory', 0
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Silesian' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Poland')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Poland'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'EMEA'),
    'Siewierz', 'Factory', 0
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Lower Silesian' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Poland')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Poland'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'EMEA'),
    'Żarów', 'Factory', 0
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Jász-Nagykun-Szolnok' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Hungary')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Hungary'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'EMEA'),
    'Jászberény', 'Factory', 0
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Ardennes' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'France')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'France'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'EMEA'),
    'Revin', 'Factory', 0
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Aragon' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Spain')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Spain'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'EMEA'),
    'Zaragoza', 'Factory', 0
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'England' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'United Kingdom')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'United Kingdom'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'EMEA'),
    'Luton', 'Office', 0;

-- APAC (set is_active to 0)
INSERT INTO dim_cities (state_id, country_id, region_id, city_name, operation_type, is_active)
SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Shanghai' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'China')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'China'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'APAC'),
    'Shanghai', 'Office', 0
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Hunan' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'China')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'China'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'APAC'),
    'Changsha', 'Factory', 0
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Rayong' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Thailand')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Thailand'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'APAC'),
    'Rayong', 'Factory', 0
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'Maharashtra' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'India')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'India'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'APAC'),
    'Pune', 'Office', 0
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'New South Wales' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Australia')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Australia'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'APAC'),
    'Sydney', 'Office', 0
UNION ALL SELECT
    (SELECT state_id FROM dim_states WHERE state_name = 'South Australia' AND country_id = (SELECT country_id FROM dim_countries WHERE country_name = 'Australia')),
    (SELECT country_id FROM dim_countries WHERE country_name = 'Australia'),
    (SELECT region_id FROM dim_regions WHERE region_name = 'APAC'),
    'Adelaide', 'Factory', 0;

-- Insert Roles
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

-- Insert Benefit Categories
INSERT INTO dim_categories (category_name, description, is_active) VALUES
('Admissão', 'Benefícios relacionados ao processo de admissão', 1),
('Folha de Pagamento', 'Benefícios relacionados ao pagamento e remuneração', 1),
('Férias e Ausências', 'Política de férias, licenças e ausências', 1),
('Jornada e Ponto', 'Controle de jornada e pontuação', 1),
('Saúde e Bem-Estar', 'Benefícios de saúde e bem-estar dos colaboradores', 1),
('Desenvolvimento e Carreira', 'Programas de desenvolvimento e progressão profissional', 1),
('Movimentações Internas', 'Transferências e movimentações de colaboradores', 1),
('Políticas e Normas', 'Políticas gerais e normas da empresa', 1),
('Diversidade e Inclusão', 'Programas de diversidade e inclusão', 1),
('Segurança da Informação', 'Políticas de segurança da informação', 1),
('Relações Trabalhistas', 'Assuntos de relações trabalhistas', 1),
('Desligamento', 'Processo de desligamento de colaboradores', 1),
('RH Geral', 'Assuntos gerais de RH', 1);
