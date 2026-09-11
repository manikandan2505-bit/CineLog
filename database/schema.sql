-- ============================================================
-- CineLog Database Schema
-- Version: 1.0
-- Database: MySQL 8.0+
-- ============================================================

CREATE DATABASE IF NOT EXISTS cinelog
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE cinelog;


-- ============================================================
-- 1. USERS
-- ============================================================

CREATE TABLE users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,

    display_name VARCHAR(100),
    bio TEXT,
    avatar_url VARCHAR(500),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);


-- ============================================================
-- 2. MOVIES
-- ============================================================

CREATE TABLE movies (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    tmdb_id INT UNSIGNED NOT NULL UNIQUE,

    title VARCHAR(255) NOT NULL,
    original_title VARCHAR(255),

    overview TEXT,

    release_date DATE,

    runtime SMALLINT UNSIGNED,

    original_language VARCHAR(10),

    poster_path VARCHAR(500),
    backdrop_path VARCHAR(500),

    vote_average DECIMAL(4,2),
    vote_count INT UNSIGNED DEFAULT 0,
    popularity DECIMAL(12,4),

    status VARCHAR(50),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);


-- ============================================================
-- 3. TV SHOWS
-- ============================================================

CREATE TABLE tv_shows (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    tmdb_id INT UNSIGNED NOT NULL UNIQUE,

    name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255),

    overview TEXT,

    first_air_date DATE,
    last_air_date DATE,

    original_language VARCHAR(10),

    poster_path VARCHAR(500),
    backdrop_path VARCHAR(500),

    vote_average DECIMAL(4,2),
    vote_count INT UNSIGNED DEFAULT 0,
    popularity DECIMAL(12,4),

    status VARCHAR(50),

    number_of_seasons SMALLINT UNSIGNED DEFAULT 0,
    number_of_episodes INT UNSIGNED DEFAULT 0,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);


-- ============================================================
-- 4. SEASONS
-- ============================================================

CREATE TABLE seasons (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    tv_show_id BIGINT UNSIGNED NOT NULL,
    tmdb_id INT UNSIGNED NOT NULL UNIQUE,

    season_number SMALLINT UNSIGNED NOT NULL,

    name VARCHAR(255),
    overview TEXT,

    air_date DATE,

    poster_path VARCHAR(500),

    episode_count SMALLINT UNSIGNED DEFAULT 0,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_seasons_tv_show
        FOREIGN KEY (tv_show_id)
        REFERENCES tv_shows(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT uq_season_number
        UNIQUE (tv_show_id, season_number)
);


-- ============================================================
-- 5. EPISODES
-- ============================================================

CREATE TABLE episodes (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    season_id BIGINT UNSIGNED NOT NULL,
    tmdb_id INT UNSIGNED NOT NULL UNIQUE,

    episode_number SMALLINT UNSIGNED NOT NULL,

    name VARCHAR(255) NOT NULL,
    overview TEXT,

    air_date DATE,

    runtime SMALLINT UNSIGNED,

    still_path VARCHAR(500),

    vote_average DECIMAL(4,2),
    vote_count INT UNSIGNED DEFAULT 0,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_episodes_season
        FOREIGN KEY (season_id)
        REFERENCES seasons(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT uq_episode_number
        UNIQUE (season_id, episode_number)
);


-- ============================================================
-- 6. GENRES
-- ============================================================

CREATE TABLE genres (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    name VARCHAR(100) NOT NULL UNIQUE
);


-- ============================================================
-- 7. MOVIE ↔ GENRE
-- ============================================================

CREATE TABLE movie_genres (
    movie_id BIGINT UNSIGNED NOT NULL,
    genre_id INT UNSIGNED NOT NULL,

    PRIMARY KEY (movie_id, genre_id),

    CONSTRAINT fk_movie_genres_movie
        FOREIGN KEY (movie_id)
        REFERENCES movies(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_movie_genres_genre
        FOREIGN KEY (genre_id)
        REFERENCES genres(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ============================================================
-- 8. TV SHOW ↔ GENRE
-- ============================================================

CREATE TABLE tv_show_genres (
    tv_show_id BIGINT UNSIGNED NOT NULL,
    genre_id INT UNSIGNED NOT NULL,

    PRIMARY KEY (tv_show_id, genre_id),

    CONSTRAINT fk_tv_show_genres_show
        FOREIGN KEY (tv_show_id)
        REFERENCES tv_shows(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_tv_show_genres_genre
        FOREIGN KEY (genre_id)
        REFERENCES genres(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ============================================================
-- 9. PEOPLE
-- ============================================================

CREATE TABLE people (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    tmdb_id INT UNSIGNED NOT NULL UNIQUE,

    name VARCHAR(255) NOT NULL,

    profile_path VARCHAR(500),

    known_for_department VARCHAR(100),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);


-- ============================================================
-- 10. MOVIE CREDITS
-- ============================================================

CREATE TABLE movie_credits (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    movie_id BIGINT UNSIGNED NOT NULL,
    person_id BIGINT UNSIGNED NOT NULL,

    credit_type ENUM('cast', 'crew') NOT NULL,

    character_name VARCHAR(255),
    job VARCHAR(255),
    department VARCHAR(100),

    CONSTRAINT fk_movie_credits_movie
        FOREIGN KEY (movie_id)
        REFERENCES movies(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_movie_credits_person
        FOREIGN KEY (person_id)
        REFERENCES people(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ============================================================
-- 11. TV SHOW CREDITS
-- ============================================================

CREATE TABLE tv_show_credits (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    tv_show_id BIGINT UNSIGNED NOT NULL,
    person_id BIGINT UNSIGNED NOT NULL,

    credit_type ENUM('cast', 'crew') NOT NULL,

    character_name VARCHAR(255),
    job VARCHAR(255),
    department VARCHAR(100),

    CONSTRAINT fk_tv_show_credits_show
        FOREIGN KEY (tv_show_id)
        REFERENCES tv_shows(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_tv_show_credits_person
        FOREIGN KEY (person_id)
        REFERENCES people(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ============================================================
-- 12. MOVIE RATINGS
-- ============================================================

CREATE TABLE movie_ratings (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT UNSIGNED NOT NULL,
    movie_id BIGINT UNSIGNED NOT NULL,

    rating DECIMAL(2,1) NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT chk_movie_rating
        CHECK (rating >= 0.5 AND rating <= 5.0),

    CONSTRAINT uq_user_movie_rating
        UNIQUE (user_id, movie_id),

    CONSTRAINT fk_movie_ratings_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_movie_ratings_movie
        FOREIGN KEY (movie_id)
        REFERENCES movies(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ============================================================
-- 13. TV SHOW RATINGS
-- ============================================================

CREATE TABLE show_ratings (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT UNSIGNED NOT NULL,
    tv_show_id BIGINT UNSIGNED NOT NULL,

    rating DECIMAL(2,1) NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT chk_show_rating
        CHECK (rating >= 0.5 AND rating <= 5.0),

    CONSTRAINT uq_user_show_rating
        UNIQUE (user_id, tv_show_id),

    CONSTRAINT fk_show_ratings_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_show_ratings_show
        FOREIGN KEY (tv_show_id)
        REFERENCES tv_shows(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ============================================================
-- 14. EPISODE RATINGS
-- ============================================================

CREATE TABLE episode_ratings (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT UNSIGNED NOT NULL,
    episode_id BIGINT UNSIGNED NOT NULL,

    rating DECIMAL(2,1) NOT NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT chk_episode_rating
        CHECK (rating >= 0.5 AND rating <= 5.0),

    CONSTRAINT uq_user_episode_rating
        UNIQUE (user_id, episode_id),

    CONSTRAINT fk_episode_ratings_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_episode_ratings_episode
        FOREIGN KEY (episode_id)
        REFERENCES episodes(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ============================================================
-- 15. MOVIE REVIEWS
-- ============================================================

CREATE TABLE movie_reviews (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT UNSIGNED NOT NULL,
    movie_id BIGINT UNSIGNED NOT NULL,

    review_text TEXT NOT NULL,

    contains_spoilers BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_movie_reviews_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_movie_reviews_movie
        FOREIGN KEY (movie_id)
        REFERENCES movies(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ============================================================
-- 16. TV SHOW REVIEWS
-- ============================================================

CREATE TABLE show_reviews (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT UNSIGNED NOT NULL,
    tv_show_id BIGINT UNSIGNED NOT NULL,

    review_text TEXT NOT NULL,

    contains_spoilers BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_show_reviews_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_show_reviews_show
        FOREIGN KEY (tv_show_id)
        REFERENCES tv_shows(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ============================================================
-- 17. EPISODE REVIEWS
-- ============================================================

CREATE TABLE episode_reviews (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT UNSIGNED NOT NULL,
    episode_id BIGINT UNSIGNED NOT NULL,

    review_text TEXT NOT NULL,

    contains_spoilers BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_episode_reviews_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_episode_reviews_episode
        FOREIGN KEY (episode_id)
        REFERENCES episodes(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ============================================================
-- 18. MOVIE WATCH HISTORY
-- ============================================================

CREATE TABLE movie_watches (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT UNSIGNED NOT NULL,
    movie_id BIGINT UNSIGNED NOT NULL,

    watched_at DATETIME NOT NULL,

    rewatch BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_movie_watches_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_movie_watches_movie
        FOREIGN KEY (movie_id)
        REFERENCES movies(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ============================================================
-- 19. EPISODE WATCH HISTORY
-- ============================================================

CREATE TABLE episode_watches (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT UNSIGNED NOT NULL,
    episode_id BIGINT UNSIGNED NOT NULL,

    watched_at DATETIME NOT NULL,

    rewatch BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_episode_watches_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_episode_watches_episode
        FOREIGN KEY (episode_id)
        REFERENCES episodes(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ============================================================
-- 20. DIARY ENTRIES
-- ============================================================

CREATE TABLE diary_entries (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT UNSIGNED NOT NULL,

    movie_id BIGINT UNSIGNED NULL,
    episode_id BIGINT UNSIGNED NULL,

    watched_at DATETIME NOT NULL,

    notes TEXT,

    rewatch BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,



    CONSTRAINT fk_diary_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_diary_movie
        FOREIGN KEY (movie_id)
        REFERENCES movies(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_diary_episode
        FOREIGN KEY (episode_id)
        REFERENCES episodes(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ============================================================
-- 21. WATCHLIST
-- ============================================================

CREATE TABLE watchlist_items (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT UNSIGNED NOT NULL,

    movie_id BIGINT UNSIGNED NULL,
    tv_show_id BIGINT UNSIGNED NULL,

    added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,



    CONSTRAINT fk_watchlist_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_watchlist_movie
        FOREIGN KEY (movie_id)
        REFERENCES movies(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_watchlist_show
        FOREIGN KEY (tv_show_id)
        REFERENCES tv_shows(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ============================================================
-- 22. CUSTOM LISTS
-- ============================================================

CREATE TABLE lists (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT UNSIGNED NOT NULL,

    name VARCHAR(150) NOT NULL,
    description TEXT,

    is_public BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_lists_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ============================================================
-- 23. LIST ITEMS
-- ============================================================

CREATE TABLE list_items (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    list_id BIGINT UNSIGNED NOT NULL,

    movie_id BIGINT UNSIGNED NULL,
    tv_show_id BIGINT UNSIGNED NULL,

    position INT UNSIGNED,

    added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,



    CONSTRAINT fk_list_items_list
        FOREIGN KEY (list_id)
        REFERENCES lists(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_list_items_movie
        FOREIGN KEY (movie_id)
        REFERENCES movies(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_list_items_show
        FOREIGN KEY (tv_show_id)
        REFERENCES tv_shows(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ============================================================
-- 24. FAVORITES
-- ============================================================

CREATE TABLE favorites (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    user_id BIGINT UNSIGNED NOT NULL,

    movie_id BIGINT UNSIGNED NULL,
    tv_show_id BIGINT UNSIGNED NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,



    CONSTRAINT fk_favorites_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_favorites_movie
        FOREIGN KEY (movie_id)
        REFERENCES movies(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_favorites_show
        FOREIGN KEY (tv_show_id)
        REFERENCES tv_shows(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);


-- ============================================================
-- END OF SCHEMA
-- ============================================================