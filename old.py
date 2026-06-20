"""
CineMatch — A movie recommender system.
Reads movie_dict.pkl ({'movie id': [...], 'title': [...], 'tags': [...]})
and similarity.pkl (cosine distance matrix aligned by row index).
Fetches posters, genres, ratings, and overview live from TMDB.
"""

import os
import pickle
import time

import pandas as pd
import requests
import streamlit as st

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

st.set_page_config(
    page_title="CineMatch — Find your next watch",
    page_icon="🎞️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def _load_tmdb_key() -> str:
    """Check, in order: env var, then a local tmdb_key.txt file in the project folder."""
    key = os.environ.get("TMDB_API_KEY", "").strip()
    if key:
        return key
    key_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmdb_key.txt")
    if os.path.exists(key_file):
        with open(key_file, "r") as f:
            return f.read().strip()
    return ""


TMDB_API_KEY = _load_tmdb_key()
TMDB_BASE = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p"
PLACEHOLDER_POSTER = "https://placehold.co/500x750/1c1f26/d4a24e?text=No+Poster&font=roboto"

NUM_RECOMMENDATIONS = 5


# --------------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def load_data():
    with open("movie_dict.pkl", "rb") as f:
        movie_dict = pickle.load(f)
    movies = pd.DataFrame(movie_dict)
    # Normalize column names (strip stray whitespace like ' movie id', 'title ')
    movies.columns = [c.strip() for c in movies.columns]
    rename_map = {}
    for c in movies.columns:
        if c.lower().replace("_", " ") == "movie id":
            rename_map[c] = "movie_id"
        elif c.lower() == "title":
            rename_map[c] = "title"
    movies = movies.rename(columns=rename_map)

    with open("similarity.pkl", "rb") as f:
        similarity = pickle.load(f)

    return movies, similarity


# --------------------------------------------------------------------------
# TMDB fetchers (cached so repeat lookups are instant + don't hit rate limits)
# --------------------------------------------------------------------------

@st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
def fetch_movie_details(movie_id: int) -> dict:
    """Returns poster_path, genres, rating, overview, release_date for a movie_id."""
    if not TMDB_API_KEY:
        return {}
    url = f"{TMDB_BASE}/movie/{movie_id}"
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}
    try:
        resp = requests.get(url, params=params, timeout=6)
        resp.raise_for_status()
        data = resp.json()
        return {
            "poster_path": data.get("poster_path"),
            "genres": [g["name"] for g in data.get("genres", [])],
            "rating": data.get("vote_average"),
            "overview": data.get("overview"),
            "release_date": data.get("release_date", ""),
            "runtime": data.get("runtime"),
        }
    except requests.RequestException:
        return {}


def poster_url(poster_path, size="w500"):
    if poster_path:
        return f"{IMG_BASE}/{size}{poster_path}"
    return PLACEHOLDER_POSTER


# --------------------------------------------------------------------------
# Recommendation engine
# --------------------------------------------------------------------------

def recommend(movie_title: str, movies: pd.DataFrame, similarity) -> list[dict]:
    matches = movies[movies["title"] == movie_title]
    if matches.empty:
        return []
    idx = matches.index[0]
    distances = list(enumerate(similarity[idx]))
    ranked = sorted(distances, reverse=True, key=lambda x: x[1])[1 : NUM_RECOMMENDATIONS + 1]

    results = []
    for i, score in ranked:
        row = movies.iloc[i]
        details = fetch_movie_details(int(row["movie_id"]))
        results.append(
            {
                "title": row["title"],
                "movie_id": int(row["movie_id"]),
                "score": score,
                **details,
            }
        )
    return results


# --------------------------------------------------------------------------
# Styling — film-strip cinema theme
# --------------------------------------------------------------------------

def inject_css():
    st.html(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
        <style>
        :root {
            --bg: #0B0C10;
            --bg-card: #15171D;
            --bg-card-hover: #1C1F26;
            --accent: #D4A24E;
            --accent-soft: rgba(212, 162, 78, 0.14);
            --crimson: #A8334B;
            --text: #E8E6E1;
            --text-dim: #8C8C94;
            --sprocket: #2A2D35;
            --radius: 4px;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(ellipse 1200px 600px at 50% -10%, rgba(212,162,78,0.06), transparent),
                var(--bg);
            color: var(--text);
        }

        #MainMenu, footer, header {visibility: hidden;}

        .block-container {
            padding-top: 2rem;
            max-width: 1200px;
        }

        /* ---------- Sprocket rule (signature element) ---------- */
        .sprocket-rule {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 4px;
            margin: 0 0 0.4rem 0;
        }
        .sprocket-rule span {
            width: 9px;
            height: 9px;
            border-radius: 2px;
            background: var(--sprocket);
            flex-shrink: 0;
        }
        .sprocket-rule::before, .sprocket-rule::after { content: none; }
        .sprocket-line {
            flex: 1;
            display: flex;
            justify-content: space-between;
            gap: 14px;
            padding: 0 10px;
        }

        /* ---------- Hero ---------- */
        .hero-wrap {
            text-align: center;
            padding: 1.4rem 0 0.6rem 0;
        }
        .hero-eyebrow {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            letter-spacing: 0.32em;
            text-transform: uppercase;
            color: var(--accent);
            margin-bottom: 0.6rem;
        }
        .hero-title {
            font-family: 'Bebas Neue', sans-serif;
            font-size: 5rem;
            line-height: 0.95;
            letter-spacing: 0.04em;
            color: var(--text);
            margin: 0;
        }
        .hero-title em {
            font-style: normal;
            color: var(--accent);
        }
        .hero-sub {
            font-size: 1rem;
            color: var(--text-dim);
            margin-top: 0.8rem;
            max-width: 560px;
            margin-left: auto;
            margin-right: auto;
        }

        /* ---------- Search section ---------- */
        .search-label {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: var(--text-dim);
            margin-bottom: 0.5rem;
            margin-top: 1.6rem;
        }

        div[data-baseweb="select"] > div {
            background-color: var(--bg-card) !important;
            border: 1px solid var(--sprocket) !important;
            border-radius: var(--radius) !important;
        }
        div[data-baseweb="select"] span {
            color: var(--text) !important;
        }

        .stButton > button {
            background: var(--accent);
            color: #15120A;
            border: none;
            border-radius: var(--radius);
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            font-size: 0.82rem;
            padding: 0.65rem 1.6rem;
            transition: all 0.15s ease;
            width: 100%;
        }
        .stButton > button:hover {
            background: #E5B765;
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(212,162,78,0.25);
        }
        .stButton > button:active { transform: translateY(0); }

        /* ---------- Section heading for results ---------- */
        .results-heading {
            font-family: 'Bebas Neue', sans-serif;
            font-size: 1.9rem;
            letter-spacing: 0.03em;
            color: var(--text);
            margin: 2.6rem 0 0.3rem 0;
        }
        .results-heading span { color: var(--accent); }
        .results-caption {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            color: var(--text-dim);
            letter-spacing: 0.06em;
            margin-bottom: 1.4rem;
        }

        /* ---------- Movie frame card ---------- */
        .frame-card {
            background: var(--bg-card);
            border: 1px solid var(--sprocket);
            border-radius: var(--radius);
            overflow: hidden;
            transition: border-color 0.2s ease, transform 0.2s ease;
            height: 100%;
        }
        .frame-card:hover {
            border-color: var(--accent);
            transform: translateY(-3px);
        }
        .frame-poster-wrap {
            position: relative;
            width: 100%;
            aspect-ratio: 2 / 3;
            overflow: hidden;
            background: #0E0F13;
        }
        .frame-poster-wrap img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }
        .frame-rating {
            position: absolute;
            top: 8px;
            right: 8px;
            background: rgba(11,12,16,0.85);
            border: 1px solid var(--accent);
            color: var(--accent);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 2px 7px;
            border-radius: 3px;
            backdrop-filter: blur(4px);
        }
        .frame-match {
            position: absolute;
            bottom: 8px;
            left: 8px;
            background: rgba(168,51,75,0.9);
            color: #fff;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.66rem;
            font-weight: 600;
            letter-spacing: 0.04em;
            padding: 2px 7px;
            border-radius: 3px;
        }
        .frame-body {
            padding: 0.85rem 0.9rem 1rem 0.9rem;
        }
        .frame-title {
            font-weight: 700;
            font-size: 0.95rem;
            line-height: 1.25;
            color: var(--text);
            margin-bottom: 0.3rem;
            min-height: 2.4em;
        }
        .frame-meta {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.68rem;
            color: var(--text-dim);
            margin-bottom: 0.5rem;
        }
        .frame-genres {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-bottom: 0.6rem;
        }
        .genre-pill {
            font-size: 0.64rem;
            font-family: 'JetBrains Mono', monospace;
            color: var(--accent);
            background: var(--accent-soft);
            padding: 2px 7px;
            border-radius: 10px;
            white-space: nowrap;
        }
        .frame-overview {
            font-size: 0.78rem;
            color: var(--text-dim);
            line-height: 1.5;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        /* ---------- Empty state ---------- */
        .empty-state {
            text-align: center;
            padding: 3rem 1rem;
            color: var(--text-dim);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            border: 1px dashed var(--sprocket);
            border-radius: var(--radius);
            margin-top: 1.5rem;
        }

        /* ---------- Footer ---------- */
        .app-footer {
            text-align: center;
            color: var(--text-dim);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.7rem;
            letter-spacing: 0.08em;
            margin-top: 3.5rem;
            padding-top: 1.4rem;
            border-top: 1px solid var(--sprocket);
        }

        @media (max-width: 640px) {
            .hero-title { font-size: 3rem; }
        }
        </style>
        """
    )


def sprocket_rule():
    dots = "".join(["<span></span>" for _ in range(28)])
    st.html(f'<div class="sprocket-rule"><div class="sprocket-line">{dots}</div></div>')


# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------

def render_hero():
    sprocket_rule()
    st.html(
        """
        <div class="hero-wrap">
            <div class="hero-eyebrow">Frame by frame, find what's next</div>
            <h1 class="hero-title">CINE<em>MATCH</em></h1>
            <p class="hero-sub">
                Pick a film you love. We'll scan thousands of plots, genres,
                and themes to reel in five you'll love just as much.
            </p>
        </div>
        """
    )
    sprocket_rule()


def render_card(movie: dict):
    title = movie["title"]
    rating = movie.get("rating")
    rating_html = f'<div class="frame-rating">★ {rating:.1f}</div>' if rating else ""
    match_pct = max(0, min(100, round(movie.get("score", 0) * 100)))

    genres = movie.get("genres") or []
    genre_html = "".join(f'<span class="genre-pill">{g}</span>' for g in genres[:3])

    year = (movie.get("release_date") or "")[:4]
    runtime = movie.get("runtime")
    meta_parts = [p for p in [year, f"{runtime} min" if runtime else None] if p]
    meta_html = " · ".join(meta_parts)

    overview = movie.get("overview") or "No synopsis available."

    st.html(
        f"""
        <div class="frame-card">
            <div class="frame-poster-wrap">
                <img src="{poster_url(movie.get('poster_path'))}" alt="{title} poster" />
                {rating_html}
                <div class="frame-match">{match_pct}% MATCH</div>
            </div>
            <div class="frame-body">
                <div class="frame-title">{title}</div>
                <div class="frame-meta">{meta_html}</div>
                <div class="frame-genres">{genre_html}</div>
                <div class="frame-overview">{overview}</div>
            </div>
        </div>
        """
    )


def main():
    inject_css()

    if not TMDB_API_KEY:
        st.warning(
            "⚠️ TMDB_API_KEY environment variable not set. Posters, ratings, "
            "genres, and overviews won't load until it's configured. "
            "See the README for setup instructions.",
            icon="⚠️",
        )

    try:
        movies, similarity = load_data()
    except FileNotFoundError as e:
        st.error(
            f"Couldn't find a required file: `{e.filename}`. Make sure "
            "`movie_dict.pkl` and `similarity.pkl` are in the project root."
        )
        st.stop()
    except Exception as e:
        st.error(f"Failed to load model files: {e}")
        st.stop()

    render_hero()

    st.html('<div class="search-label">Select a film</div>')
    col1, col2 = st.columns([4, 1])
    with col1:
        selected_title = st.selectbox(
            "Select a film",
            options=movies["title"].values,
            label_visibility="collapsed",
            placeholder="Search by title…",
        )
    with col2:
        find_clicked = st.button("Find similar")

    if find_clicked and selected_title:
        with st.spinner("Scanning the archive…"):
            recommendations = recommend(selected_title, movies, similarity)

        st.html(
            f'<div class="results-heading">Because you watched <span>{selected_title}</span></div>'
        )
        st.html('<div class="results-caption">RANKED BY THEMATIC SIMILARITY</div>')

        if not recommendations:
            st.html('<div class="empty-state">No matches found for that title. Try another.</div>')
        else:
            cols = st.columns(len(recommendations))
            for col, movie in zip(cols, recommendations):
                with col:
                    render_card(movie)

    st.html(
        '<div class="app-footer">CINEMATCH · CONTENT-BASED RECOMMENDATION ENGINE · POWERED BY TMDB</div>'
    )


if __name__ == "__main__":
    main()
