# dressMe

A personal style app being built around style profiles, a digital wardrobe, and
eventual Buy / Maybe / Skip recommendations.

## Frontend preview

Start the interactive sample wardrobe from the project root (no database needed):

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory frontend
```

Open http://127.0.0.1:8765. The responsive dashboard includes illustrated clothing
cards, search and category filters, adding pieces, recording wears, a style profile
editor, palette swatches, and styling ideas. Demo changes reset on refresh.
Illustrations are placeholders, not photos of actual clothing. Fonts load from
Google Fonts with local serif/sans-serif fallbacks.

For saved data, start the backend as described below and open
http://127.0.0.1:8000/app/. Choose **Demo wardrobe → Connect to backend** and enter
an existing user ID. Live mode calls the existing API on the same origin; this
frontend does not add authentication. The standalone preview only supports demo
mode. Item editing/deletion and image uploads are not yet exposed in the dashboard.

Demo palette and silhouette data in `frontend/styling-data.js` mirrors the rules
in `backend/styling.py`; keep these in sync when changing demo styling rules.

## Backend setup

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

## Record a wear

Use `POST /users/{user_id}/wardrobe/{item_id}/wear` in `/docs` with no request
body to increase the item's `times_worn` by one. The response contains the updated
item, and the wardrobe summary reflects the new total immediately.

Each successful request records another wear, including repeated requests; this
does not store wear dates or deduplicate by day. Use the existing PATCH endpoint
to correct accidental counts. Increments happen in the database to avoid lost
updates between simultaneous wear requests. Unknown users or items, and items
belonging to another user, return 404. A count at the maximum integer value returns
409. Login-based authorization is still pending.

## Remove a wardrobe item

Use `DELETE /users/{user_id}/wardrobe/{item_id}` in `/docs` with an item ID from
the wardrobe list. Success returns 204 with no response body. Missing users,
missing items, and items belonging to a different user return 404.

Deletion permanently removes the item; there is no undo. The wardrobe list and
summary exclude it immediately. Past recommendations and feedback remain stored,
but the recommendation's item reference becomes null and the clothing details
are no longer available. This checks the selected user's item ownership;
login-based authorization is still pending.

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

## Personalized styling ideas

`GET /users/{user_id}/style-suggestions` returns a palette and two generic
clothing suggestions with explanations, using the user's saved style profile.
For example, an Autumn / Hourglass profile suggests terracotta, olive, and camel
with a wrap top and a belted jacket.

The standalone `suggest_items(color_season, undertone, body_type)` function in
`backend/styling.py` contains editable starter rules. Spring, Summer, Autumn,
and Winter take precedence over warm, cool, or neutral undertones. Supported body
types are hourglass, pear, rectangle, athletic, apple, and inverted triangle.
Unknown values receive general suggestions with explanatory notes. A missing
user or profile returns 404.

These are subjective styling ideas based on self-reported preferences, not photo
analysis or predictions of attractiveness. Skin depth does not determine undertone.
This initial function does not use `preferred_styles`, match real products or
wardrobe items, or save recommendations. No new database tables are required.

## Tests

From the project root, using an environment with the backend dependencies and `httpx`:

```sh
python -m unittest discover -s backend -p 'test_*.py'
```

Tests use a temporary SQLite database and do not touch your PostgreSQL data.

## 16-palette personal color guide

The frontend features a Korean-inspired personal color guide with the 16 subtypes
selected for dressMe. Each card shows named swatches and opens the profile editor
with its palette selected; Save preferences applies it to suggestions. Existing
four-season profiles remain supported. Skin and hair descriptions are not used
to automatically classify users. The linked reference uses some different names.

`frontend/palettes.json` is the shared subtype and swatch catalog. After editing
it or the backend styling rules, run `python3 scripts/build_styling_data.py` to
refresh the generated offline demo data. Hex colors are illustrative approximations.

## Photo color studio

Open **Photo color studio** to select a local JPEG, PNG, or WebP portrait (up to
10 MB / 40 megapixels). Two copies of the same image appear surrounded by colors
from independently selected palettes. Select a swatch to compare colors, then
**Use [palette]** to open the profile editor and save your choice.

This is manual virtual draping, not automatic skin-tone detection or a ranked
season prediction. Lighting, makeup, and screen settings can affect appearance.
The original image is displayed without recoloring, cropping, or background removal.
Image bytes stay in a browser object URL, are never uploaded or stored, and are
released when replaced or removed. Refreshing clears the photo. Demo profile
changes remain temporary; live mode saves only the selected profile fields.

### Experimental photo detector

The photo studio now includes a browser-local canvas sampler. Click a skin patch
(or move the marker with arrow keys and press Enter) to get a three-palette
shortlist. Median RGB pixels reduce isolated pixel noise; a yellow-to-red ratio
estimates the sample's golden, rosy, or mixed cast. Very bright/dark samples are
rejected. These hand-written rules are unvalidated, not a trained detector or
professional season diagnosis; camera white balance can change the result.
It does not detect faces, infer ethnicity, or assign seasons by skin depth. The
shortlist covers broad starting palettes, not automatic classification into all
16 subtypes. Compare a suggestion, then explicitly save it through the profile.

## AI vision pipeline (new)

The photo studio now offers **Analyze with AI**, separate from the optional local
pixel experiment. It calls `POST /users/{user_id}/ai-style-analysis` with an image
body and `X-Photo-Consent: yes`. The backend validates the image, corrects EXIF
orientation, resizes to at most 1024px, strips metadata, and invokes the OpenAI
Responses API with a strict output schema. The model receives saved style
preferences, the newest 50 wardrobe items, and up to 20 recent feedback records.
No email, password, or username is sent. Results include photo-quality notes,
up to three palette candidates, clothing ideas, limitations, and the model name.

To enable it, set `OPENAI_API_KEY` and `STYLE_VISION_MODEL` in the root `.env`.
Choose a model available to your API account that supports image input and
Responses structured outputs. Restart FastAPI, visit `/app/`, connect an existing
user, select a portrait, and check the consent box before analyzing. API usage
may incur charges. `/ai/status` reports whether configuration is present.
Never place the key in frontend JavaScript. This remains a local prototype with
no authentication or per-user quotas; do not expose the endpoint publicly yet.

Local draping never sends the image. **Analyze with AI does send the resized
photo and style context to OpenAI**. The app does not persist photos or model
responses; `store: false` is passed to the provider, which does not itself imply
zero provider retention. Saving a suggested palette is a separate user action.

The adapter is tested with mocked provider responses, not a live paid model run.
It is an integration with a pretrained model, not a custom-trained color-analysis
model. Do not claim validated accuracy or automatic learning from feedback.

Next platform milestones: store analysis/feedback evaluation records, add a
Pandas evaluation notebook, introduce OpenCV image-quality features where useful,
and migrate the current vanilla-JavaScript UI to React. React, OpenCV, and a
trained recommendation model are not implemented in this increment.

## Recommendation feedback and evaluation

- `POST /users/{id}/recommendations`: record an explicit BUY/MAYBE/SKIP decision
  with a required explanation and optional owned `item_id`.
- `GET /users/{id}/recommendations`: list saved decisions with limit/offset pagination.
- `PUT /users/{id}/recommendations/{rec_id}/feedback`: save or replace the latest
  reaction, optional rating (1–5), purchase outcome, and notes. Omitted optional
  fields are cleared. Repeat reviews update one response rather than adding votes.
- `GET /users/{id}/recommendations/{rec_id}/feedback`: retrieve the latest response.

The frontend's **Was it a good recommendation?** section loads the latest 50
saved recommendations for a connected user and lets them review and revise
feedback. Demo suggestions and AI photo-analysis results are not automatically
converted to BUY/MAYBE/SKIP records. Use seeded recommendations or explicitly
record a decision through `/docs` first. Authentication remains pending.

Run the read-only Pandas report from the project root:

```sh
.venv/bin/python analysis/evaluate_recommendations.py --user-id 1
.venv/bin/python -m unittest discover -s analysis -p 'test_*.py'
```

It reports feedback coverage, like rate, purchase rate, and mean rating by decision.
Missing ratings and purchase responses are excluded from their denominators;
legacy duplicate reviews use the highest feedback ID. Empty groups use null
metrics. These are descriptive feedback metrics, not model accuracy or causal
proof of improvement. This adds evaluation infrastructure, not automatic retraining.

### Feedback-aware AI context

AI analysis now links each review to its recommendation and clothing item,
including category, color, brand, decision, explanation, and user comments.
Only the newest review per recommendation is included (up to 20). Deleted or
unavailable items have `item: null`; another user's items are never included.
Comments and explanations are limited to 2,000 characters each. This context is
sent to OpenAI only through the existing consented AI-analysis action.

For example, a negative review saying “Fit was uncomfortable” on a blue shirt
now reaches the model with its item details, rather than an unexplained negative
rating. The model is instructed not to assume a purchase implies liking an item.
This is context-based personalization, not model training; live output quality
still needs evaluation with configured model access.

### Evaluation API

`GET /users/{user_id}/recommendation-evaluation` returns the same Pandas metrics
as the CLI, grouped by BUY/MAYBE/SKIP. The API and CLI now share
`backend/evaluation.py` so their definitions stay consistent. It includes all
saved recommendations for the user, regardless of list pagination. Rates are
fractions from 0 to 1; missing outcomes yield null instead of a misleading zero.
An empty history returns `metrics: []`; a missing user returns 404.
Try it in `/docs`. These statistics describe recorded feedback, not predictive
accuracy. PostgreSQL integration is still unverified; tests use SQLite.

The frontend feedback section includes **Your recommendation report**. In live
mode, select **Refresh report** to see coverage, likes, purchase outcomes, and
average ratings grouped by recommendation. Saving feedback refreshes the report.
Missing purchase or rating answers remain unknown; demo activity is excluded.
Run `node frontend/test-evaluation.cjs` to check report formatting.

### Ranked wardrobe suggestions

`GET /users/{user_id}/wardrobe-ranking?limit=10` ranks the user's own clothes
against saved preferences and returns item IDs, names, scores, and explanations.
This deterministic baseline awards two points for an exact normalized palette
color match, one point for a curated related shade (instead of the exact-match
points), and one point for a saved style phrase found in item metadata.
Separate style phrases with commas, semicolons, or newlines. Scores range from
0–3 and are not probabilities. Ties use ascending item ID. Missing or unrecognized
preferences do not create guessed matches; an empty wardrobe returns an empty list.
The limit accepts 1–50. Related names include cream/ivory/off-white/warm white, olive/olive green,
terracotta/terra cotta/burnt orange, and cobalt/cobalt blue. Related matches are
explicitly labeled and score below exact matches. Broad colors are not expanded;
visual similarity is not measured. The method identifier is `palette-keywords-v2`.
This endpoint does not call AI, modify data, or automatically log BUY decisions.
In the frontend inspiration section, **Already in your closet → Find my matches**
loads the top five owned pieces in live mode, with explanations and matching points.
Changing the wardrobe or preferences clears outdated results. Demo mode prompts
users to connect their wardrobe. Feedback learning remains a separate next step.
Run `node frontend/test-wardrobe-ranking.cjs` for frontend state checks.

### Feedback feature summary

`GET /users/{user_id}/feedback-features` uses Pandas to summarize feedback by
normalized wardrobe color and category, separately for BUY, MAYBE, and SKIP.
It reports review counts, like rates, rating counts, and average ratings from
the latest review for each of the 100 most recently reviewed recommendations.
`reviewed_recommendations` includes reviews with missing/deleted items, which
cannot contribute feature groups. Missing ratings remain unknown. Item features
reflect the current wardrobe metadata, not a historical snapshot.
A liked SKIP decision is kept separate from liked BUY advice: these metrics
measure reactions to recommendations, not direct garment preferences. They do
not automatically alter ranking weights or demonstrate model improvement.
The endpoint is available in FastAPI's `/docs`; frontend integration is pending.

Download the same feedback feature metrics with
`GET /users/{user_id}/feedback-features.csv`. The CSV includes a stable header
for empty reports, blank missing ratings, and like rates on a 0–1 scale.
It uses the same latest-review logic and 100-review window as the JSON endpoint.
Response headers `X-Reviewed-Recommendations` and `X-Review-Window-Limit` expose
coverage. Spreadsheet formula-like labels are prefixed with an apostrophe.
No comments, photos, email addresses, or other users' records are exported.
After downloading, load it with `pd.read_csv("feedback-features-1.csv")`.

In live mode, the frontend recommendation report now provides **Download color &
category CSV**. Downloads show progress and retryable errors; switching users
cancels delivery of an outdated response. Demo mode disables the button.
Run `node frontend/test-feedback-export.cjs` to verify the download behavior.
