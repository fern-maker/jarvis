-- Jarvis Memory Database Schema
-- Stores all conversations and metadata for long-term recall

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    web_search_query TEXT,
    web_search_sources TEXT,  -- JSON array of sources
    referenced_past_convos TEXT,  -- JSON array of referenced conversation IDs
    category TEXT,  -- "coding", "debugging", "web_search", "technical_advice", etc.
    tags TEXT,  -- JSON array of tags
    session_id TEXT  -- Group related conversations by session
);

CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    preference_key TEXT UNIQUE NOT NULL,
    preference_value TEXT NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS web_search_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT UNIQUE NOT NULL,
    sources TEXT NOT NULL,  -- JSON array
    retrieved_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast retrieval
CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversations_category ON conversations(category);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_key ON user_preferences(preference_key);
