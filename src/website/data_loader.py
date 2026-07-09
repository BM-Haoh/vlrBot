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
