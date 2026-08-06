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
        "ControladoriaErbe": {
            "name": "ControladoriaErbe",
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