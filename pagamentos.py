import streamlit as st
import pandas as pd
import plotly.express as px

# ===============================
# CONFIG
# ===============================
st.set_page_config(page_title="Report Mensal Erbe - Jurídico - Pagamentos", layout="wide")

# --- INJEÇÃO DE ESTILO PARA FONTE GLOBAL ---
st.markdown("""
    <style>
    /* Aumenta a fonte base do corpo do app */
    html, body, [class*="ViewContainer"] {
        font-size: 1.15rem; 
    }

    /* Aumenta especificamente o texto das tabelas e dataframes */
    .stTable, .stDataFrame td, .stDataFrame th {
        font-size: 18px !important;
    }

    /* Títulos e Subtítulos */
    h1 { font-size: 2.8rem !important; }
    h2 { font-size: 2.2rem !important; }
    h3 { font-size: 1.8rem !important; }

    /* Texto da Sidebar */
    section[data-testid="stSidebar"] .stMarkdown p {
        font-size: 1.2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
st.title("Pagamentos")
DATA_INICIO = pd.to_datetime("2025-08-26")
DATA_FIM = pd.to_datetime("2026-08-25")

def filtrar_vencimento(df):
    df["VencLíquid"] = pd.to_datetime(df["VencLíquid"], errors="coerce")
    
    return df[df["VencLíquid"].between(DATA_INICIO, DATA_FIM)]

df = pd.read_excel("Pagamentos_atualizado.xlsx")
df = filtrar_vencimento(df)

df["Valor Restante"] = pd.to_numeric(
    df["Valor Restante"].astype(str).str.replace(",", "."),
    errors="coerce"
)

df["Valor do Lançamento"] = pd.to_numeric(
    df["Valor do Lançamento"].astype(str).str.replace(",", "."),
    errors="coerce"
)
def formatar_valor(valor):
    if valor >= 1_000_000:
        return f"R$ {valor / 1_000_000:.2f} M".replace(".", ",")
    elif valor >= 1_000:
        return f"R$ {valor / 1_000:.1f} mil".replace(".", ",")
    else:
        return f"R$ {valor:.2f}".replace(".", ",")

# 2. Calcular as somas (KPIs)
valor_restante_total = df["Valor Restante"].sum()
valor_lancamento_total = df["Valor do Lançamento"].sum()

if valor_lancamento_total > 0:
    percentual = ((valor_lancamento_total-valor_restante_total) / valor_lancamento_total) * 100
else:
    percentual = 0.0

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Pago", formatar_valor(valor_lancamento_total-valor_restante_total))

with col2:
    st.metric("Saldo Pendente", formatar_valor(valor_restante_total))

with col3:
    st.metric("Execução", f"{percentual:.2f}%".replace(".", ","))
# Pizza
status_counts = df["Pagamento"].value_counts()

fig = px.pie(
    values=status_counts.values,
    names=status_counts.index,
    title="Proporção de Pagamentos"
)
fig.update_layout(
    height=500, # Aumente este valor (ex: 600, 700) para deixar a pizza maior
    margin=dict(t=50, b=20, l=20, r=20) # Reduz as margens em branco ao redor do gráfico
)

st.plotly_chart(fig, use_container_width=True)

mapeamento_naturezas = {
    "-": "Cível",
    "Administrativo": "Cível",
    "Cível": "Cível",
    "Cível - Estratégico": "Cível",
    
    "Administrativo - Trabalhista": "Trabalhista",
    "Trabalhista": "Trabalhista",
    
    "Tributário": "Tributário",
    "Administrativo - Tributário": "Tributário"
}


df["Nova Natureza"] = df["Natureza"].map(mapeamento_naturezas).fillna(df["Natureza"])
df_agrupado = df.groupby("Nova Natureza")[["Valor do Lançamento", "Valor Restante"]].sum().reset_index()
df_agrupado = df_agrupado.rename(columns={
    "Valor do Lançamento": "Total",
    "Valor Restante": "Pendente"
})
df_agrupado["Pago"] = df_agrupado["Total"] - df_agrupado["Pendente"]
st.subheader("Valores Por Natureza ")
fig = px.bar(
    df_agrupado, 
    x="Nova Natureza", # <--- Mudamos o eixo X para a nova coluna
    y=["Pago", "Pendente"],
    title="Soma de Valores por Nova Natureza",
    labels={"value": "Valor (R$)", "variable": "Tipo de Valor", "Nova Natureza": "Natureza"},
    barmode="group",
    text_auto='.2s',
    log_y=True
)

fig.update_traces(textfont_size=12, textangle=0, textposition="outside")

st.plotly_chart(fig, use_container_width=True)


df["VencLíquid"] = pd.to_datetime(
    df["VencLíquid"],
    errors="coerce"
)

df["Data_Fiscal"] = (
    df["VencLíquid"]
    - pd.Timedelta(days=25)
    + pd.DateOffset(months=1)
)

df["Periodo_Ordenacao"] = (
    df["Data_Fiscal"]
    .dt.to_period("M")
)

# --------------------------------------------------
# TIMELINE BASE
# --------------------------------------------------

df_timeline = (
    df.groupby("Periodo_Ordenacao")[
        ["Valor do Lançamento", "Valor Restante"]
    ]
    .sum()
    .reset_index()
)

df_timeline = df_timeline.sort_values(
    "Periodo_Ordenacao"
)

meses_pt = {
    1: 'JAN',
    2: 'FEV',
    3: 'MAR',
    4: 'ABR',
    5: 'MAI',
    6: 'JUN',
    7: 'JUL',
    8: 'AGO',
    9: 'SET',
    10: 'OUT',
    11: 'NOV',
    12: 'DEZ'
}

df_timeline["Mês_Exibicao"] = (
    df_timeline["Periodo_Ordenacao"]
    .dt.month.map(meses_pt)
    + "/"
    + df_timeline["Periodo_Ordenacao"]
    .dt.year.astype(str)
    .str[-2:]
)

df_timeline = df_timeline.rename(columns={
    "Valor do Lançamento": "Total",
    "Valor Restante": "Pendente"
})

df_timeline["Pendente"] = (
    df_timeline["Pendente"]
    .fillna(0)
)

df_timeline["Total"] = (
    df_timeline["Total"]
    .fillna(0)
)

df_timeline["Pago"] = (
    df_timeline["Total"]
    - df_timeline["Pendente"]
)

# --------------------------------------------------
# MELT
# --------------------------------------------------

df_melt = df_timeline.melt(
    id_vars=[
        "Periodo_Ordenacao",
        "Mês_Exibicao"
    ],

    value_vars=[
        "Pago",
        "Pendente"
    ],

    var_name="Tipo",
    value_name="Valor"
)

# --------------------------------------------------
# CLASSIFICAÇÃO
# --------------------------------------------------

def classificar_eixo(row):

    p = row["Periodo_Ordenacao"]
    tipo = row["Tipo"]

    # ----------------------------
    # PENDENTES
    # ----------------------------

    if tipo == "Pendente":

        # Somente >= 2026
        if p.year >= 2026:
            return row["Mês_Exibicao"], p

        else:
            return "REMOVER", p

    # ----------------------------
    # PAGOS FIXOS
    # ----------------------------

    elif tipo == "Pago" and p.year in [2022, 2023]:
        return "2022-2023", pd.Period("1900-01", "M")

    elif tipo == "Pago" and p.year == 2024:
        return "2024", pd.Period("1900-02", "M")

    elif tipo == "Pago" and p.year == 2025:
        return "2025", pd.Period("1900-03", "M")

    # ----------------------------
    # PAGOS >= 2026
    # ----------------------------

    elif tipo == "Pago" and p.year >= 2026:
        return "Pagos (≥ JAN/26)", pd.Period("1900-04", "M")

    else:
        return "REMOVER", p

df_melt[["Eixo_X", "Periodo_Sort"]] = df_melt.apply(
    classificar_eixo,
    axis=1,
    result_type="expand"
)

# --------------------------------------------------
# AGRUPAMENTO
# --------------------------------------------------

df_plot = (
    df_melt.groupby(
        ["Eixo_X", "Tipo", "Periodo_Sort"]
    )["Valor"]
    .sum()
    .reset_index()
)

# --------------------------------------------------
# REMOVE LIXO
# --------------------------------------------------

df_plot = df_plot[
    df_plot["Eixo_X"] != "REMOVER"
]

# --------------------------------------------------
# REMOVE FIXOS ORIGINAIS
# --------------------------------------------------

df_plot = df_plot[
    ~(
        (df_plot["Tipo"] == "Pago")
        &
        (
            df_plot["Eixo_X"].isin([
                "2022-2023",
                "2024",
                "2025"
            ])
        )
    )
]

# --------------------------------------------------
# ADICIONA FIXOS
# --------------------------------------------------

fixos = pd.DataFrame({

    "Eixo_X": [
        "2022-2023",
        "2024",
        "2025"
    ],

    "Tipo": [
        "Pago",
        "Pago",
        "Pago"
    ],

    "Periodo_Sort": [
        pd.Period("1900-01", "M"),
        pd.Period("1900-02", "M"),
        pd.Period("1900-03", "M")
    ],

    "Valor": [                       #ALTERE AQUI
        210000000,
        210000000,
        210000000
    ]
})

df_plot = pd.concat(
    [df_plot, fixos],
    ignore_index=True
)

# --------------------------------------------------
# REMOVE ZEROS
# --------------------------------------------------

df_plot = df_plot[
    df_plot["Valor"] > 0
]

# --------------------------------------------------
# REMOVE MESES TOTALMENTE PAGOS
# --------------------------------------------------

# identifica quais eixos possuem pendência
meses_com_pendente = set(
    df_plot.loc[
        df_plot["Tipo"] == "Pendente",
        "Eixo_X"
    ]
)

# mantém:
# - tudo que tem pendente
# - fixos
# - barra agregada
df_plot = df_plot[
    (
        df_plot["Eixo_X"].isin(meses_com_pendente)
    )
    |
    (
        df_plot["Eixo_X"].isin([
            "2022-2023",
            "2024",
            "2025",
            "Pagos (≥ JAN/26)"
        ])
    )
]

# --------------------------------------------------
# ORDENAÇÃO
# --------------------------------------------------

# --------------------------------------------------
# ORDEM DINÂMICA DO EIXO X
# --------------------------------------------------

ordem_base = [
    "2022-2023",
    "2024",
    "2025",
    "Pagos (≥ JAN/26)",
    "JAN/26",
    "FEV/26",
    "MAR/26",
    "ABR/26",
    "MAI/26",
    "JUN/26",
    "JUL/26",
    "AGO/26"
]

# mantém somente categorias existentes
ordem_eixo_x = [
    item
    for item in ordem_base
    if item in df_plot["Eixo_X"].unique()
]
# --------------------------------------------------
# GRÁFICO
# --------------------------------------------------

st.subheader(
    "Evolução Financeira da Carteira"
)

st.caption(
    "Acompanhamento de pagamentos realizados e pendentes (Ciclo 26 a 25)"
)

cores_customizadas = {
    "Pago": "#0A2463",
    "Pendente": "#BBD1EA"
}

fig = px.bar(
    df_plot,
    x="Eixo_X",
    y="Valor",
    color="Tipo",
    barmode="group",
    color_discrete_map=cores_customizadas,
    text_auto=".2s",
)

fig.update_layout(

    xaxis_title="",
    yaxis_title="Valor (R$)",
    legend_title="",

    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.2,
        xanchor="center",
        x=0.5
    ),

    plot_bgcolor="rgba(0,0,0,0)",
)

fig.update_xaxes(
    categoryorder="array",
    categoryarray=ordem_eixo_x
)

fig.update_traces(
    textfont_size=12,
    textangle=0,
    textposition="outside"
)

st.plotly_chart(
    fig,
    use_container_width=True
)