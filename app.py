import streamlit as st
import streamlit_authenticator as stauth
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import datetime
import os

# ============================================================
# CONFIG GERAL (unificado - roda uma única vez para todo o app)
# ============================================================
st.set_page_config(page_title="Report Mensal Erbe - Jurídico", layout="wide")

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

# ============================================================
# LOGIN (unificado - antes existia um login separado em
# aplicativo.py e outro em PAINEL_FINAL_ATT.py; agora é um só)
# ============================================================
credentials = {
    "usernames": {
        "ControladoriaErbe": {
            "name": "ControladoriaErbe",
            "password": "Erbe@3009"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "meu_app_unificado",
    "abc123",
    cookie_expiry_days=1
)

authenticator.login()

authentication_status = st.session_state.get("authentication_status")
name = st.session_state.get("name")
username = st.session_state.get("username")


# ============================================================
# PAINEL 1 — Painel Jurídico (ex.: aplicativo.py)
# Overview / Claims por Ano / New Claims / Resolved
# ============================================================
def painel_juridico():

    # =========================
    # ESTILO
    # =========================
    st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # =========================
    # CORES
    # =========================
    COLORS = {
        "blue_dark": "#0B3C5D",
        "blue_light": "#BFD7EA",
        "blue_medium": "#328CC1",
        "gray": "#A9A9A9",
        "green": "#5CB85C",
        "red": "#D9534F",
        "magenta": "#C2185B"
    }

    labels_macro = ["FAR", "Cível", "Property Tax", "Labor", "Tax"]

    pagina = st.sidebar.radio("Navegação - Painel Jurídico", [
        "Overview",
        "Claims por Ano",
        "New Claims",
        "Resolved"
    ])

    # =========================
    # FUNÇÃO DONUT
    # =========================
    def donut(values, title, total):
        fig = go.Figure(data=[go.Pie(
            labels=labels_macro,
            values=values,
            hole=0.7,
            marker_colors=[
                COLORS["blue_dark"],
                COLORS["blue_medium"],
                COLORS["magenta"],
                COLORS["gray"],
                COLORS["blue_light"]
            ],
            textinfo='percent',
            texttemplate='%{percent:.2%}'
        )])

        fig.update_layout(
            title=dict(text=title, x=0.5),
            annotations=[dict(text=f"<b>{total}</b>", x=0.5, y=0.5, showarrow=False)],
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
            plot_bgcolor="white"
        )

        return fig

    # =========================
    # FUNÇÃO LABEL
    # =========================
    def add_labels(fig, x_vals, y_vals, color):

        texts = []

        for i in range(len(y_vals)):

            if y_vals[i] >= 11:
                texts.append(str(y_vals[i]))

            else:
                texts.append("")

                if y_vals[i] > 0:

                    fig.add_annotation(
                        x=x_vals[i],
                        y=y_vals[i],
                        text=str(y_vals[i]),
                        showarrow=False,
                        xshift=-25,
                        font=dict(color=color, size=11)
                    )

        return texts

    # =========================
    # PAGE 1 — OVERVIEW
    # =========================
    if pagina == "Overview":

        df = pd.read_excel("BASE_UNIFICADA.xlsx")
        df = df.drop_duplicates(subset="Pasta")
        df_assu = pd.read_excel("assumptions_26_slides.xlsx")
        values = [
            (df_assu.iloc[2,1]/1000000).round(2),
            (-df_assu.iloc[3,1]/1000000).round(2),
            (-df_assu.iloc[4,1]/1000000).round(2),
            (df_assu.iloc[5,1]/1000000).round(2),
            (df_assu.iloc[6,1]/1000000).round(2),
            (df_assu.iloc[7,1]/1000000).round(2),
            (df_assu.iloc[8,1]/1000000).round(2)
        ]
        st.title("Erbe Update")

        claims_macro = df.groupby("Macro Assunto").size()

        # TOTAL LOSS vindo da outra tabela
        total_loss = (df_assu.iloc[8,1] / 1000000).round(2)

        total_claims = len(df)

        # -----------------------------
        # proporção fixa por macro assunto
        # (exemplo - ajuste para o seu caso)
        # -----------------------------

        proporcao_macro = {
            "FAR": 0.09,
            "Cível": 0.77,
            "IPTU Customer": 0.01,
            "Tax": 0.11,
            "Labor": 0.02
        }

        # gera os valores proporcionais
        loss_macro_prop = pd.Series(proporcao_macro) * total_loss

        # garante ordem igual ao gráfico
        loss_macro_prop = loss_macro_prop.reindex(labels_macro, fill_value=0)

        col1, col2 = st.columns(2)

        with col1:

            st.plotly_chart(
                donut(
                    claims_macro.reindex(labels_macro, fill_value=0).values,
                    "Total Claims",
                    total_claims
                ),
                use_container_width=True
            )

        with col2:

            st.plotly_chart(
            donut(
            loss_macro_prop.values,
            "Expected Loss",
            total_loss
        ),
        use_container_width=True
    )

        st.markdown("<br>", unsafe_allow_html=True)

        df_assu = pd.read_excel("assumptions_26_slides.xlsx")

        values = [
            (df_assu.iloc[2,1]/1000000).round(2),
            (-df_assu.iloc[3,1]/1000000).round(2),
            (-df_assu.iloc[4,1]/1000000).round(2),
            (df_assu.iloc[5,1]/1000000).round(2),
            (df_assu.iloc[6,1]/1000000).round(2),
            (df_assu.iloc[7,1]/1000000).round(2),
            (df_assu.iloc[8,1]/1000000).round(2)
        ]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=["Dez25","Resolved","Savings","Revised","Subtotal","New","Total"],
            y=values,
            marker_color=[
                COLORS["gray"], COLORS["red"], COLORS["green"],
                COLORS["blue_medium"], COLORS["gray"],
                COLORS["magenta"], COLORS["blue_dark"]
            ],
            text=values,
            textposition="outside"
        ))

        fig.update_layout(plot_bgcolor="white", height=350)

        st.plotly_chart(fig, use_container_width=True)

        col3, col4 = st.columns([2,1])

        with col3:
            valor1 = ((df_assu.iloc[2,1]/1000000).round(2))
            valor3 = ((df["Valor Pedido Objeto Corrigido"].sum()/1000000).round(2))
            vals = [valor1, (valor3 - valor1).round(2), valor3]

            fig2 = go.Figure()

            fig2.add_trace(go.Bar(
                x=["Total","Carrying","Updated"],
                y=vals,
                marker_color=[COLORS["gray"], COLORS["blue_medium"], COLORS["green"]],
                text=vals,
                textposition="outside"
            ))

            fig2.update_layout(plot_bgcolor="white", height=300)

            st.plotly_chart(fig2, use_container_width=True)

        with col4:

            st.table(pd.DataFrame({
                "Subject":["Civil","Tax","Labor","Construction"],
                "Rate":["TJ+1%","Selic","TST+1%","INCC"],
                "12M":["16.8%","14.5%","16.8%","5.8%"]
            }))

    # =========================
    # PAGE 2 — CLAIMS
    # =========================
    elif pagina == "Claims por Ano":

        st.title("New Claims Filled per Year")

        df = pd.read_excel("RELATORIO_FILTRADO.xlsx")

        df = df.drop_duplicates(subset="Pasta")

        df["Data de cadastro"] = pd.to_datetime(df["Data de cadastro"], dayfirst=True, errors="coerce")
        df["Data de Encerramento"] = pd.to_datetime(df["Data de Encerramento"], dayfirst=True, errors="coerce")

        ativos_2026 = df[
            (df["Data de cadastro"].dt.year == 2026) &
            (df["Status"] == "ATIVOS")
        ].shape[0]

        encerrados_2026 = df[
            (df["Data de cadastro"].dt.year == 2026) &
            (df["Data de Encerramento"].dt.year == 2026)
        ].shape[0]

        anos = ["2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022","2023","2024","2025","2026"]

        ativos = [80,34,92,159,261,200,630,261,641,1739,523,339,305,452,ativos_2026]

        encerrados = [7952,5966,7590,7987,7314,4810,2782,1873,1078,2475,638,483,236,74,encerrados_2026]

        df_bp = pd.read_excel("POS_BP.xlsx")

        df_bp["Data de cadastro"] = pd.to_datetime(df_bp["Data de cadastro"], dayfirst=True, errors="coerce")

        total_risk_2026 = df_bp["Valor Pedido Atualizado"].sum()
        expected_loss_2026 = df_bp["Valor Pedido.1"].sum()
        total_risk_2026 = (total_risk_2026/1000000).round(2)
        expected_loss_2026 = (expected_loss_2026/1000000).round(2)

        st.table(pd.DataFrame({
            "Métrica":["Total Risk","Expected Loss"],
            "≤2012":[144.2,33.3],"2013":[47.7,7],"2014":[24.2,16.6],"2015":[87.4,31.9],
            "2016":[199.2,69.6],"2017":[194.4,65.9],"2018":[190.9,94.6],"2019":[87.8,40.8],
            "2020":[226,93.2],"2021":[191.6,59.7],"2022":[211.3,20.8],"2023":[136.3,50.6],
            "2024":[46.6,18.3],"2025":[55.3,28.7],
            "2026":[total_risk_2026,expected_loss_2026]
        }))

        fig = go.Figure()

        text_resolved = add_labels(fig, anos, encerrados, COLORS["blue_light"])
        text_active = add_labels(fig, anos, ativos, COLORS["blue_dark"])

        fig.add_trace(go.Bar(
            x=anos, y=encerrados,
            name="Resolved",
            marker_color=COLORS["blue_light"],
            text=text_resolved,
            textposition="inside"
        ))

        fig.add_trace(go.Bar(
            x=anos, y=ativos,
            name="Active",
            marker_color=COLORS["blue_dark"],
            text=text_active,
            textposition="inside"
        ))

        totals = [a+b for a,b in zip(ativos,encerrados)]

        for i in range(len(anos)):

            fig.add_annotation(
                x=anos[i],
                y=totals[i]*1.05,
                text=str(totals[i]),
                showarrow=False
            )

        fig.update_layout(barmode="stack", plot_bgcolor="white", height=450)

        st.plotly_chart(fig, use_container_width=True)

    # =========================
    # PAGE 3 — NEW CLAIMS (CORRIGIDO)
    # =========================
    elif pagina == "New Claims":
        df_bp = pd.read_excel("POS_BP.xlsx")
        df_bp["Data de cadastro"] = pd.to_datetime(df_bp["Data de cadastro"], dayfirst=True, errors="coerce")
        
        st.title("New Claims")
        
        # --- CÁLCULOS DO GRÁFICO SUPERIOR ---
        acumulado_new_claims = df_bp["Valor Pedido.1"].sum()
        acumulado_new_claims = (acumulado_new_claims/1000000).round(2)
        values_top = [54.4, 9.2, acumulado_new_claims] 

        fig_top = go.Figure()
        fig_top.add_trace(go.Bar(
            x=["Budget","Forecast","Actual"],
            y=values_top,
            marker_color=[COLORS["magenta"], COLORS["blue_medium"], COLORS["blue_light"]],
            text=values_top,
            textposition="outside"
        ))
        
        # Linha pontilhada e porcentagem
        perc = (values_top[2]/values_top[1] - 1)*100
        fig_top.add_shape(type="line", x0=1, y0=values_top[1], x1=2, y1=values_top[2],
                          line=dict(color="black", width=2, dash="dot"))
        fig_top.add_annotation(x=1.5, y=(values_top[1]+values_top[2])/2, text=f"{perc:.2f}%", showarrow=False, yshift=10)
        
        st.plotly_chart(fig_top, use_container_width=True)

        # --- PROCESSAMENTO POR NATUREZA ---
        df_bp["Macro Assunto"] = df_bp["Macro Assunto"].fillna("Demais").astype(str).str.strip()
        df_bp["Macro Assunto"] = df_bp["Macro Assunto"].replace(["", "nan", "None"], "Demais")

        tipos_base = ["Cível", "Property Tax", "Labor", "Delay", "FAR", "Construction", "Tax", "Demais"]
        
        # Realiza os agrupamentos
        total_risk = df_bp.groupby("Macro Assunto")["Valor Pedido Atualizado"].sum() / 1000000
        expected_loss = df_bp.groupby("Macro Assunto")["Valor Pedido.1"].sum() / 1000000
        quantidade = df_bp.groupby("Macro Assunto").size()

        # Reindexa para garantir a ordem e preenche vazios com 0
        tr_vals = total_risk.reindex(tipos_base, fill_value=0).round(2).tolist()
        el_vals = expected_loss.reindex(tipos_base, fill_value=0).round(2).tolist()
        qt_vals = quantidade.reindex(tipos_base, fill_value=0).tolist()

        # Adiciona o Total
        tipos = tipos_base + ["Total"]
        tr_vals.append(round(sum(tr_vals), 2))
        el_vals.append(round(sum(el_vals), 2))
        qt_vals.append(sum(qt_vals))

        st.write("### New Claims by Nature")

        # --- CRIAÇÃO DA TABELA ALINHADA COM RÓTULOS ---
        # Definimos as colunas: a primeira para os rótulos, as outras para os dados
        col_label, *col_dat = st.columns([1.5] + [1] * len(tipos))

        # LINHA 1: Cabeçalhos
        with col_label:
            st.write("") 
        for i, col in enumerate(col_dat):
            with col:
                st.markdown(f"<div style='text-align: center'><b>{tipos[i]}</b></div>", unsafe_allow_html=True)
        
        st.divider()

        # LINHA 2: Total Risk
        with col_label:
            st.markdown("<div style='padding: 5px 0;'><b>Total Risk</b></div>", unsafe_allow_html=True)
        for i, col in enumerate(col_dat):
            with col:
                st.markdown(f"<div style='text-align: center; color: gray;'>{tr_vals[i]}</div>", unsafe_allow_html=True)

        st.divider()

        # LINHA 3: Expected Loss
        with col_label:
            st.markdown("<div style='padding: 5px 0;'><b>Expected Loss</b></div>", unsafe_allow_html=True)
        for i, col in enumerate(col_dat):
            with col:
                st.markdown(f"<div style='text-align: center; font-weight: bold;'>{el_vals[i]}</div>", unsafe_allow_html=True)

        st.divider()

        # LINHA 4: Gráficos de Barras
        with col_label:
            st.markdown("<br><br><b>Number of<br>Claims</b>", unsafe_allow_html=True)
        for i, col in enumerate(col_dat):
            with col:
                fig_mini = go.Figure(go.Bar(
                    x=[tipos[i]], 
                    y=[qt_vals[i]],
                    marker_color=COLORS["blue_dark"],
                    text=[qt_vals[i]],
                    textposition="outside"
                ))
                
                fig_mini.update_layout(
                    height=180, 
                    margin=dict(l=5, r=5, t=30, b=0),
                    yaxis=dict(visible=False, range=[0, max(qt_vals) * 1.3]),
                    xaxis=dict(visible=False),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_mini, use_container_width=True, config={'displayModeBar': False})
    # =========================
    # PAGE 4 — RESOLVED
    # =========================
    elif pagina == "Resolved":

        st.title("Finally Resolved Claims")

        tipos = ["Cível","Property Tax","Labor","Delay","FAR","Construction","Tax"]
        tipos_total = tipos + ["Total"]

        # =========================
        # CARREGAR BASE
        # =========================
        df_set = pd.read_excel("SETTLED_ACUMULADO.xlsx")

        # =========================
        # REMOVER DUPLICADOS
        # =========================
        df_set = (
            df_set
            .sort_values("Soma_Valor_Lancamento", ascending=False)
            .drop_duplicates(subset="Pasta")
        )

        # =========================
        # TABELA
        # =========================
        total_risk = df_set.groupby("Macro Assunto")["Valor Pedido Atualizado"].sum()
        expected_loss = df_set.groupby("Macro Assunto")["Valor Pedido Objeto Corrigido"].sum()
        disbursement = df_set.groupby("Macro Assunto")["Soma_Valor_Lancamento"].sum()
        total_risk = (total_risk/1000000).round(2)
        expected_loss = (expected_loss/1000000).round(2)
        disbursement = (disbursement/1000000).round(2)
        tabela = pd.DataFrame({
            "Métrica": ["Total Risk","Expected Loss","Disbursement"]
        })

        for tipo in tipos:
            tabela[tipo] = [
                total_risk.get(tipo,0),
                expected_loss.get(tipo,0),
                disbursement.get(tipo,0)
            ]

        # adicionar TOTAL na tabela
        tabela["Total"] = tabela[tipos].sum(axis=1)

        st.table(tabela)

        # =========================
        # GRÁFICO
        # =========================

        contagem = (
            df_set
            .groupby(["Macro Assunto","Macro encerramento"])
            .size()
            .unstack(fill_value=0)
        )

        settlement = contagem.get("Settled", pd.Series(0,index=tipos)).reindex(tipos, fill_value=0)
        lost = contagem.get("Lost", pd.Series(0,index=tipos)).reindex(tipos, fill_value=0)
        won = contagem.get("Won", pd.Series(0,index=tipos)).reindex(tipos, fill_value=0)

        # adicionar TOTAL ao gráfico
        settlement = settlement.tolist() + [settlement.sum()]
        lost = lost.tolist() + [lost.sum()]
        won = won.tolist() + [won.sum()]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=tipos_total,
            y=settlement,
            name="Settlement",
            marker_color=COLORS["red"]
        ))

        fig.add_trace(go.Bar(
            x=tipos_total,
            y=lost,
            name="Lost",
            marker_color=COLORS["blue_dark"]
        ))

        fig.add_trace(go.Bar(
            x=tipos_total,
            y=won,
            name="Won",
            marker_color=COLORS["blue_light"]
        ))

        totals = [s+l+w for s,l,w in zip(settlement,lost,won)]

        for i in range(len(tipos_total)):

            fig.add_annotation(
                x=tipos_total[i],
                y=totals[i]*1.08,
                text=str(int(totals[i])),
                showarrow=False
            )

        fig.update_layout(
            barmode="stack",
            plot_bgcolor="white",
            height=450
        )

        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# PAINEL 2 — Dashboard de Processos (ex.: PAINEL_FINAL_ATT.py)
# ============================================================
def painel_dashboard_processos():

    st.title("Dashboard de Processos")

    # ===============================
    # LOADS
    # ===============================
    @st.cache_data
    def load_base():
        df = pd.read_excel("BASE_UNIFICADA.xlsx")
        df.columns = df.columns.str.strip()
        return df

    @st.cache_data
    def load_relatorio():
        df = pd.read_excel("RELATORIO_FILTRADO.xlsx")
        df.columns = df.columns.str.strip()
        return df

    @st.cache_data
    def load_entradas():
        df = pd.read_excel("ENTRADAS.xlsx")
        df.columns = df.columns.str.strip().str.lower()
        return df

    @st.cache_data
    def load_settled():
        df = pd.read_excel("SETTLED_MENSAL.xlsx")
        df.columns = df.columns.str.strip().str.lower()
        return df

    df_base = load_base()
    df = load_relatorio()
    df_entradas = load_entradas()
    df_settled = load_settled()

    # ===============================
    # TRATAMENTO
    # ===============================
    df_base = df_base.drop_duplicates(subset="Pasta")

    df_entradas["data de cadastro"] = pd.to_datetime(
        df_entradas["data de cadastro"], errors="coerce"
    )

    for c in ["Data de cadastro", "Data de Encerramento"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    # ===============================
    # SELEÇÃO DO MÊS DE FECHAMENTO (MANUAL)
    # ===============================
    st.sidebar.header("Configurações de Fechamento")
    
    lista_meses = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    
    mes_nome = st.sidebar.selectbox("Selecione o mês de referência", lista_meses, index=2) # Index 2 = Março
    ano_ref = st.sidebar.number_input("Ano", min_value=2020, max_value=2030, value=2026)

    # Converter o nome do mês em número (Janeiro = 1, etc)
    mes_numero = lista_meses.index(mes_nome) + 1

    # Definir a data de "fim" (25 do mês selecionado)
    fim = pd.Timestamp(year=ano_ref, month=mes_numero, day=25)

    # Definir a data de "início" (26 do mês anterior)
    mes_anterior_dt = fim - pd.DateOffset(months=1)
    ini = pd.Timestamp(year=mes_anterior_dt.year, month=mes_anterior_dt.month, day=26)

    # Nome que será usado nos títulos (Ex: Março/26)
    mes_fechamento_nome = f"{mes_nome}/{str(ano_ref)[2:]}"

    st.sidebar.success(f"Período ativo: {ini.date()} a {fim.date()}")

    # ===============================
    # 1. IDENTIFICAÇÃO DINÂMICA DE COLUNAS (PARA EVITAR KEYERROR)
    # ===============================

    # Localiza a coluna de "Baixado Antes" independente de maiúsculas/minúsculas ou espaços
    col_baixado = [c for c in df_settled.columns if c.strip().upper() == "FOI BAIXADO ANTES"]
    col_status = [c for c in df_settled.columns if c.strip().upper() == "STATUS"]

    if not col_baixado or not col_status:
        st.error(f"Colunas não encontradas! Colunas disponíveis: {list(df_settled.columns)}")
        st.stop()

    nome_col_baixado = col_baixado[0]
    nome_col_status = col_status[0]

    # ===============================
    # 2. KPIs E CÁLCULOS
    # ===============================
    ativos = len(df_base)

    entradas_mes = len(df_entradas[
        (df_entradas["data de cadastro"] >= ini) & 
        (df_entradas["data de cadastro"] <= fim)
    ])

    # Criamos cópias temporárias normalizadas para os filtros
    status_series = df_settled[nome_col_status].astype(str).str.upper().str.strip()
    baixado_series = df_settled[nome_col_baixado].astype(str).str.upper().str.strip()

    # Filtramos quem encerrou no período
    mask_encerrados = (status_series == "ENCERRADOS")
    encerrados_mes = len(df_settled[mask_encerrados])

    # Interseção: Status ENCERRADOS e baixado_norm == SIM
    intersecao = len(df_settled[mask_encerrados & (baixado_series == "SIM")])

    # Quem encerrou sem nunca ter passado por baixa
    encerrados_diretos = encerrados_mes - intersecao

    # Baixas que ainda estão pendentes
    baixa_mes = len(df_settled[status_series == "BAIXA PROVISÓRIA"])

    # Cálculo do estoque inicial
    saidas_estoque_ativos = baixa_mes + encerrados_diretos
    ativos_mes_anterior = ativos - entradas_mes + saidas_estoque_ativos

    # ===============================
    # CÁLCULOS (Mantenha estes)
    # ===============================

    # Função de formatação segura
    def fmt_saida(valor):
        try:
            v = int(valor)
            return f"({v})" if v > 0 else ""
        except:
            return ""

    # ===============================
    # MONTAGEM DA TABELA (RECONCILIAÇÃO FINAL)
    # ===============================

    # Criamos os dados linha por linha para garantir a ordem exata da sua ilustração
    # No bloco de MONTAGEM DA TABELA:
    dados = [
        ["Ativos", int(ativos_mes_anterior), int(entradas_mes), fmt_saida(baixa_mes), fmt_saida(encerrados_mes), int(ativos)],
        ["Baixa Provisória", "", "", int(baixa_mes), fmt_saida(intersecao), int(baixa_mes - intersecao)],
        ["Encerrados", "", "", int(intersecao), int(encerrados_mes), int(intersecao + encerrados_mes)] 
    ]

    tabela = pd.DataFrame(dados, columns=["", "Mês anterior", "Novos", "Baixa provisória", "Encerrados", "Mês atual"])

    # Remove qualquer '0' que tenha sobrado para limpar o visual
    tabela = tabela.replace(0, "").replace("0", "")

    st.subheader(f"Movimentação - {fim.strftime('%b/%y')}")
    st.dataframe(tabela, use_container_width=True, hide_index=True)

    # =========================
    # PROCESSAMENTO DA TABELA
    # =========================

    def gerar_tabela_desembolso():
        # 1. Carregar os dados
        try:
            df_set = pd.read_excel("SETTLED_MENSAL.xlsx")
        except FileNotFoundError:
            st.error("Arquivo SETTLED_MENSAL.xlsx não encontrado.")
            return

        # 2. Agrupamento e Cálculos Base
        # Settled = Acordos, Won = Casos ganhos, Lost = Perdidos
        # Mapeamento para os nomes da imagem
        mapeamento = {
            "Won": "Casos ganhos*",
            "Settled": "Acordos**",
            "Lost": "Perdidos"
        }

        # Agrupar e somar
        resumo = df_set.groupby("Macro encerramento").agg({
            "Soma_Valor_Lancamento": "sum",       # BP Atualizado
            "Valor Pedido Objeto Corrigido": "sum" # Fcx Real
        }).reset_index()

        # Aplicar o mapeamento de nomes
        resumo["Baixa provisória e encerrados"] = resumo["Macro encerramento"].map(mapeamento)
        
        # Contagem de casos (Coluna da esquerda na imagem)
        contagem = df_set.groupby("Macro encerramento").size().reset_index(name="qtd")
        resumo = resumo.merge(contagem, on="Macro encerramento")

        # 3. Formatação dos valores (dividir por 1 milhão e 1 casa decimal)
        resumo["Fcx Real"] = (resumo["Soma_Valor_Lancamento"] / 1000000)
        resumo["BP atualizado"] = (resumo["Valor Pedido Objeto Corrigido"] / 1000000)

        # 4. Cálculos de Delta e %
        resumo["Δ"] = resumo["BP atualizado"] - resumo["Fcx Real"]
        resumo["%"] = (resumo["Δ"] / resumo["BP atualizado"]) * 100

        # 5. Organizar as colunas e ordenar conforme a imagem
        # Ordem desejada: Casos Ganhos, Acordos, Perdidos
        ordem = ["Casos ganhos*", "Acordos**", "Perdidos"]
        resumo["ordem_aux"] = resumo["Baixa provisória e encerrados"].map({v: i for i, v in enumerate(ordem)})
        resumo = resumo.sort_values("ordem_aux").drop(columns=["Macro encerramento", "Soma_Valor_Lancamento", "Valor Pedido Objeto Corrigido", "ordem_aux"])

        # 6. Linha de Total
        total_qtd = resumo["qtd"].sum()
        total_bp = resumo["BP atualizado"].sum()
        total_fcx = resumo["Fcx Real"].sum()
        total_delta = total_bp - total_fcx
        total_perc = (total_delta / total_bp) * 100 if total_bp != 0 else 0

        linha_total = pd.DataFrame({
            "qtd": [total_qtd],
            "Baixa provisória e encerrados": ["Total"],
            "BP atualizado": [total_bp],
            "Fcx Real": [total_fcx],
            "Δ": [total_delta],
            "%": [total_perc]
        })

        tabela_final = pd.concat([resumo, linha_total], ignore_index=True)

        # =========================
        # EXIBIÇÃO NO STREAMLIT
        # =========================

        st.markdown("### Desembolso e Fluxo de Caixa")

        # Formatação final para exibição
        df_display = tabela_final.copy()

        # Formata as colunas numéricas para 1 casa decimal e o % com símbolo
        # Adicionei o .str.replace(".", ",") para garantir o formato brasileiro (opcional)
        for col in ["BP atualizado", "Fcx Real", "Δ"]:
            df_display[col] = df_display[col].map("{:.1f}".format).str.replace(".", ",")

        df_display["%"] = df_display["%"].map("{:.0f}%".format)

        # Renomeia as colunas para o display
        colunas_novas = ["", "Baixa provisória e encerrados", "BP atualizado", "Fcx Real", "Δ", "%"]
        df_display.columns = colunas_novas

        # ==========================================
        # Exibe a tabela centralizada e sem índice
        # ==========================================
        st.dataframe(
            df_display,
            hide_index=True,          # Esconde o índice (equivalente ao que o st.table fazia)
            use_container_width=True, # Ocupa toda a tela
            column_config={
                # Esse truque aplica o alinhamento 'center' para todas as colunas da lista
                col: st.column_config.Column(alignment="center") for col in colunas_novas
            }
        )

    # Chamar a função dentro do bloco 'Resolved' do seu app
    gerar_tabela_desembolso()

    # ===============================
    # GRÁFICO 1
    # ===============================
    st.subheader("Entradas por Macro Assunto")

    graf1 = (
        df_entradas
        .groupby("macro assunto")
        .size()
        .reset_index(name="quantidade")
        .sort_values(by="quantidade", ascending=False)
    )

    # Criamos o objeto do gráfico primeiro para configurar as traces
    fig_bar = px.bar(graf1, x="macro assunto", y="quantidade", text="quantidade")

    # Ajusta para o texto ficar acima da barra
    fig_bar.update_traces(textposition='outside')

    st.plotly_chart(fig_bar, use_container_width=True)
    # =========================
    # PROCESSAMENTO DA TABELA
    # =========================

    def gerar_tabela_new_claims():

        # ==========================================
        # AGRUPAMENTO DOS DADOS
        # ==========================================

        resumo = df_entradas.groupby("macro assunto").agg({
            "valor pedido.1": "sum"
        }).reset_index()

        # Quantidade de claims
        contagem = (
            df_entradas.groupby("macro assunto")
            .size()
            .reset_index(name="New Claims 1M")
        )

        resumo = resumo.merge(contagem, on="macro assunto")

        # Fcx em milhões
        resumo["Fcx"] = resumo["valor pedido.1"] / 1_000_000

        # ==========================================
        # ORGANIZAÇÃO
        # ==========================================

        resumo = resumo.sort_values(
            by="New Claims 1M",
            ascending=False
        )

        resumo = resumo[[
            "New Claims 1M",
            "macro assunto",
            "Fcx"
        ]]

        # ==========================================
        # LINHA TOTAL
        # ==========================================

        linha_total = pd.DataFrame({
            "New Claims 1M": [resumo["New Claims 1M"].sum()],
            "macro assunto": ["Total"],
            "Fcx": [resumo["Fcx"].sum()]
        })

        tabela_final = pd.concat(
            [resumo, linha_total],
            ignore_index=True
        )

        # ==========================================
        # EXIBIÇÃO
        # ==========================================

        st.markdown("### New Claims")

        df_display = tabela_final.copy()

        # Formatação do Fcx
        df_display["Fcx"] = (
            df_display["Fcx"]
            .map("{:.2f}".format)
            .str.replace(".", ",")
        )

        # Renomeia colunas
        df_display.columns = [
            "Quantidade",
            "macro assunto",
            "Fcx"
        ]

        # Exibe usando o st.dataframe com configurações de coluna
        st.dataframe(
            df_display,
            hide_index=True, # Tira aquela coluna de índice inútil da esquerda
            use_container_width=True, # Faz a tabela ocupar toda a largura
            column_config={
                "Quantidade": st.column_config.Column(alignment="center"),
                "macro assunto": st.column_config.Column(alignment="center"),
                "Fcx": st.column_config.Column(alignment="center")
            }
        )

    # ==========================================
    # CHAMADA DA FUNÇÃO
    # ==========================================

    gerar_tabela_new_claims()

    # ===============================
    # GRÁFICO 2
    # ===============================
    
    st.subheader("Encerrados vs Baixa Provisória")

    graf2 = (
        df_settled
        .groupby(["status", "macro encerramento"])
        .size()
        .reset_index(name="quantidade")
    )

    fig = px.bar(
        graf2,
        x="status",
        y="quantidade",
        color="macro encerramento",
        barmode="stack",
        text_auto=True 
    )

    fig.update_traces(
        textfont_size=14,          
        textangle=0,               
        textposition="inside",     
        insidetextanchor="middle"  
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Entradas vs Encerrados (2026)")

    # =========================================================================
    #CONFIGURAÇÕES MANUAIS 
    # =========================================================================

    
    DATA_ATUAL = pd.to_datetime("2026-05-26") #ALTERE AQUI

    
    historico_manual = {
        1: {"entradas": 150, "encerrados": 120},
        2: {"entradas": 130, "encerrados": 140},
        3: {"entradas": 160, "encerrados": 110},
        4: {"entradas": 145, "encerrados": 135},
        # 5: {"entradas": X, "encerrados": Y}, 
    }

    
    if DATA_ATUAL.day >= 26:
        data_fiscal_atual = DATA_ATUAL + pd.DateOffset(months=1)
    else:
        data_fiscal_atual = DATA_ATUAL

    mes_atual_fiscal = data_fiscal_atual.month

    
    @st.cache_data(ttl=3600) 
    def carregar_contagem_atual():
        try:
            df_entradas = pd.read_excel("ENTRADAS.xlsx")
            df_settled = pd.read_excel("SETTLED_MENSAL.xlsx")
            
            # Conta a quantidade de linhas de cada base
            return len(df_entradas), len(df_settled)
        except Exception as e:
            st.warning(f"Aviso: Não foi possível ler as bases do mês atual. ({e})")
            return 0, 0

    qtd_entradas_atual, qtd_encerrados_atual = carregar_contagem_atual()

    
    meses_2026 = pd.date_range("2026-01-01", "2026-12-31", freq="MS")
    dados_grafico = []

    for data_mes in meses_2026:
        m = data_mes.month
        
        # MESES FUTUROS (Maiores que o mês fiscal atual) -> Zerados
        if m > mes_atual_fiscal:
            entradas = 0
            encerrados = 0
            
        # MÊS ATUAL FISCAL -> Puxa a contagem de linhas dos arquivos
        elif m == mes_atual_fiscal:
            entradas = qtd_entradas_atual
            encerrados = qtd_encerrados_atual
            
        # MESES PASSADOS -> Puxa do dicionário 'historico_manual'
        else:
            entradas = historico_manual.get(m, {}).get("entradas", 0)
            encerrados = historico_manual.get(m, {}).get("encerrados", 0)
            
        dados_grafico.append({
            "Data": data_mes,
            "Entradas": entradas,
            "Encerrados": encerrados
        })

    df_grafico = pd.DataFrame(dados_grafico)

    # =========================================================================
    #GERAÇÃO DO GRÁFICO
    # =========================================================================
    fig_temporal = px.line(
        df_grafico, 
        x="Data", 
        y=["Entradas", "Encerrados"], 
        markers=True,
        text="value"
    )

    fig_temporal.update_xaxes(
        dtick="M1", 
        tickformat="%b/%y", 
        tickmode="linear"
    )

    fig_temporal.update_traces(textposition="top center")

    st.plotly_chart(fig_temporal, use_container_width=True)
    # ===============================
    # ASSUMPTIONS
    # ===============================
    st.divider()
    st.subheader("Assumptions")

    if os.path.exists("assumptions_26_slides.xlsx"):

        assumptions = pd.read_excel("assumptions_26_slides.xlsx")
        assumptions.columns = assumptions.columns.astype(str).str.strip().str.lower()

        for col in ["calculo", "fixo", "soma"]:
            if col in assumptions.columns:
                assumptions[col] = pd.to_numeric(assumptions[col], errors="coerce")
                assumptions[col] = assumptions[col].apply(
                    lambda v: f"R$ {v/1000000:.2f}M" if pd.notnull(v) else ""
                )

        st.dataframe(assumptions, use_container_width=True, hide_index=True)

    else:
        st.info("Arquivo assumptions_26_slides.xlsx não encontrado.")


# ============================================================
# PAINEL 3 — Pagamentos (ex.: pagamentos.py)
# ============================================================
def painel_pagamentos():

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


# ============================================================
# CONTROLE DE ACESSO E ROTEAMENTO GERAL
# ============================================================
if authentication_status == False:
    st.error("Usuário ou senha incorretos")

elif authentication_status == None:
    st.warning("Digite seu usuário e senha")

elif authentication_status:

    authenticator.logout("Sair", "sidebar")

    st.sidebar.title("📁 Painéis")
    painel_selecionado = st.sidebar.radio(
        "Selecione o painel",
        ["Painel Jurídico", "Dashboard de Processos", "Pagamentos"]
    )

    st.sidebar.divider()

    if painel_selecionado == "Painel Jurídico":
        painel_juridico()
    elif painel_selecionado == "Dashboard de Processos":
        painel_dashboard_processos()
    elif painel_selecionado == "Pagamentos":
        painel_pagamentos()
