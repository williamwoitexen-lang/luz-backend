CREATE TABLE IF NOT EXISTS documents (
    document_id      VARCHAR PRIMARY KEY,
    title            VARCHAR NOT NULL,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by       VARCHAR,                 -- usuário que criou
    allowed_countries VARCHAR,
    allowed_cities   VARCHAR,
    min_role_level    INTEGER DEFAULT 1,
    collar            VARCHAR,
    plant_code        INTEGER
);

CREATE TABLE IF NOT EXISTS versions (
    version_id      VARCHAR PRIMARY KEY,
    document_id     VARCHAR NOT NULL,
    version_number  INTEGER NOT NULL,
    file_path       VARCHAR,                 -- caminho do arquivo salvo (local ou ADLS)
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id         VARCHAR PRIMARY KEY,
    document_id      VARCHAR NOT NULL,
    version_id       VARCHAR NOT NULL,
    chunk_index      INTEGER NOT NULL,
    content          VARCHAR NOT NULL,
    embedding        BLOB NOT NULL,
    allowed_countries VARCHAR,
    allowed_cities    VARCHAR,
    min_role_level    INTEGER DEFAULT 1,
    created_by        VARCHAR,
    collar            VARCHAR,
    plant_code        INTEGER
);
