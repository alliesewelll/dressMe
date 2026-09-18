-- 1. Most common clothing colors
SELECT
	primary_color,
	COUNT(*) AS item_count,
	ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS percentage_of_wardrobe
FROM clothing_items
GROUP BY primary_color
ORDER BY item_count DESC, primary_color;

-- 2. Average rating by clothing category
SELECT
	c.category,
	ROUND(AVG(f.rating), 2) AS average_rating,
	COUNT(f.rating) AS rating_count
FROM clothing_items AS c
JOIN recommendations AS r ON r.item_id = c.item_id
JOIN feedback AS f ON f.recommendation_id = r.recommendation_id
WHERE f.rating IS NOT NULL
GROUP BY c.category
ORDER BY average_rating DESC, rating_count DESC;

-- 3. Recommendation acceptance rate
-- Acceptance is calculated from recommendations with purchase feedback.
SELECT
	COUNT(*) FILTER (WHERE purchased = TRUE) AS accepted_count,
	COUNT(*) FILTER (WHERE purchased = FALSE) AS declined_count,
	COUNT(*) AS responded_count,
	ROUND(
		100.0 * COUNT(*) FILTER (WHERE purchased = TRUE)
		/ NULLIF(COUNT(*), 0),
		2
	) AS acceptance_rate_percent
FROM feedback
WHERE purchased IS NOT NULL;

-- 4. Brands and categories a specific user prefers
-- Change 'maya_style' to another username as needed.
SELECT
	u.username,
	c.brand,
	c.category,
	COUNT(*) AS positive_feedback_count,
	COUNT(*) FILTER (WHERE f.purchased = TRUE) AS purchased_count,
	ROUND(AVG(f.rating), 2) AS average_rating
FROM users AS u
JOIN feedback AS f ON f.user_id = u.user_id
JOIN recommendations AS r ON r.recommendation_id = f.recommendation_id
JOIN clothing_items AS c ON c.item_id = r.item_id
WHERE u.username = 'maya_style'
  AND (f.feedback = 'LIKE' OR f.purchased = TRUE)
GROUP BY u.username, c.brand, c.category
ORDER BY positive_feedback_count DESC, average_rating DESC NULLS LAST;

-- 5. Wardrobe distribution by item type for each user
SELECT
	u.username,
	c.category,
	COUNT(*) AS item_count,
	ROUND(
		100.0 * COUNT(*)
		/ SUM(COUNT(*)) OVER (PARTITION BY u.user_id),
		2
	) AS percentage_of_wardrobe
FROM users AS u
JOIN clothing_items AS c ON c.user_id = u.user_id
GROUP BY u.user_id, u.username, c.category
ORDER BY u.username, item_count DESC, c.category;

-- 6. Average recommendation confidence by category
SELECT
	c.category,
	ROUND(AVG(r.confidence_score), 4) AS avg_confidence,
	ROUND(AVG(f.rating), 2) AS avg_rating,
	COUNT(r.recommendation_id) AS recommendation_count
FROM clothing_items AS c
JOIN recommendations AS r ON r.item_id = c.item_id
LEFT JOIN feedback AS f ON f.recommendation_id = r.recommendation_id
GROUP BY c.category
ORDER BY avg_confidence DESC, avg_rating DESC;

-- 7. Top-performing items by buy rate
SELECT
	c.item_name,
	c.brand,
	c.category,
	COUNT(f.feedback_id) AS feedback_count,
	COUNT(*) FILTER (WHERE f.purchased = TRUE) AS bought_count,
	COUNT(*) FILTER (WHERE f.purchased = FALSE) AS declined_count,
	ROUND(
		100.0 * COUNT(*) FILTER (WHERE f.purchased = TRUE)
		/ NULLIF(COUNT(f.feedback_id), 0),
		2
	) AS buy_rate_percent,
	ROUND(AVG(f.rating), 2) AS avg_rating
FROM clothing_items AS c
LEFT JOIN recommendations AS r ON r.item_id = c.item_id
LEFT JOIN feedback AS f ON f.recommendation_id = r.recommendation_id
GROUP BY c.item_id, c.item_name, c.brand, c.category
HAVING COUNT(f.feedback_id) > 0
ORDER BY buy_rate_percent DESC, avg_rating DESC NULLS LAST;

-- 8. User purchase behavior summary
SELECT
	u.username,
	COUNT(f.feedback_id) AS total_feedback,
	COUNT(*) FILTER (WHERE f.purchased = TRUE) AS purchases,
	COUNT(*) FILTER (WHERE f.purchased = FALSE) AS non_purchases,
	ROUND(
		100.0 * COUNT(*) FILTER (WHERE f.purchased = TRUE)
		/ NULLIF(COUNT(f.feedback_id), 0),
		2
	) AS purchase_rate_percent,
	ROUND(AVG(f.rating), 2) AS avg_rating
FROM users AS u
LEFT JOIN feedback AS f ON f.user_id = u.user_id
GROUP BY u.user_id, u.username
ORDER BY purchase_rate_percent DESC NULLS LAST, total_feedback DESC;

-- 9. Total spend and average purchase price by user and category
SELECT
	u.username,
	c.category,
	COUNT(*) AS item_count,
	ROUND(SUM(c.purchase_price), 2) AS total_spend,
	ROUND(AVG(c.purchase_price), 2) AS avg_purchase_price
FROM users AS u
JOIN clothing_items AS c ON c.user_id = u.user_id
GROUP BY u.user_id, u.username, c.category
ORDER BY total_spend DESC NULLS LAST, item_count DESC;

-- 10. Most-worn items in the wardrobe
SELECT
	u.username,
	c.item_name,
	c.category,
	c.brand,
	c.times_worn,
	c.purchase_price,
	c.purchase_date
FROM clothing_items AS c
JOIN users AS u ON u.user_id = c.user_id
ORDER BY c.times_worn DESC, c.purchase_price DESC NULLS LAST
LIMIT 10;

-- 11. Style profile distribution across the app
SELECT
	sp.color_season,
	sp.body_type,
	COUNT(*) AS profile_count
FROM style_profiles AS sp
GROUP BY sp.color_season, sp.body_type
ORDER BY profile_count DESC, sp.color_season, sp.body_type;

-- 12. High-confidence recommendations that were not purchased
SELECT
	u.username,
	c.item_name,
	c.category,
	r.recommendation,
	r.confidence_score,
	f.purchased,
	f.rating,
	r.recommendation_reason
FROM recommendations AS r
JOIN users AS u ON u.user_id = r.user_id
JOIN clothing_items AS c ON c.item_id = r.item_id
LEFT JOIN feedback AS f ON f.recommendation_id = r.recommendation_id
WHERE r.confidence_score >= 0.85
  AND (f.purchased IS NULL OR f.purchased = FALSE)
ORDER BY r.confidence_score DESC, u.username;

-- 13. Colors that look most pleasing on each user
-- The flattering score combines rating, positive feedback, and purchases.
WITH color_feedback AS (
	SELECT
		u.user_id,
		u.username,
		c.primary_color,
		COUNT(DISTINCT c.item_id) AS item_count,
		COUNT(f.feedback_id) AS feedback_count,
		AVG(f.rating) AS average_rating,
		AVG(CASE WHEN f.feedback = 'LIKE' THEN 1.0 ELSE 0.0 END) AS like_rate,
		AVG(CASE WHEN f.purchased = TRUE THEN 1.0 ELSE 0.0 END) AS purchase_rate
	FROM users AS u
	JOIN clothing_items AS c ON c.user_id = u.user_id
	JOIN recommendations AS r ON r.item_id = c.item_id
	JOIN feedback AS f ON f.recommendation_id = r.recommendation_id
	WHERE c.primary_color IS NOT NULL
	GROUP BY u.user_id, u.username, c.primary_color
)
SELECT
	username,
	primary_color,
	item_count,
	feedback_count,
	ROUND(average_rating, 2) AS average_rating,
	ROUND(100.0 * like_rate, 2) AS like_rate_percent,
	ROUND(100.0 * purchase_rate, 2) AS purchase_rate_percent,
	ROUND(
		(average_rating / 5.0) * 0.50
		+ like_rate * 0.30
		+ purchase_rate * 0.20,
		4
	) AS flattering_score
FROM color_feedback
ORDER BY username, flattering_score DESC, feedback_count DESC, primary_color;