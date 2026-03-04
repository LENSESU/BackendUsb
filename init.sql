-- =========================================
-- BASE TABLES CREATION
-- =========================================

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200)
);

-- =========================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_user_role
        FOREIGN KEY (role_id)
        REFERENCES roles(id)
        ON DELETE RESTRICT
);

-- =========================================

CREATE TABLE incident_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(200)
);

-- =========================================

CREATE TABLE files (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    uploaded_by_user_id INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_file_user
        FOREIGN KEY (uploaded_by_user_id)
        REFERENCES users(id)
        ON DELETE SET NULL
);

-- =========================================

CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL,
    technician_id INTEGER,
    category_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    campus_place VARCHAR(200),
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    status VARCHAR(20) NOT NULL DEFAULT 'New',
    priority VARCHAR(20),
    before_photo_id INTEGER NOT NULL,
    after_photo_id INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,

    CONSTRAINT fk_incident_student
        FOREIGN KEY (student_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_incident_technician
        FOREIGN KEY (technician_id)
        REFERENCES users(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_incident_category
        FOREIGN KEY (category_id)
        REFERENCES incident_categories(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_incident_before_photo
        FOREIGN KEY (before_photo_id)
        REFERENCES files(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_incident_after_photo
        FOREIGN KEY (after_photo_id)
        REFERENCES files(id)
        ON DELETE SET NULL
);

-- =========================================

CREATE TABLE suggestions (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    photo_id INTEGER,
    total_votes INTEGER NOT NULL DEFAULT 0,
    institutional_comment TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_suggestion_student
        FOREIGN KEY (student_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_suggestion_photo
        FOREIGN KEY (foto_id)
        REFERENCES files(id)
        ON DELETE SET NULL
);

-- =========================================

CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE
);

-- =========================================

CREATE TABLE suggestion_tags (
    suggestion_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,

    PRIMARY KEY (suggestion_id, tag_id),

    CONSTRAINT fk_suggestion_tag_suggestion
        FOREIGN KEY (suggestion_id)
        REFERENCES suggestions(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_suggestion_tag_tag
        FOREIGN KEY (tag_id)
        REFERENCES tags(id)
        ON DELETE CASCADE
);

-- =========================================

CREATE TABLE votes (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL,
    suggestion_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_vote_student
        FOREIGN KEY (student_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_vote_suggestion
        FOREIGN KEY (suggestion_id)
        REFERENCES suggestions(id)
        ON DELETE CASCADE,

    CONSTRAINT unique_vote_per_student
        UNIQUE (student_id, suggestion_id)
);

-- =========================================

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    incident_id INTEGER NOT NULL,
    message VARCHAR(300) NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_notification_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_notification_incident
        FOREIGN KEY (incident_id)
        REFERENCES incidents(id)
        ON DELETE CASCADE
);