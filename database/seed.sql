TRUNCATE TABLE feedback, recommendations, clothing_items, style_profiles, users
RESTART IDENTITY CASCADE;

INSERT INTO users (username, email, password_hash) VALUES
	('maya_style', 'maya@example.com', '$2b$12$fakehashmaya0000000000000000000000000000000000000000'),
	('jordan_wardrobe', 'jordan@example.com', '$2b$12$fakehashjordan00000000000000000000000000000000000000'),
	('alex_threads', 'alex@example.com', '$2b$12$fakehashalex0000000000000000000000000000000000000000'),
	('sam_dressed', 'sam@example.com', '$2b$12$fakehashsam00000000000000000000000000000000000000000');

INSERT INTO style_profiles (user_id, color_season, body_type, undertone, preferred_styles)
SELECT user_id, profile.color_season, profile.body_type, profile.undertone, profile.preferred_styles
FROM users
JOIN (VALUES
	('maya_style', 'Autumn', 'Hourglass', 'Warm', 'Classic, relaxed, earth tones'),
	('jordan_wardrobe', 'Winter', 'Rectangle', 'Cool', 'Minimal, streetwear, monochrome'),
	('alex_threads', 'Spring', 'Athletic', 'Warm', 'Preppy, colorful, smart casual'),
	('sam_dressed', 'Summer', 'Pear', 'Cool', 'Romantic, vintage, soft neutrals')
) AS profile(username, color_season, body_type, undertone, preferred_styles)
	ON users.username = profile.username;

INSERT INTO clothing_items (
	user_id, item_name, category, subcategory, brand, primary_color, pattern,
	material, item_size, purchase_price, times_worn, purchase_date, image_url
)
SELECT users.user_id, item.item_name, item.category, item.subcategory, item.brand,
	   item.primary_color, item.pattern, item.material, item.item_size,
	   item.purchase_price, item.times_worn, item.purchase_date, item.image_url
FROM users
JOIN (VALUES
	('maya_style', 'Camel wool coat', 'Outerwear', 'Coat', 'Everlane', 'Camel', 'Solid', 'Wool', 'M', 185.00, 18, DATE '2025-10-12', 'https://example.com/images/camel-wool-coat.jpg'),
	('maya_style', 'Ivory silk blouse', 'Tops', 'Blouse', 'Quince', 'Ivory', 'Solid', 'Silk', 'M', 59.90, 12, DATE '2025-08-20', 'https://example.com/images/ivory-silk-blouse.jpg'),
	('maya_style', 'Dark straight-leg jeans', 'Bottoms', 'Jeans', 'Madewell', 'Indigo', 'Solid', 'Denim', '29', 98.00, 27, DATE '2025-03-15', 'https://example.com/images/dark-jeans.jpg'),
	('jordan_wardrobe', 'Black utility jacket', 'Outerwear', 'Jacket', 'Uniqlo', 'Black', 'Solid', 'Cotton', 'L', 79.90, 22, DATE '2025-09-03', 'https://example.com/images/black-utility-jacket.jpg'),
	('jordan_wardrobe', 'White heavyweight tee', 'Tops', 'T-Shirt', 'COS', 'White', 'Solid', 'Cotton', 'L', 45.00, 31, DATE '2025-02-11', 'https://example.com/images/white-heavyweight-tee.jpg'),
	('jordan_wardrobe', 'Charcoal cargo trousers', 'Bottoms', 'Trousers', 'Carhartt WIP', 'Charcoal', 'Solid', 'Cotton', '32', 115.00, 16, DATE '2025-06-28', 'https://example.com/images/charcoal-cargo-trousers.jpg'),
	('alex_threads', 'Sky blue oxford shirt', 'Tops', 'Button-Up', 'J.Crew', 'Sky blue', 'Solid', 'Cotton', 'M', 79.50, 14, DATE '2025-04-07', 'https://example.com/images/sky-blue-oxford.jpg'),
	('alex_threads', 'Olive chino pants', 'Bottoms', 'Chinos', 'Bonobos', 'Olive', 'Solid', 'Cotton', '31', 99.00, 20, DATE '2025-05-19', 'https://example.com/images/olive-chinos.jpg'),
	('alex_threads', 'Navy knit blazer', 'Outerwear', 'Blazer', 'Spier & Mackay', 'Navy', 'Solid', 'Wool blend', 'M', 198.00, 9, DATE '2025-01-22', 'https://example.com/images/navy-knit-blazer.jpg'),
	('sam_dressed', 'Dusty rose midi dress', 'Dresses', 'Midi Dress', 'Reformation', 'Dusty rose', 'Floral', 'Viscose', 'S', 218.00, 7, DATE '2025-07-14', 'https://example.com/images/dusty-rose-dress.jpg'),
	('sam_dressed', 'Cream cable-knit cardigan', 'Knitwear', 'Cardigan', 'Madewell', 'Cream', 'Textured', 'Cotton blend', 'S', 88.00, 11, DATE '2025-11-02', 'https://example.com/images/cream-cardigan.jpg'),
	('sam_dressed', 'Light wash wide-leg jeans', 'Bottoms', 'Jeans', 'Abercrombie', 'Light blue', 'Solid', 'Denim', '28', 89.00, 15, DATE '2025-03-30', 'https://example.com/images/light-wide-leg-jeans.jpg')
) AS item(username, item_name, category, subcategory, brand, primary_color, pattern, material, item_size, purchase_price, times_worn, purchase_date, image_url)
	ON users.username = item.username;

INSERT INTO recommendations (
	user_id, item_id, recommendation, confidence_score, color_score,
	body_type_score, preference_score, recommendation_reason
)
SELECT users.user_id, clothing_items.item_id, recommendation.recommendation,
	   recommendation.confidence_score, recommendation.color_score,
	   recommendation.body_type_score, recommendation.preference_score,
	   recommendation.recommendation_reason
FROM users
JOIN (VALUES
	('maya_style', 'Camel wool coat', 'BUY', 0.9400, 0.9700, 0.9100, 0.9400, 'Warm autumn colors and a defined waist suit your profile.'),
	('maya_style', 'Dark straight-leg jeans', 'BUY', 0.8800, 0.8200, 0.9300, 0.9000, 'A versatile classic that balances your proportions.'),
	('jordan_wardrobe', 'Black utility jacket', 'BUY', 0.9200, 0.9800, 0.8800, 0.9300, 'The clean black silhouette matches your minimalist wardrobe.'),
	('jordan_wardrobe', 'White heavyweight tee', 'MAYBE', 0.6700, 0.7600, 0.7000, 0.6500, 'Useful basic, but consider whether you need another white tee.'),
	('alex_threads', 'Navy knit blazer', 'BUY', 0.9000, 0.8800, 0.9200, 0.9100, 'Navy works with your warm coloring and smart-casual style.'),
	('alex_threads', 'Olive chino pants', 'BUY', 0.8500, 0.9000, 0.8400, 0.8600, 'Olive adds color while staying easy to pair with your wardrobe.'),
	('sam_dressed', 'Dusty rose midi dress', 'BUY', 0.9500, 0.9600, 0.9000, 0.9700, 'Soft summer coloring and a romantic silhouette make this a strong match.'),
	('sam_dressed', 'Cream cable-knit cardigan', 'MAYBE', 0.7200, 0.7800, 0.7600, 0.6800, 'A gentle neutral that works well, though the texture may feel bulky.')
) AS recommendation(username, item_name, recommendation, confidence_score, color_score, body_type_score, preference_score, recommendation_reason)
	ON users.username = recommendation.username
JOIN clothing_items
	ON clothing_items.user_id = users.user_id
   AND clothing_items.item_name = recommendation.item_name;

INSERT INTO feedback (
	user_id, recommendation_id, purchased, rating, times_worn, feedback, comments
)
SELECT users.user_id, recommendations.recommendation_id, feedback_data.purchased,
	   feedback_data.rating, feedback_data.times_worn, feedback_data.feedback,
	   feedback_data.comments
FROM users
JOIN (VALUES
	('maya_style', 'Camel wool coat', TRUE, 5, 6, 'LIKE', 'The color is flattering and it works for both work and weekends.'),
	('maya_style', 'Dark straight-leg jeans', TRUE, 4, 8, 'LIKE', 'Comfortable fit and easy to style.'),
	('jordan_wardrobe', 'Black utility jacket', TRUE, 5, 10, 'LIKE', 'Exactly the practical layer I was looking for.'),
	('jordan_wardrobe', 'White heavyweight tee', FALSE, 3, 0, 'NEUTRAL', 'I already have several similar tees.'),
	('alex_threads', 'Navy knit blazer', TRUE, 5, 4, 'LIKE', 'Looks polished without feeling too formal.'),
	('sam_dressed', 'Dusty rose midi dress', TRUE, 5, 3, 'LIKE', 'The fit and color are both excellent.'),
	('sam_dressed', 'Cream cable-knit cardigan', FALSE, 2, 0, 'DISLIKE', 'The sleeves feel too oversized for my preference.')
) AS feedback_data(username, item_name, purchased, rating, times_worn, feedback, comments)
	ON users.username = feedback_data.username
JOIN clothing_items
	ON clothing_items.user_id = users.user_id
   AND clothing_items.item_name = feedback_data.item_name
JOIN recommendations
	ON recommendations.user_id = users.user_id
   AND recommendations.item_id = clothing_items.item_id;
