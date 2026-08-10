-- Skill Finder schema for MySQL 8.0
-- Execute this file manually against an empty database.
-- The application never creates or alters tables automatically.

SET NAMES utf8mb4;
SET time_zone = '+00:00';

CREATE TABLE repositories (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  github_id BIGINT UNSIGNED NOT NULL,
  owner VARCHAR(100) NOT NULL,
  name VARCHAR(100) NOT NULL,
  full_name VARCHAR(201) NOT NULL,
  html_url VARCHAR(512) NOT NULL,
  homepage VARCHAR(512) NULL,
  description TEXT NULL,
  language VARCHAR(100) NULL,
  topics JSON NOT NULL,
  categories JSON NOT NULL,
  matched_rules JSON NOT NULL,
  stars_count INT UNSIGNED NOT NULL DEFAULT 0,
  forks_count INT UNSIGNED NOT NULL DEFAULT 0,
  open_issues_count INT UNSIGNED NOT NULL DEFAULT 0,
  archived BOOLEAN NOT NULL DEFAULT FALSE,
  disabled BOOLEAN NOT NULL DEFAULT FALSE,
  available BOOLEAN NOT NULL DEFAULT TRUE,
  github_created_at DATETIME(6) NOT NULL,
  github_updated_at DATETIME(6) NOT NULL,
  last_synced_at DATETIME(6) NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uk_repositories_github_id (github_id),
  UNIQUE KEY uk_repositories_full_name (full_name),
  KEY idx_repositories_stars (stars_count),
  KEY idx_repositories_language (language),
  KEY idx_repositories_available_synced (available, last_synced_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE star_snapshots (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  repository_id BIGINT UNSIGNED NOT NULL,
  snapshot_date DATE NOT NULL,
  stars_count INT UNSIGNED NOT NULL DEFAULT 0,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uk_star_snapshots_repository_date (repository_id, snapshot_date),
  KEY idx_star_snapshots_date (snapshot_date),
  CONSTRAINT fk_star_snapshots_repository
    FOREIGN KEY (repository_id) REFERENCES repositories (id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE collection_runs (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  status VARCHAR(32) NOT NULL,
  trigger_type VARCHAR(32) NOT NULL,
  started_at DATETIME(6) NOT NULL,
  finished_at DATETIME(6) NULL,
  query_count INT UNSIGNED NOT NULL DEFAULT 0,
  discovered_count INT UNSIGNED NOT NULL DEFAULT 0,
  updated_count INT UNSIGNED NOT NULL DEFAULT 0,
  failed_count INT UNSIGNED NOT NULL DEFAULT 0,
  rate_limit_remaining INT NULL,
  rate_limit_reset_at DATETIME(6) NULL,
  error_summary TEXT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY idx_collection_runs_started (started_at),
  KEY idx_collection_runs_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
