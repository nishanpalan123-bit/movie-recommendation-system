import os
import pickle
import pandas as pd
import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------- SESSION WITH RETRIES ----------------
session = requests.Session()
retry = Retry(
    total=5,  # Retry up to 5 times
    backoff_factor=1,  # Wait 1s, 2s, 4s, etc. between retries
    status_forcelist=[429, 500, 502, 503, 504]  # Retry on these HTTP codes
)
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)

# ---------------- FETCH POSTER ----------------
@st.cache_data(show_spinner=False)
def fetch_poster(movie_id):
    """
    Fetches the movie poster from TMDB. Returns a placeholder if failed.
    """
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return "https://image.tmdb.org/t/p/w500/" + data['poster_path']
    except requests.exceptions.RequestException as e:
        print(f"[Warning] Failed to fetch poster for movie_id {movie_id}: {e}")
        return "https://via.placeholder.com/500x750.png?text=No+Image"

# ---------------- RECOMMEND FUNCTION ----------------
def recommend(movie):
    """
    Returns a list of 5 recommended movie titles and their posters.
    """
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]

    # Get top 5 similar movies
    movies_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:6]

    recommended_movies = []
    recommended_posters = []

    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        recommended_posters.append(fetch_poster(movie_id))

    return recommended_movies, recommended_posters

# ---------------- LOAD FILES ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

movies_dict = pickle.load(open(os.path.join(BASE_DIR, "movie_dict.pkl"), "rb"))
movies = pd.DataFrame(movies_dict)

similarity = pickle.load(open(os.path.join(BASE_DIR, "similarity.pkl"), "rb"))

# ---------------- STREAMLIT UI ----------------
st.set_page_config(page_title="🎬 Movie Recommender", layout="wide")
st.title("🎬 Movie Recommender System")

selected_movie_name = st.selectbox(
    "Select a movie:",
    movies['title'].values
)

if st.button("Recommend"):
    with st.spinner("Finding recommendations..."):
        names, posters = recommend(selected_movie_name)

    # Display movies in a row of 5 columns
    cols = st.columns(5)
    for idx, col in enumerate(cols):
        with col:
            st.image(posters[idx], width=180)  # Fixed width for consistent layout
            st.caption(names[idx])             # Clean title display