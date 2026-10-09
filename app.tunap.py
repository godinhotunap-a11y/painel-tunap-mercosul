import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime

# Configuração da página (otimizada para mobile/desktop)
st.set_page_config(
    page_title="TUNAP | Campanha Mercosul",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="auto"
)

# -----------------------------------------------------------------------------
# Estilização CSS Customizada para Mobile (Responsividade e Tabelas)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-size: 16px;
    }
    .table-responsive {
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        margin-bottom: 1rem;
    }
    table.table {
        width: 100%;
        max-width: 100%;
        background-color: transparent;
        white-space: nowrap;
        font-size: 14px;
    }
    table.table th, table.table td {
        padding: 8px 12px;
        text-align: center;
        border-top: 1px solid #dee2e6;
    }
    table.table th {
        background-color: #f8f9fa;
        font-weight: bold;
    }
    .kpi-card {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0
