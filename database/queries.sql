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
