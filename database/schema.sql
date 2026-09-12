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

CREATE TABLE recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    item_id INT NOT NULL,

    recommendation VARCHAR(255) NOT NULL CHECK (recommendation IN ('BUY', 'MAYBE', 'SKIP')),
    confidence_score DECIMAL(5, 4),
    color_score DECIMAL(5, 4),
    body_type_score DECIMAL(5, 4),
    preference_score DECIMAL(5, 4),
    
    recommendation_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_item FOREIGN KEY (item_id) REFERENCES clothing_items(item_id) ON DELETE SET NULL
);

CREATE TABLE feedback (
    feedback_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    recommendation_id INT NOT NULL,

    purchased BOOLEAN,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    times_worn INT DEFAULT 0,
    feedback VARCHAR(255) NOT NULL CHECK (feedback IN ('LIKE', 'DISLIKE', 'NEUTRAL')),
    comments TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_recommendation FOREIGN KEY (recommendation_id) REFERENCES recommendations(recommendation_id) ON DELETE CASCADE
);

SELECT primary_color, AVG(f.rating) AS average_rating, COUNT(*) AS item_count
FROM clothing_items c 
JOIN recommendations r ON c.item_id = r.item_id
JOIN feedback f ON r.recommendation_id = f.recommendation_id
WHERE f.rating IS NOT NULL
GROUP BY primary_color
ORDER BY average_rating DESC;