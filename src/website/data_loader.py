from brain import rodar_sync
import streamlit as st
import brain

@st.cache_data(ttl=86400)
def carregar_dados(cache_window):
    dados = rodar_sync(brain.site_data_reload())
    return dados

@st.cache_data(ttl=86400)
def load_team_table(time_id, cache_window):
    stats_table = rodar_sync(brain.load_team_table(time_id))
    return stats_table

@st.cache_data(ttl=86400)
def load_team_ratings(time_id, cache_window):
    team_ratings = rodar_sync(brain.load_team_ratings(time_id))
    return team_ratings

@st.cache_data(ttl=86400)
def load_player_map_stats(time_id, pool, cache_window):
    map_stats = rodar_sync(brain.load_player_map_stats(time_id, pool))
    return map_stats

@st.cache_data(ttl=86400)
def load_leaderboard(map_id, condition, cache_window):
    lb = rodar_sync(brain.load_leaderboard(map_id, condition))
    return lb

