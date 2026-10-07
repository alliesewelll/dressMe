# dressMe

A personal style app being built around style profiles, a digital wardrobe, and
eventual Buy / Maybe / Skip recommendations.

## Try the wardrobe API

Configure `DATABASE_URL` in a root `.env` file using `.env.example` as a guide.
Use an existing PostgreSQL user record (the sample data uses IDs 1–4).
`database/seed.sql` resets the tables, so only run it against a disposable demo database.

From an environment with `backend/requirements.txt` installed:

```sh
cd backend
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs and try `POST /users/{user_id}/wardrobe`
with an existing user ID and this body:

```json
{
  "item_name": "Blue cotton shirt",
  "category": "Tops",
  "primary_color": "Blue",
  "material": "Cotton",
  "purchase_price": "29.95"
}
```

Then use `GET /users/{user_id}/wardrobe` to see saved items, newest first.
The list supports `limit` (1–100, default 50) and `offset` (default 0).
Only `item_name` is required. Blank names, negative prices/wear counts, and
unknown fields are rejected. An unknown user returns 404; an empty wardrobe returns `[]`.
`image_url` stores a reference only; image uploads and AI analysis are future work.

These are local prototype endpoints: user IDs select records, and authentication
and access controls are not implemented yet.

## Save and retrieve style preferences

Use `PATCH /users/{user_id}/style-profile` in `/docs` to create a profile or
update selected preferences for an existing user:

```json
{
  "color_season": "Autumn",
  "undertone": "Warm",
  "preferred_styles": "Classic, relaxed, earth tones"
}
```

`body_type` is also optional. `preferred_styles` is free-form text, consistent
with the existing database. These preferences are supplied by the user, not
automatically inferred. The endpoint returns the saved profile.

Use `GET /users/{user_id}/style-profile` to retrieve it. Missing users or profiles
return 404. Updates preserve omitted fields; send `null` to clear a field.
Empty requests, blank strings, unknown fields, and overly long values return 422.
Each user has one profile; repeated saves update the same record.

User schemas now use `username` to match the database. Signup input represents
a private `password`; a future signup handler must hash it into `password_hash`.
User responses exclude passwords and hashes. Signup/login endpoints are still
not implemented, and preferences use the same local-prototype access model as the wardrobe.

## Tests

From the project root, using an environment with the backend dependencies and `httpx`:

```sh
python -m unittest discover -s backend -p 'test_*.py'
```

Tests use a temporary SQLite database and do not touch your PostgreSQL data.
