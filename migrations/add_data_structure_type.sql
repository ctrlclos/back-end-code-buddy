ALTER TABLE coding_challenges
ADD COLUMN IF NOT EXISTS data_structure_type VARCHAR(50);

CREATE INDEX IF NOT EXISTS idx_challenges_data_structure_type ON coding_challenges(data_structure_type);
