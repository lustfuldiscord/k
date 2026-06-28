CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id INTEGER PRIMARY KEY,
    prefix TEXT DEFAULT ',',
    baserole_id INTEGER,
    imuted_id INTEGER,
    disablecustomfms INTEGER DEFAULT 0,
    autonick TEXT,
    googlesafetylevel INTEGER DEFAULT 0,
    dj_id INTEGER,
    modlog_id INTEGER,
    joinlogs_id INTEGER,
    premiumrole_id INTEGER,
    rmuted_id INTEGER,
    jailroles_id INTEGER DEFAULT 0,
    muted_id INTEGER,
    jailrole_id INTEGER,
    autoplay TEXT,
    jail_id INTEGER,
    jailmsg TEXT,
    welcome_channel_id INTEGER DEFAULT NULL,
    autorole_id INTEGER DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS user_prefixes (
    user_id INTEGER PRIMARY KEY,
    prefix TEXT
);

CREATE TABLE IF NOT EXISTS booster_roles (
    guild_id INTEGER,
    user_id INTEGER,
    role_id INTEGER,
    PRIMARY KEY (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS booster_settings (
    guild_id INTEGER PRIMARY KEY,
    role_limit INTEGER DEFAULT 1,
    base_role_id INTEGER,
    share_limit INTEGER DEFAULT 2
);

CREATE TABLE IF NOT EXISTS booster_filters (
    guild_id INTEGER,
    word TEXT,
    PRIMARY KEY (guild_id, word)
);

CREATE TABLE IF NOT EXISTS automation_messages (
    guild_id INTEGER,
    type TEXT, 
    channel_id INTEGER,
    message TEXT,
    PRIMARY KEY (guild_id, type, channel_id)
);

CREATE TABLE IF NOT EXISTS sticky_messages (
    guild_id INTEGER,
    channel_id INTEGER,
    message TEXT,
    last_message_id INTEGER,
    PRIMARY KEY (guild_id, channel_id)
);

CREATE TABLE IF NOT EXISTS imgonly_channels (
    guild_id INTEGER,
    channel_id INTEGER,
    PRIMARY KEY (guild_id, channel_id)
);

CREATE TABLE IF NOT EXISTS aliases (
    guild_id INTEGER,
    shortcut TEXT,
    command TEXT,
    PRIMARY KEY (guild_id, shortcut)
);

-- Join to Create System Settings (Per-Guild Configuration Setup)
CREATE TABLE IF NOT EXISTS voice_settings (
    guild_id INTEGER PRIMARY KEY,
    master_channel_id INTEGER,
    category_id INTEGER
);

-- Active Temporary Voice Rooms Tracking (Handles Multi-Guild Storage Scales Natively)
CREATE TABLE IF NOT EXISTS active_voice_rooms (
    channel_id INTEGER PRIMARY KEY,
    owner_id INTEGER,
    guild_id INTEGER
);

-- Vanity Custom Status Reward Role Subsystem Configuration Mapping Tables
CREATE TABLE IF NOT EXISTS vanity_settings (
    guild_id INTEGER PRIMARY KEY,
    vanity_string TEXT,
    role_id INTEGER
);

-- Server Specific AFK Tracker Storage Setup
CREATE TABLE IF NOT EXISTS guild_afk (
    guild_id INTEGER,
    user_id INTEGER,
    reason TEXT,
    timestamp TEXT,
    PRIMARY KEY (guild_id, user_id)
);

-- Forced Nickname Lock Mapping Configurations
CREATE TABLE IF NOT EXISTS nicklock (
    guild_id INTEGER,
    user_id INTEGER,
    nickname TEXT,
    PRIMARY KEY (guild_id, user_id)
);

-- Automated Honeypot Trap Channel Configurations
CREATE TABLE IF NOT EXISTS honeypots (
    guild_id INTEGER,
    channel_id INTEGER,
    PRIMARY KEY (guild_id, channel_id)
);

ALTER TABLE guild_settings ADD COLUMN autorole_id INTEGER DEFAULT NULL;
