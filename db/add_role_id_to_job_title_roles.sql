-- Migration: Add role_id FK to dim_job_title_roles table
-- Purpose: Link job_title_roles to role_ids for complete user info endpoint

-- Check if column already exists
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'dim_job_title_roles' AND COLUMN_NAME = 'role_id'
)
BEGIN
    -- Add role_id column
    ALTER TABLE dim_job_title_roles
    ADD role_id INT NULL;
    
    PRINT 'Added role_id column to dim_job_title_roles';
END
ELSE
BEGIN
    PRINT 'role_id column already exists in dim_job_title_roles';
END;

-- Check if FK constraint already exists
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS 
    WHERE CONSTRAINT_NAME = 'FK_job_title_roles_roles'
)
BEGIN
    -- Create FK constraint
    ALTER TABLE dim_job_title_roles
    ADD CONSTRAINT FK_job_title_roles_roles 
    FOREIGN KEY (role_id) REFERENCES dim_roles(role_id);
    
    PRINT 'Added FK constraint FK_job_title_roles_roles';
END
ELSE
BEGIN
    PRINT 'FK constraint FK_job_title_roles_roles already exists';
END;

-- Populate role_id by joining role names with dim_roles
UPDATE dim_job_title_roles
SET role_id = dr.role_id
FROM dim_job_title_roles djtr
JOIN dim_roles dr ON djtr.role = dr.role_name
WHERE djtr.role_id IS NULL;

PRINT 'Updated role_id values from dim_roles table';

-- Verification query
SELECT 'Verification - Job Title Roles with Role IDs:' as [Status];
SELECT TOP 10 
    job_title, 
    role, 
    role_id,
    is_active,
    created_at
FROM dim_job_title_roles
ORDER BY created_at DESC;

PRINT 'Migration completed successfully';
