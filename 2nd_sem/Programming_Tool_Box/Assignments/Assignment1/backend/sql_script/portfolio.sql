
CREATE TABLE IF NOT EXISTS person (
    person_id BIGSERIAL PRIMARY KEY,
    full_name VARCHAR(200) NOT NULL,
    role VARCHAR(255),
    date_of_birth DATE,
    location VARCHAR(255),
    summary TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS person_highlight (
    highlight_id BIGSERIAL PRIMARY KEY,
    person_id BIGINT NOT NULL REFERENCES person(person_id) ON DELETE CASCADE,
    highlight_text TEXT NOT NULL,
    sort_order INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS education (
    education_id BIGSERIAL PRIMARY KEY,
    person_id BIGINT NOT NULL REFERENCES person(person_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    organization VARCHAR(255) NOT NULL,
    period VARCHAR(100) NOT NULL,
    details TEXT,
    sort_order INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS experience (
    experience_id BIGSERIAL PRIMARY KEY,
    person_id BIGINT NOT NULL REFERENCES person(person_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    organization VARCHAR(255) NOT NULL,
    period VARCHAR(100) NOT NULL,
    details TEXT,
    sort_order INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS hobby (
    hobby_id BIGSERIAL PRIMARY KEY,
    person_id BIGINT NOT NULL REFERENCES person(person_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    sort_order INT NOT NULL DEFAULT 0
);


-- Insert data 

INSERT INTO person (
    full_name,
    role,
    date_of_birth,
    location,
    summary
)
VALUES (
    'Raicu Maria',
    'Machine Learning Engineer & Data Science Student',
    TO_DATE('0x-0x-2003', 'DD-MM-YYYY'),
    'Cluj-Napoca, Romania',
    ''
);

INSERT INTO person_highlight (person_id, highlight_text, sort_order)
VALUES
    ((SELECT person_id FROM person WHERE full_name = 'Raicu Maria' ORDER BY person_id DESC LIMIT 1), 'Lives in Cluj-Napoca', 1),
    ((SELECT person_id FROM person WHERE full_name = 'Raicu Maria' ORDER BY person_id DESC LIMIT 1), 'Interested in Data Science', 2),
    ((SELECT person_id FROM person WHERE full_name = 'Raicu Maria' ORDER BY person_id DESC LIMIT 1), 'Enjoys long runs', 3);

INSERT INTO education (person_id, title, organization, period, details, sort_order)
VALUES
    (
        (SELECT person_id FROM person WHERE full_name = 'Raicu Maria' ORDER BY person_id DESC LIMIT 1),
        'MSc in Data Science',
        'Babes Bolyai University',
        '2025 - present',
        'Specializing in data science to deepen my understanding of machine learning and AI.',
        1
    ),
    (
        (SELECT person_id FROM person WHERE full_name = 'Raicu Maria' ORDER BY person_id DESC LIMIT 1),
        'BSc in Computer Science',
        'Babes Bolyai University',
        '2022 - 2025',
        'Starting to build a strong foundation in computer science.',
        2
    );

INSERT INTO experience (person_id, title, organization, period, details, sort_order)
VALUES
    (
        (SELECT person_id FROM person WHERE full_name = 'Raicu Maria' ORDER BY person_id DESC LIMIT 1),
        'Machine Learning Engineer',
        'Lateral',
        'Sept 2025 - present',
        'Working on advanced solutions in Ai on real world problems.',
        1
    ),
    (
        (SELECT person_id FROM person WHERE full_name = 'Raicu Maria' ORDER BY person_id DESC LIMIT 1),
        'Machine Learning Developer Intern',
        'Lateral',
        'July 2025 - Sept 2025',
        'Worked on advanced AI solutions through trainings on multimodal AI, Retrieval-Augmented Generation (RAG), and deployment techniques using AWS and Docker.',
        2
    );

INSERT INTO hobby (person_id, title, description, sort_order)
VALUES
    (
        (SELECT person_id FROM person WHERE full_name = 'Raicu Maria' ORDER BY person_id DESC LIMIT 1),
        'Running',
        'Exploring neighborhoods for new perspectives.',
        1
    ),
    (
        (SELECT person_id FROM person WHERE full_name = 'Raicu Maria' ORDER BY person_id DESC LIMIT 1),
        'Tennis',
        'Practicing tennis every week.',
        2
    ),
    (
        (SELECT person_id FROM person WHERE full_name = 'Raicu Maria' ORDER BY person_id DESC LIMIT 1),
        'Painting',
        'Another passion that keeps me creative and relaxed.',
        3
    );
