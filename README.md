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

## Wardrobe summary

Use `GET /users/{user_id}/wardrobe/summary` in `/docs` for an overview of the
user's entire wardrobe: item count, number of items with a recorded price,
total recorded spending, total wears, and items with zero recorded wears.

Missing prices are excluded from spending; a recorded zero price still counts
as priced. Spending is a decimal string and assumes all prices use the same
currency. Wear totals reflect manually recorded counts. An empty wardrobe
returns zero totals; an unknown user returns 404. The summary includes all of
the user's items regardless of wardrobe-list filters or pagination, and reflects
edits on the next request.

## Search your wardrobe

The wardrobe list accepts optional `search`, `category`, and `color` filters:

```text
GET /users/1/wardrobe?search=shirt&category=Tops&color=Blue
```

Search finds text anywhere in an item's name. Category and color match the whole
value. All three ignore case and trim surrounding spaces; blank filters are ignored.
Combine filters to narrow results, then use `limit` and `offset` to page through
the matches. Results remain newest first and limited to the selected user.
No matches returns `[]`. Search characters such as `%` and `_` are treated literally.
Try these fields on the GET wardrobe endpoint in `/docs`.

## Edit a wardrobe item

Use `PATCH /users/{user_id}/wardrobe/{item_id}` with IDs from the wardrobe list:

```json
{
  "item_name": "Blue linen shirt",
  "material": "Linen",
  "times_worn": 6
}
```

Only supplied fields change. `times_worn` sets the total wear count, rather than
incrementing it. Send `null` to clear optional details such as brand or price;
item name and wear count cannot be null. Empty updates and invalid values return
422. Missing items or items belonging to a different user return 404.
This checks the selected item's user ID; login-based authorization is still pending.

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
