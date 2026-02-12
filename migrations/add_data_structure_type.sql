ALTER TABLE coding_challenges
ADD COLUMN data_structure_type VARCHAR(50);

CREATE INDEX idx_challenges_data_structure_type ON coding_challenges(data_structure_type);
