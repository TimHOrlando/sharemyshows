-- Add only the missing MFA fields to users table
-- Your table already has email_verified, so we only need these two

-- Add mfa_code column (stores 6-digit code)
ALTER TABLE users ADD COLUMN mfa_code VARCHAR(6);

-- Add mfa_code_expires column (when code expires)
ALTER TABLE users ADD COLUMN mfa_code_expires DATETIME;

-- Verify columns were added
SELECT sql FROM sqlite_master WHERE type='table' AND name='users';
