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



from datetime import datetime


# 📘 Instruções e histórico
with st.expander("ℹ️ Instruções de uso e atualizações", expanded=True):
    st.markdown("""
    ### 🧪 Como usar este aplicativo

    1. **Selecione o método cromatográfico** utilizado na análise (coluna, rampa, etc.)
    2. **Digite o tempo de retenção observado** da substância suspeita.
    3. (Opcional) Informe até **3 fragmentos m/z (íons diagnóstico)** para refinar os resultados.
    4. O app listará substâncias compatíveis com o TR informado e calculará o **Índice de Retenção Linear (IRL)**.

    
    
    

    
    
    
    
    
    
    
    """)

# Carregar a planilha

# Selecionar método
metodo = st.selectbox("Selecione o método analítico", [
    "DB-1ms", "HP-5ms", "DB-5ms (SID)", "DB-5ms (MARGGIE)", "DB1-ms 4metros"
])

# Entrada de TR observado
tr_obs = st.number_input("Digite o tempo de retenção observado (min)", min_value=0.0, step=0.01, format="%.2f")

# Tolerância
tolerancia = st.slider("Tolerância de variação de TR (%)", 1, 10, 4)
tr_min = tr_obs * (1 - tolerancia / 100)
tr_max = tr_obs * (1 + tolerancia / 100)

# Entrada de fragmentos (opcional)
fragmentos_input = st.text_input("Fragmentos observados (ex: 91,105,119)")
fragmentos_obs = [f.strip() for f in fragmentos_input.split(",") if f.strip().isdigit()]
fragmentos_obs = list(map(int, fragmentos_obs))

# Carregar dados unificados

# Mapear coluna de RT conforme método
col_tr_por_metodo = {
    "DB-1ms": "RT_DB1ms",
    "HP-5ms": "RT_HP5ms",
    "DB-5ms (SID)": "RT_DB5ms_SID",
    "DB-5ms (MARGGIE)": "RT_DB5ms_MARGGIE",
    "DB1-ms 4metros": "RT_4m"
}
col_tr = col_tr_por_metodo.get(metodo)

# Filtro por TR
df_filtrados = df_triagem[df_triagem[col_tr].between(tr_min, tr_max)].copy()
df_filtrados["TR Selecionado"] = df_filtrados[col_tr]

# Filtro por fragmentos
def contem_todos_fragmentos(frag_str, fragmentos_necessarios):
    try:
        frag_lista = list(map(int, frag_str.split(",")))
        return all(f in frag_lista for f in fragmentos_necessarios)
    except:
        return False

if fragmentos_obs:
    df_filtrados = df_filtrados[df_filtrados["Fragmentos (m/z)"].apply(
        lambda x: contem_todos_fragmentos(x, fragmentos_obs)
    )]

# Layout lado a lado
col1, col2 = st.columns(2)

with col1:
    st.write(f"Mostrando substâncias com TR entre {tr_min:.2f} e {tr_max:.2f} minutos:")
    st.dataframe(df_filtrados[["Substância", "TR Selecionado", "Fragmentos (m/z)", "Observações"]])

with col2:
    st.subheader("Cálculo do IRL com base nos alcanos")
    df_ri = xls.parse("Alcanos")
    coluna_alcanos = col_tr  # mesmo nome da coluna de RT por método

    df_alcanos = df_ri[[coluna_alcanos, "n-Alcano"]].dropna()
    df_alcanos["RT"] = pd.to_numeric(df_alcanos[coluna_alcanos], errors="coerce")
    df_alcanos["n"] = df_alcanos["n-Alcano"]

    tr_subst = tr_obs
    linhas_validas = df_alcanos[df_alcanos["RT"] < tr_subst]

    if not linhas_validas.empty and len(df_alcanos) >= 2:
        idx_n = linhas_validas["RT"].idxmax()
        if idx_n + 1 < len(df_alcanos):
            RT_n = df_alcanos.at[idx_n, "RT"]
            RT_n1 = df_alcanos.at[idx_n + 1, "RT"]
            n = df_alcanos.at[idx_n, "n"]
            IRL_calc = 100 * (n + (tr_subst - RT_n) / (RT_n1 - RT_n))
            st.success(f"Índice de Retenção Linear calculado: **{IRL_calc:.2f}**")
        else:
            st.warning("RT informado está fora da faixa superior dos alcanos.")
    else:
        st.warning("Não foi possível calcular o IRL com os dados disponíveis.")

# Criar log de ações
def registrar_log(acao, detalhes):
    log_path = "log_acoes.csv"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = [now, acao, detalhes]

    if not os.path.exists(log_path):
        with open(log_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["DataHora", "Acao", "Detalhes"])
            writer.writerow(linha)
    else:
        with open(log_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(linha)

# Registrar consulta
registrar_log("Consulta", f"Método: {metodo}, TR: {tr_obs}, Fragmentos: {fragmentos_obs}, Tolerância: {tolerancia}%")