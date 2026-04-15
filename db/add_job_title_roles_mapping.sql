-- Criar tabela de mapeamento JobTitle → Role
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'dim_job_title_roles')
BEGIN
    CREATE TABLE dim_job_title_roles (
        job_title_role_id INT IDENTITY(1,1) PRIMARY KEY,
        job_title NVARCHAR(255) NOT NULL UNIQUE,
        role NVARCHAR(100) NOT NULL,
        is_active BIT DEFAULT 1,
        created_at DATETIME2 DEFAULT GETUTCDATE(),
        updated_at DATETIME2 DEFAULT GETUTCDATE(),
        INDEX idx_job_title (job_title),
        INDEX idx_role (role)
    );
    
    PRINT 'Tabela dim_job_title_roles criada com sucesso';
END
ELSE
BEGIN
    PRINT 'Tabela dim_job_title_roles já existe';
END
GO

-- Inserir dados
IF NOT EXISTS (SELECT 1 FROM dim_job_title_roles WHERE job_title = 'SVP Corporate Communications')
BEGIN
    INSERT INTO dim_job_title_roles (job_title, role, is_active) VALUES
    ('SVP Corporate Communications', 'Vice-Presidente', 1),
    ('SVP Global Product Line Care', 'Vice-Presidente', 1),
    ('SVP, Global Retail Sales', 'Vice-Presidente', 1),
    ('SVP, Marketing & CDI', 'Vice-Presidente', 1),
    ('SVP, Sales BA North America', 'Vice-Presidente', 1),
    ('VP & General Counsel', 'Vice-Presidente', 1),
    ('VP Brand & Consumer Insights', 'Vice-Presidente', 1);
    
    PRINT 'Dados inseridos com sucesso';
END
ELSE
BEGIN
    PRINT 'Dados já existem na tabela';
END
GO

-- Verificar
SELECT job_title, role FROM dim_job_title_roles ORDER BY job_title;
