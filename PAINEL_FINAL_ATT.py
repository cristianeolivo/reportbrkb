import streamlit as st
import pandas as pd
import plotly.express as px
import os
import streamlit_authenticator as stauth

# ===============================
# CONFIG
# ===============================
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

# =========================
# LOGIN
# =========================
credentials = {
    "usernames": {
        "JuridicoErbe": {
            "name": "JuridicoErbe",
            "password": "Erbe@3009"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "meu_appv3",
    "abc123",
    cookie_expiry_days=1
)

authenticator.login()
authentication_status = st.session_state.get("authentication_status")

# =========================
# CONTROLE DE ACESSO
# =========================
if authentication_status == False:
    st.error("Usuário ou senha incorretos")

elif authentication_status == None:
    st.warning("Digite seu usuário e senha")

elif authentication_status:

    authenticator.logout("Sair", "sidebar")
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
        base_app = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
        arquivo = os.path.join(base_app, "SETTLED_MENSAL.xlsx")
        aba_preferencial = "SETTLED_MENSAL"

        col_macro = "Macro encerramento"
        col_fcx = "Soma_Valor_Lancamento"
        col_bp = "Valor Pedido Objeto Corrigido"

        colunas_obrigatorias = [col_macro, col_fcx, col_bp]

        mapeamento = {
            "Won": "Casos ganhos",
            "Settled": "Acordos",
            "Lost": "Perdidos"
        }

        ordem_macro = ["Won", "Settled", "Lost"]

        try:
            excel = pd.ExcelFile(arquivo)
        except FileNotFoundError:
            st.error("Arquivo SETTLED_MENSAL.xlsx não encontrado.")
            return
        except Exception as e:
            st.error(f"Erro ao abrir SETTLED_MENSAL.xlsx: {e}")
            return

        if aba_preferencial in excel.sheet_names:
            aba_usada = aba_preferencial
        elif len(excel.sheet_names) == 1:
            aba_usada = excel.sheet_names[0]
        else:
            st.error(
                "Aba 'SETTLED_MENSAL' não encontrada em SETTLED_MENSAL.xlsx. "
                f"Abas disponíveis: {', '.join(excel.sheet_names)}"
            )
            return

        try:
            df_set = pd.read_excel(excel, sheet_name=aba_usada)
            df_set.columns = df_set.columns.astype(str).str.strip()
        except Exception as e:
            st.error(f"Erro ao ler a aba '{aba_usada}': {e}")
            return

        colunas_ausentes = [col for col in colunas_obrigatorias if col not in df_set.columns]

        if colunas_ausentes:
            st.error(
                "Coluna(s) obrigatória(s) ausente(s) em SETTLED_MENSAL.xlsx: "
                + ", ".join(colunas_ausentes)
            )
            return

        df_set[col_macro] = df_set[col_macro].fillna("").astype(str).str.strip()
        df_set[col_fcx] = pd.to_numeric(df_set[col_fcx], errors="coerce").fillna(0)
        df_set[col_bp] = pd.to_numeric(df_set[col_bp], errors="coerce").fillna(0)

        diagnostico = (
            df_set.groupby(col_macro, dropna=False)
            .agg(
                qtd=(col_macro, "size"),
                soma_bruta_bp_atualizado=(col_bp, "sum"),
                soma_bruta_fcx_real=(col_fcx, "sum")
            )
            .reset_index()
        )

        with st.expander("Diagnóstico temporário - Desembolso e Fluxo de Caixa", expanded=False):
            st.write(f"Arquivo utilizado: {arquivo}")
            st.write(f"Aba utilizada: {aba_usada}")
            st.write(f"Abas disponíveis no arquivo: {', '.join(excel.sheet_names)}")
            st.write(f"BP atualizado vem da coluna: {col_bp}")
            st.write(f"Fcx Real vem da coluna: {col_fcx}")
            st.dataframe(diagnostico, hide_index=True, use_container_width=True)

        df_tabela = df_set[df_set[col_macro].isin(ordem_macro)].copy()

        resumo = (
            df_tabela.groupby(col_macro)
            .agg(
                qtd=(col_macro, "size"),
                bp_bruto=(col_bp, "sum"),
                fcx_bruto=(col_fcx, "sum")
            )
            .reindex(ordem_macro, fill_value=0)
            .reset_index()
        )

        resumo["Baixa provisória e encerrados"] = resumo[col_macro].map(mapeamento)

        resumo["BP atualizado"] = resumo["bp_bruto"] / 1_000_000
        resumo["Fcx Real"] = resumo["fcx_bruto"] / 1_000_000

        resumo["Δ"] = resumo["BP atualizado"] - resumo["Fcx Real"]
        resumo["%"] = resumo.apply(
            lambda row: (row["Δ"] / row["BP atualizado"]) * 100 if row["BP atualizado"] != 0 else 0,
            axis=1
        )

        resumo = resumo[
            ["qtd", "Baixa provisória e encerrados", "BP atualizado", "Fcx Real", "Δ", "%"]
        ]

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

        st.markdown("### Desembolso e Fluxo de Caixa")

        df_display = tabela_final.copy()

        for col in ["BP atualizado", "Fcx Real", "Δ"]:
            df_display[col] = df_display[col].map(lambda x: f"{x:.1f}".replace(".", ","))

        df_display["%"] = df_display["%"].map(lambda x: f"{x:.0f}%")

        colunas_novas = ["", "Baixa provisória e encerrados", "BP atualizado", "Fcx Real", "Δ", "%"]
        df_display.columns = colunas_novas

        st.dataframe(
            df_display,
            hide_index=True,
            use_container_width=True,
            column_config={
                col: st.column_config.Column(alignment="center") for col in colunas_novas
            }
        )

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

    import pandas as pd
    import numpy as np
    import plotly.express as px
    import streamlit as st
    import datetime

    import pandas as pd
    import numpy as np
    import plotly.express as px
    import streamlit as st
    import datetime

    st.subheader("Entradas vs Encerrados (2026)")

    # =========================================================================
    #CONFIGURAÇÕES MANUAIS 
    # =========================================================================

    
    DATA_ATUAL = pd.to_datetime("2026-05-26") #ALTERE AQUI

    
    historico_manual = {
        1: {"entradas": 32, "encerrados": 82},
        2: {"entradas": 49, "encerrados": 149},
        3: {"entradas": 45, "encerrados": 68},
        4: {"entradas": 13, "encerrados": 115},
        5: {"entradas": 22, "encerrados": 59},

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
