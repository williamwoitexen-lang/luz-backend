-- Criar tabela de agentes permitidos
CREATE TABLE allowed_agents (
    agent_id INT PRIMARY KEY IDENTITY(1,1),
    code NVARCHAR(50) NOT NULL UNIQUE,
    name NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX),
    is_active BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE()
);

-- Inserir agentes permitidos
INSERT INTO allowed_agents (code, name, description, is_active)
VALUES 
    ('LUZ', 'RH e Assuntos Gerais', 'Gerenciador de assuntos de RH, dúvidas gerais e relacionamento', 1),
    ('IGP', 'IGP', 'Gerenciador IGP (a ser definido)', 1),
    ('SMART', 'Smart', 'Gerenciador Smart (a ser definido)', 1);

-- Índice para buscas rápidas
CREATE INDEX idx_allowed_agents_code ON allowed_agents(code) WHERE is_active = 1;
