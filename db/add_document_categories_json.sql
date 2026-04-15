-- Migration: Add document_categories_used column to conversation_messages
-- Purpose: Store JSON with all categories used in each response for dashboard analytics
-- Date: 2026-01-21
-- Status: Ready to execute

USE ca_peoplechatbot_db;

-- Step 1: Add the column to conversation_messages table
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'conversation_messages' 
    AND COLUMN_NAME = 'document_categories_used'
)
BEGIN
    ALTER TABLE conversation_messages
    ADD document_categories_used NVARCHAR(MAX) NULL;
    
    PRINT 'Column document_categories_used added to conversation_messages';
END
ELSE
BEGIN
    PRINT 'Column document_categories_used already exists';
END;

-- Step 2: Create index on role and created_at for faster queries
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes 
    WHERE object_id = OBJECT_ID('conversation_messages') 
    AND name = 'idx_assistant_messages_categories'
)
BEGIN
    CREATE NONCLUSTERED INDEX idx_assistant_messages_categories
    ON conversation_messages(role, created_at)
    WHERE role = 'assistant' AND document_categories_used IS NOT NULL;
    
    PRINT 'Index idx_assistant_messages_categories created';
END
ELSE
BEGIN
    PRINT 'Index idx_assistant_messages_categories already exists';
END;

-- Step 3: Verify the column was created
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    IS_NULLABLE,
    CHARACTER_MAXIMUM_LENGTH
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'conversation_messages'
AND COLUMN_NAME = 'document_categories_used';

PRINT 'Migration complete!';
