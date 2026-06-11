import streamlit as st
import pickle
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_KEY = st.secrets["TMDB_API_KEY"]

session = requests.Session()
retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
session.mount("https://", HTTPAdapter(max_retries=retry))

def fetch_poster(movie_id):
    try:
        response = session.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}",
            params={
                "api_key": API_KEY,
                "language": "en-US"
            },
            timeout=10
        )
        response.raise_for_status()
        print(response.status_code)
        print(response.text[:200])
        data = response.json()
        if data.get("poster_path"):
            return "https://image.tmdb.org/t/p/w500/" + data["poster_path"]

    except Exception as e:
        print(f"Error fetching poster for {movie_id}: {e}")
    return None

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True,key=lambda x: x[1])[1:6]
    recommended_movies = []
    recommended_movies_posters = []
    for mov in movies_list:
        movie_id = movies.iloc[mov[0]].movie_id
        print(movie_id)
        recommended_movies.append(movies.iloc[mov[0]].title)
        recommended_movies_posters.append(fetch_poster(movie_id)) # Fetch poster from API
    return recommended_movies,recommended_movies_posters

movies_dict = pickle.load(open("../movies_dictionary.pkl","rb"))
movies = pd.DataFrame(movies_dict)

vectors = pickle.load(open("../vectors.pkl","rb"))

@st.cache_resource
def load_similarity():
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.feature_extraction.text import CountVectorizer
    cv = CountVectorizer(max_features=5000,stop_words='english')
    similarity_vectors = cv.fit_transform(movies['tags'])
    similarity = cosine_similarity(similarity_vectors)
    return similarity

similarity = load_similarity()

st.title("Movie Recommender System")

selected_movie = st.selectbox("Movies",movies['title'].values)

if st.button("Recommend"):
    st.write("Recommended Movies")
    rec_movies,posters = recommend(selected_movie)
    cols = st.columns(5)
    for i,col in enumerate(cols):
        with col:
            st.text(rec_movies[i])
            if posters[i] is not None:
                st.image(posters[i])
            else:
                st.write("Poster unavailable")