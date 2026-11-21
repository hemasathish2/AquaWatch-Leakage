# AquaWatch — Streamlit + Render + Supabase (No AWS)

## Step 1 — Supabase
1. Create a free project at https://supabase.com.
2. Open SQL Editor, paste and run `schema.sql`.
3. In Storage, create a **private** bucket named `complaint-photos`.
4. In Project Settings > API / API Keys, find your project URL and **service_role / secret key**. Never share this key or commit it to GitHub.

## Step 2 — Run locally (Mac)
```bash
cd AquaWatch-Streamlit-Render
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Edit `.env` with your Supabase URL, service-role key, and a strong admin password.
```bash
streamlit run app.py
```
Open http://localhost:8501.

## Step 3 — Deploy with Render
1. Upload the project to a new GitHub repository. Do **not** upload `.env`.
2. Go to https://dashboard.render.com > New > Web Service; connect the repo.
3. Choose Python runtime and Free plan if available.
4. Build command: `pip install -r requirements.txt`
5. Start command: `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true`
6. Set environment variables: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `ADMIN_PASSWORD`.
7. Deploy and open your assigned `https://...onrender.com` link.

## Notes
- Supabase stores complaints and photos persistently. Render's local filesystem is temporary.
- Render free services can sleep after inactivity; Supabase free projects may pause after inactivity.
- Admin uses one shared password, suitable for a student demo, not production.
- Anyone who knows a complaint ID can view it; do not submit sensitive personal information.
- Before a wider public launch, add authentication, rate limiting, and privacy controls.

## Exact leakage location on the map
On **Report Leakage**, pan/zoom the map to the leakage area and **click the exact spot**.
The selected coordinates are saved with the complaint in Supabase. The tracking page
and admin dashboard show the location on a map and provide a Google Maps link.
The initial map is centered on Bengaluru, but you can navigate anywhere.
This is a user-selected pin, **not automatic GPS detection**.
For an existing Supabase project, rerun `schema.sql` to add the new columns.
