import streamlit as st
import pandas as pd
import pickle
import requests
import time

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Movie Recommender System",
    page_icon="🎬",
    layout="wide"
)

# ---------------- LOAD DATA ----------------

movies_dict = pickle.load(open("movie_dict.pkl", "rb"))
movies = pd.DataFrame(movies_dict)

similarity = pickle.load(open("similarity.pkl", "rb"))

TMDB_API_KEY = "c0d19e14e4b0199155f7ebf0f367d004"

# ---------------- CUSTOM CSS ----------------

st.markdown("""
<style>

.main{
    background-color:#141414;
    color:white;
}

.stApp{
    background-color:#141414;
}

h1,h2,h3,p,label{
    color:white !important;
}

.movie-title{
    text-align:center;
    font-size:15px;
    font-weight:bold;
    padding-top:8px;
}

div[data-testid="stSelectbox"]{
    background-color:#222222;
}
            

 img {
    border-radius:15px !important;
}

img:hover{
    transform:scale(1.05);
    transition:0.3s;
}

div.stButton > button{
    background-color:#E50914;
    color:white;
    border:none;
    border-radius:10px;
}

div.stButton > button:hover{
    background-color:#ff1f1f;
}           
            
</style>
""", unsafe_allow_html=True)

# ---------------- TMDB FUNCTIONS ----------------

@st.cache_data
def get_movie_details(movie_id):

    url = f"https://api.themoviedb.org/3/movie/{movie_id}"

    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        poster_path = data.get("poster_path")

        if poster_path:
            poster = f"https://image.tmdb.org/t/p/w500{poster_path}"
        else:
            poster = "https://placehold.co/500x750?text=No+Poster"

        return {
            "poster": poster,
            "rating": data.get("vote_average", "N/A"),
            "genres": ", ".join(
                [g["name"] for g in data.get("genres", [])]
            ),
            "overview": data.get(
                "overview",
                "Overview not available."
            )
        }

    except Exception as e:
        print(e)

        return {
            "poster": "https://placehold.co/500x750?text=No+Poster",
            "rating": "N/A",
            "genres": "Not Available",
            "overview": "Overview not available."
        }
    
def recommend(movie):

    movie_index = movies[movies['title'] == movie].index[0]

    distances = similarity[movie_index]

    movies_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x:x[1]
    )[1:11]

    recommended_movies = []

    for i in movies_list:

        movie_id = movies.iloc[i[0]].movie_id

        details = get_movie_details(movie_id)
        time.sleep(0.2)

        print("Title:", movies.iloc[i[0]].title)
        print("Movie ID:", movie_id)
        print("Poster:", details["poster"])
        print("="*50)

        recommended_movies.append({
        "title": movies.iloc[i[0]].title,
        "poster": details["poster"],
        "rating": details["rating"],
        "genres": details["genres"],
        "overview": details["overview"]
    })

    return recommended_movies

# ---------------- HEADER ----------------

st.markdown("""
<div style="
background: linear-gradient(135deg,#000000,#1a1a1a,#E50914);
padding:40px;
border-radius:20px;
margin-bottom:20px;
">
<h1 style="color:white;font-size:48px;">
🎬 Cineflex
</h1>

<h3 style="color:#d3d3d3;">
AI Powered Movie Recommendation System
</h3>

<p style="color:white;">
Get personalized movie recommendations instantly.
</p>
</div>
""", unsafe_allow_html=True)

# ---------------- SELECT MOVIE ----------------

selected_movie = st.selectbox(
    "🔍 Search Movie",
    movies['title'].values
)

# ---------------- RECOMMEND BUTTON ----------------

if st.button("Recommend Movies"):

    recommendations = recommend(selected_movie)

    st.markdown("""<h2 style='color:white'>🔥 Recommended For You</h2>
""", unsafe_allow_html=True)

    cols = st.columns(4)

    for idx, movie in enumerate(recommendations[:4]):

        with cols[idx]:

            if movie["poster"]:
                st.image(movie["poster"], use_container_width=True)
            else:
                st.markdown("""
<div style="
    height:660px;
    width:100%;
    background:#1e1e1e;
    border-radius:15px;
    display:flex;
    justify-content:center;
    align-items:center;
    color:white;
    font-size:22px;
    font-weight:bold;
">
    🎬 No Poster
</div>
""", unsafe_allow_html=True)

            st.markdown(f"""<div style="background:#1e1e1e;padding:10px;border-radius:10px;margin-top:5px;text-align:center;height:70px;display:flex;
                        align-items:centerjustify-content:center;font-weight:bold;">{movie['title']}</div>
            """, unsafe_allow_html=True)

            rating = movie["rating"]

            if rating == "N/A":
                st.caption("⭐ N/A")
            else:
                st.caption(f"⭐ {round(float(rating),1)}")
                with st.expander("📖 Overview"):
                    st.write(movie["overview"])

    st.write("")
    st.write("")

    cols = st.columns(4)

    for idx, movie in enumerate(recommendations[4:8]):

        with cols[idx]:

            if movie["poster"]:
                st.image(movie["poster"], use_container_width=True)
            else:
                st.markdown("""
<div style="
    height:660px;
    width:100%;
    background:#1e1e1e;
    border-radius:15px;
    display:flex;
    justify-content:center;
    align-items:center;
    color:white;
    font-size:22px;
    font-weight:bold;
">
    🎬 No Poster
</div>
""", unsafe_allow_html=True)

            st.markdown(f"""<div style="background:#1e1e1e;padding:10px;border-radius:10px;margin-top:5px;text-align:center;height:70px;display:flex;
                        align-items:centerjustify-content:center;font-weight:bold;">{movie['title']}</div>
            """, unsafe_allow_html=True)

            rating = movie["rating"]

            if rating == "N/A":
                st.caption("⭐ N/A")
            else:
                st.caption(f"⭐ {movie['rating']}")
                with st.expander("📖 Overview"):
                    st.write(movie["overview"])

# ---------------- FOOTER ----------------

st.markdown("---")
st.markdown(
    "<center>Built with ❤️ using Streamlit</center>",
    unsafe_allow_html=True
)