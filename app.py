
import streamlit as st
import pandas as pd
from datetime import datetime
import csv
import os

st.set_page_config(page_title="Identificação por IRL", layout="wide")

# -----------------------------
# 🔍 Busca por nome de substância
# -----------------------------
st.subheader("🔍 Buscar substância pelo nome")

busca = st.text_input("Digite parte do nome da substância").strip().lower()

# Carregar a planilha
xls = pd.ExcelFile("PLANILHA_IRL.xlsx")
df_triagem = xls.parse("Substâncias")

if busca:
    resultados = df_triagem[df_triagem["Substância"].str.lower().str.contains(busca)]
    if not resultados.empty:
        st.write(f"Resultados encontrados: {len(resultados)}")
        st.dataframe(resultados[[
            "Substância", "IRL_DB1ms", "IRL_HP5ms", "IRL_DB5ms_SID", "IRL_DB5ms_MARGGIE", "IRL_4m",
            "RT_DB1ms", "RT_HP5ms", "RT_DB5ms_SID", "RT_DB5ms_MARGGIE", "RT_4m",
            "Fragmentos (m/z)", "Observações"
        ]])
    else:
        st.warning("Nenhuma substância encontrada com esse nome.")

# (continuação omitida aqui, mas incluída no deploy real)
