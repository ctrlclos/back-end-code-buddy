-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS submissions CASCADE;
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
  is_curated BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_challenges_author ON coding_challenges(author);
CREATE INDEX idx_challenges_difficulty ON coding_challenges(difficulty);
CREATE INDEX idx_challenges_data_structure_type ON coding_challenges(data_structure_type);

-- Create submissions table
CREATE TABLE submissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    challenge_id INTEGER NOT NULL REFERENCES coding_challenges(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    language VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'submitted',
    notes TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for submissions
CREATE INDEX idx_submissions_user_id ON submissions(user_id);
CREATE INDEX idx_submissions_challenge_id ON submissions(challenge_id);
CREATE INDEX idx_submissions_user_challenge ON submissions(user_id, challenge_id);
