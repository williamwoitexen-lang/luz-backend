-- Migration: Add "Unmapped" role and update job_title_roles

-- Disable the foreign key constraint temporarily
ALTER TABLE dim_job_title_roles NOCHECK CONSTRAINT FK_job_title_roles_dim_roles;

PRINT 'Disabled FK constraint';

-- First update dim_job_title_roles: change role_id from 24 to 99
UPDATE dim_job_title_roles 
SET role_id = 99 
WHERE role_id = 24;

PRINT 'Updated dim_job_title_roles: role_id 24 -> 99';

-- Then delete the old role entry from dim_roles
DELETE FROM dim_roles 
WHERE role_id = 24;

PRINT 'Deleted old role_id 24 from dim_roles';

-- Re-enable the foreign key constraint
ALTER TABLE dim_job_title_roles CHECK CONSTRAINT FK_job_title_roles_dim_roles;

PRINT 'Re-enabled FK constraint';

-- Verification
SELECT 'Updated dim_roles:' as [Status];
SELECT role_id, role_name FROM dim_roles WHERE role_id = 99;

SELECT 'Updated dim_job_title_roles:' as [Status];
SELECT TOP 10 job_title, role, role_id FROM dim_job_title_roles WHERE role = 'Unmapped';
