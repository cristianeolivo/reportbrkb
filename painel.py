import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import datetime
import os

# ==========================================================
# CONFIGURAÇÃO
# ==========================================================

st.set_page_config(page_title="Report Mensal Erbe - Jurídico", layout="wide")

# ==========================================================
# FUNÇÕES AUXILIARES
# ==========================================================

def verificar_arquivo(nome):

    if not os.path.exists(nome):
        st.error(f"Arquivo não encontrado: {nome}")
        st.stop()


def tratar_data(col):

    if pd.api.types.is_numeric_dtype(col):

        return pd.to_datetime(
            col,
            unit="D",
            origin="1899-12-30",
            errors="coerce"
        )

    return pd.to_datetime(col, errors="coerce", dayfirst=True)


def tratar_moeda(col):

    return pd.to_numeric(
        col.astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce"
    )


def padronizar_colunas(df):

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
    )

    return df

# ==========================================================
# HEADER
# ==========================================================

col_logo, col_titulo = st.columns([2,5])

with col_logo:

    if os.path.exists("logo.png"):
        logo = Image.open("logo.png")
        st.image(logo,width=450)

with col_titulo:
    st.title("Report Mensal Erbe - Jurídico")

st.divider()

# ==========================================================
# FILTRO PERÍODO
# ==========================================================

col1,col2,col3 = st.columns([2,2,1])

with col1:
    data_inicio = st.date_input("Data início", value=datetime.date(2024,1,1))

with col2:
    data_fim = st.date_input("Data fim", value=datetime.date.today())

with col3:
    st.write("")
    st.write("")
    st.button("Filtrar", use_container_width=True)

# ==========================================================
# CARREGAR BASES
# ==========================================================

@st.cache_data
def carregar_bases():

    verificar_arquivo("Entradas_Analise.xlsx")
    verificar_arquivo("SETTLED.xlsx")
    verificar_arquivo("relatorio_tratado.xlsx")

    entradas = pd.read_excel("Entradas_Analise.xlsx")
    settled = pd.read_excel("SETTLED.xlsx")
    relatorio = pd.read_excel("relatorio_tratado.xlsx")

    entradas = padronizar_colunas(entradas)
    settled = padronizar_colunas(settled)
    relatorio = padronizar_colunas(relatorio)

    return entradas, settled, relatorio

entradas, settled, relatorio = carregar_bases()

# ==========================================================
# TRATAMENTO DE DATAS
# ==========================================================

if "data cálculo" in entradas.columns:
    entradas["data cálculo"] = tratar_data(entradas["data cálculo"])

if "data cálculo" in settled.columns:
    settled["data cálculo"] = tratar_data(settled["data cálculo"])

# ==========================================================
# REMOVER DUPLICADOS
# ==========================================================

if "pasta" in entradas.columns:
    entradas = entradas.sort_values("data cálculo").drop_duplicates("pasta", keep="last")

if "pasta" in settled.columns:
    settled = settled.sort_values("data cálculo").drop_duplicates("pasta", keep="last")

if "pasta" in relatorio.columns:
    relatorio = relatorio.drop_duplicates("pasta")

# ==========================================================
# FILTRO DATA
# ==========================================================

entradas_filtrado = entradas[
(entradas["data cálculo"]>=pd.to_datetime(data_inicio)) &
(entradas["data cálculo"]<=pd.to_datetime(data_fim))
].copy()

settled_filtrado = settled[
(settled["data cálculo"]>=pd.to_datetime(data_inicio)) &
(settled["data cálculo"]<=pd.to_datetime(data_fim))
].copy()

# ==========================================================
# MÉTRICAS
# ==========================================================

entradas_total = entradas_filtrado["pasta"].count()

baixa_prov = settled_filtrado[
settled_filtrado["status"].astype(str).str.upper()=="BAIXA PROVISORIA"
]["pasta"].count()

encerrados = settled_filtrado[
settled_filtrado["status"].astype(str).str.upper()=="ENCERRADOS"
]["pasta"].count()

mes_atual = relatorio["pasta"].nunique()

col1,col2,col3,col4 = st.columns(4)

col1.metric("Entradas", entradas_total)
col2.metric("Baixa Provisória", baixa_prov)
col3.metric("Encerrados", encerrados)
col4.metric("Processos Atuais", mes_atual)

st.divider()

# ==========================================================
# GRÁFICO ENTRADAS
# ==========================================================

col_g1,col_g2 = st.columns(2)

with col_g1:

    st.subheader("Entradas do mês")

    if "macro assunto" in entradas_filtrado.columns:

        graf = entradas_filtrado.groupby("macro assunto")["pasta"].count().reset_index()

        if not graf.empty:

            fig = px.bar(
                graf,
                x="macro assunto",
                y="pasta",
                text="pasta"
            )

            st.plotly_chart(fig,use_container_width=True)

        else:
            st.info("Sem dados no período selecionado")

# ==========================================================
# GRÁFICO SAÍDAS
# ==========================================================

with col_g2:

    st.subheader("Saídas e Baixas")

    if {"status","macro encerramento"}.issubset(settled_filtrado.columns):

        saidas = settled_filtrado.groupby(
            ["status","macro encerramento"]
        )["pasta"].count().reset_index()

        if not saidas.empty:

            fig = px.bar(
                saidas,
                x="status",
                y="pasta",
                color="macro encerramento",
                barmode="stack"
            )

            st.plotly_chart(fig,use_container_width=True)

        else:
            st.info("Sem saídas no período")

st.divider()

# ==========================================================
# GRÁFICO ENTRADAS X SAÍDAS
# ==========================================================

st.subheader("Entradas x Saídas")

entradas_filtrado["mes"] = entradas_filtrado["data cálculo"].dt.month
settled_filtrado["mes"] = settled_filtrado["data cálculo"].dt.month

entradas_mes = entradas_filtrado.groupby("mes")["pasta"].count()
saidas_mes = settled_filtrado.groupby("mes")["pasta"].count()

meses = range(1,13)

fig = go.Figure()

fig.add_trace(go.Scatter(
x=list(meses),
y=[entradas_mes.get(m,0) for m in meses],
mode="lines+markers",
name="Entradas"
))

fig.add_trace(go.Scatter(
x=list(meses),
y=[saidas_mes.get(m,0) for m in meses],
mode="lines+markers",
name="Saídas"
))

fig.update_layout(
xaxis_title="Mês",
yaxis_title="Quantidade"
)

st.plotly_chart(fig,use_container_width=True)

st.divider()

# ==========================================================
# TABELA FINANCEIRA
# ==========================================================

st.subheader("Baixa provisória e encerrados")

dados = []

for status in ["won","settled","lost"]:

    df = settled_filtrado[
    settled_filtrado["macro encerramento"].astype(str).str.lower()==status
    ]

    qtd = df["pasta"].count()

    bp = tratar_moeda(df["valor pedido objeto corrigido"]).sum()

    fcx = tratar_moeda(df["valor integral do acordo/condenação"]).sum()

    saving = (bp-fcx)/bp if bp>0 else 0

    dados.append({
        "Status":status.title(),
        "Quantidade":qtd,
        "BP Atualizado":bp,
        "FCX Real":fcx,
        "Saving":saving
    })

df_tabela = pd.DataFrame(dados)

bp_total = df_tabela["BP Atualizado"].sum()
fcx_total = df_tabela["FCX Real"].sum()

total = {
"Status":"Total",
"Quantidade":df_tabela["Quantidade"].sum(),
"BP Atualizado":bp_total,
"FCX Real":fcx_total,
"Saving":(bp_total-fcx_total)/bp_total if bp_total>0 else 0
}

df_tabela = pd.concat([df_tabela,pd.DataFrame([total])])

def format_moeda(v):
    return f"R$ {v/1000000:.2f}M"

def format_percent(v):
    return f"{v*100:.1f}%"

df_tabela["BP Atualizado"] = df_tabela["BP Atualizado"].apply(format_moeda)
df_tabela["FCX Real"] = df_tabela["FCX Real"].apply(format_moeda)
df_tabela["Saving"] = df_tabela["Saving"].apply(format_percent)

st.dataframe(df_tabela,use_container_width=True)

# ==========================================================
# ASSUMPTIONS
# ==========================================================

st.divider()
st.subheader("Assumptions")

if os.path.exists("assumptions_26.xlsx"):

    assumptions = pd.read_excel("assumptions_26.xlsx")

    assumptions.columns = assumptions.columns.astype(str).str.strip()

    st.dataframe(assumptions,use_container_width=True)

else:

    st.info("Arquivo assumptions_26.xlsx não encontrado.")