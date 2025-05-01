CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    host TEXT,
    name TEXT,
    password TEXT,
    url TEXT NOT NULL,
    uri TEXT NOT NULL,
    inbox TEXT NOT NULL,
    shared_inbox TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (username, host)
);



CREATE TABLE IF NOT EXISTS Posts (
    id TEXT PRIMARY KEY NOT NULL,
    user_id INTEGER NOT NULL,
    uri TEXT NOT NULL,
    url TEXT,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id)
);

CREATE TABLE IF NOT EXISTS Followers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    follower_id INTEGER NOT NULL,
    followed_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (follower_id) REFERENCES Users(id),
    FOREIGN KEY (followed_id) REFERENCES Users(id),
    UNIQUE (follower_id, followed_id)
);

CREATE TABLE IF NOT EXISTS Keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    public_key TEXT NOT NULL,
    private_key TEXT,
    key_type TEXT NOT NULL CHECK (key_type IN ('RSASSA-PKCS1-v1_5', 'Ed25519')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id)
);
