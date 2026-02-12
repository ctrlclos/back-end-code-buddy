-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS coding_challenges CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create coding challenges table
CREATE TABLE coding_challenges(
  id SERIAL PRIMARY KEY,
  author INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  difficulty VARCHAR(50) NOT NULL,
  data_structure_type VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_challenges_author ON coding_challenges(author);
CREATE INDEX idx_challenges_difficulty ON coding_challenges(difficulty);
CREATE INDEX idx_challenges_data_structure_type ON coding_challenges(data_structure_type);

-- Optional: Insert test data
-- Uncomment below to create test users and data

-- INSERT INTO users (username, password) VALUES
-- ('testuser1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS6c9rK8e'), -- password: test123
-- ('testuser2', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS6c9rK8e'); -- password: test123
