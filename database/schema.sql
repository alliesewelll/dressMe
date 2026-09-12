CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE style_profiles (
    profile_id SERIAL PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    color_season VARCHAR(50),
    body_type VARCHAR(50),
    undertone VARCHAR(50),
    preferred_styles TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE clothing_items (
    item_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,

    item_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    subcategory VARCHAR(50),
    brand VARCHAR(100),

    primary_color VARCHAR(50),
    pattern VARCHAR(50),
    material VARCHAR(100),
    item_size VARCHAR(20),
    purchase_price DECIMAL(10, 2),
    times_worn INT DEFAULT 0,
    purchase_date DATE,

    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
