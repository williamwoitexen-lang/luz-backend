-- Migration: Add address and location_name columns to documents table
-- When location_id is provided, these are auto-filled from dim_electrolux_locations

ALTER TABLE documents
ADD address NVARCHAR(500) NULL,
    location_name NVARCHAR(255) NULL;

-- Create index for location_name filtering
CREATE INDEX idx_location_name ON documents(location_name);

-- Log migration
PRINT 'Migration completed: Added address and location_name columns to documents table';
