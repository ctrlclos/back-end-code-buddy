-- Add function metadata columns for  code-challenge-style execution
-- function_name being NULL means the challenge uses stdin/stdout mode (backward compat)
ALTER TABLE coding_challenges ADD COLUMN IF NOT EXISTS function_name VARCHAR(100);
ALTER TABLE coding_challenges ADD COLUMN IF NOT EXISTS function_params JSONB DEFAULT '[]';
ALTER TABLE coding_challenges ADD COLUMN IF NOT EXISTS return_type VARCHAR(50) DEFAULT 'string';
