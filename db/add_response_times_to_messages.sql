-- Migration: Add response time tracking to conversation_messages table
-- Purpose: Store retrieval_time, llm_time, total_time from LLM Server responses

-- Check if columns already exist
IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'conversation_messages' AND COLUMN_NAME = 'retrieval_time'
)
BEGIN
    -- Add response time columns
    ALTER TABLE conversation_messages
    ADD retrieval_time FLOAT NULL,  -- Time to retrieve documents (milliseconds)
        llm_time FLOAT NULL,        -- Time LLM took to generate response (milliseconds)
        total_time FLOAT NULL;      -- Total time from question to answer (milliseconds)
    
    PRINT 'Added response time columns to conversation_messages';
END
ELSE
BEGIN
    PRINT 'Response time columns already exist in conversation_messages';
END;

-- Verification query
SELECT 'Verification - conversation_messages columns:' as [Status];
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'conversation_messages' 
ORDER BY ORDINAL_POSITION;
