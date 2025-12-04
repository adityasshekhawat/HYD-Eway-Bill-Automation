-- Complete Supabase Database Setup for DC Sequences
-- Run this entire script in Supabase SQL Editor

-- Step 1: Create the table
CREATE TABLE IF NOT EXISTS dc_sequences (
    prefix TEXT PRIMARY KEY,
    current_number BIGINT DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- Step 2: Disable Row Level Security for this table
-- This allows the service to read/write sequences without authentication
ALTER TABLE dc_sequences DISABLE ROW LEVEL SECURITY;

-- Step 3: Drop existing function if it exists
DROP FUNCTION IF EXISTS increment_sequence(text);

-- Step 4: Create the increment function
CREATE OR REPLACE FUNCTION increment_sequence(seq_prefix TEXT)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    next_seq BIGINT;
BEGIN
    INSERT INTO dc_sequences (prefix, current_number, last_updated)
    VALUES (seq_prefix, 1, NOW())
    ON CONFLICT (prefix) 
    DO UPDATE SET 
        current_number = dc_sequences.current_number + 1,
        last_updated = NOW()
    RETURNING current_number INTO next_seq;
    
    RETURN next_seq;
END;
$$;

-- Step 5: Insert initial sequences starting from 350
INSERT INTO dc_sequences (prefix, current_number) VALUES
('AKDCAH', 350),
('AKDCSG', 350),
('BDDCAH', 350),
('BDDCSG', 350),
('SBDCAH', 350),
('SBDCSG', 350)
ON CONFLICT (prefix) DO NOTHING;

-- Step 6: Verify the setup
SELECT 'Setup Complete!' as status;
SELECT * FROM dc_sequences ORDER BY prefix; 