"""
SISTEMA INTEGRADO DE GESTÃO DA DEFESA CIVIL
Versão 2.0 - Refatoração Institucional
Autor: Defesa Civil AM / DTI
Descrição: Aplicação Streamlit para registro, monitoramento e administração de ocorrências.
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime
import requests
from core.database import obter_referencia

# =============================================================================
# CONFIGURAÇÕES GLOBAIS E CONSTANTES
# =============================================================================
PAGE_TITLE = "Sistema Defesa Civil"
PAGE_ICON = "🛡️"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "collapsed"

# Credenciais (em produção, usar variáveis de ambiente)
CREDENCIAIS = {
    "gestaodefesacivil": "defesacivilam26",
    "admin": "1234"
}

# Mapeamento de cores para riscos (hex e para pinos do mapa)
CORES_RISCO_HEX = {
    'ALTO': '#F97316',
    'MÉDIO': '#EAB308',
    'MEDIO': '#EAB308',
    'BAIXO': '#22C55E',
    'CRÍTICO': '#EF4444',
    'CRITICO': '#EF4444'
}
CORES_RISCO_PINO = {
    'ALTO': 'orange',
    'MÉDIO': 'beige',
    'MEDIO': 'beige',
    'BAIXO': 'green',
    'CRÍTICO': 'red',
    'CRITICO': 'red'
}

# URL base para assets (logo, etc.)
ASSETS_URL = "https://raw.githubusercontent.com/EBRlock/dashboard-defesa-civil/main/assets/logo_defesa.png"

# =============================================================================
# INICIALIZAÇÃO DA SESSÃO
# =============================================================================
def inicializar_sessao():
    """Garante que todas as chaves da sessão existam com valores padrão."""
    defaults = {
        "autenticado": False,
        "rota": "login",
        "endereco_capturado": "",
        "lat_capturada": None,
        "lon_capturada": None
    }
    for chave, valor in defaults.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor

inicializar_sessao()

# =============================================================================
# FUNÇÕES DE UTILIDADE (BUSCA, FORMATAÇÃO, ETC.)
# =============================================================================
def adicionar_emoji_natureza(tipo: str) -> str:
    """Adiciona um emoji correspondente ao tipo de ocorrência."""
    tipo_upper = str(tipo).upper()
    if 'INCÊNDIO' in tipo_upper:
        return f"🔥 {tipo}"
    if 'DESLIZAMENTO' in tipo_upper:
        return f"⛰️ {tipo}"
    if 'ALAGAMENTO' in tipo_upper:
        return f"🌊 {tipo}"
    if 'DESABAMENTO' in tipo_upper:
        return f"🏚️ {tipo}"
    return f"📝 {tipo}"

def buscar_endereco_por_coordenada(lat: float, lon: float) -> str:
    """
    Consulta o serviço Nominatim (OpenStreetMap) para obter o endereço
    a partir das coordenadas geográficas.
    """
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        headers = {'User-Agent': 'DefesaCivilAM/2.0'}
        resposta = requests.get(url, headers=headers, timeout=5).json()
        return resposta.get('display_name', 'Endereço não encontrado')
    except Exception:
        return ""

@st.cache_data(ttl=15)
def carregar_dados() -> pd.DataFrame:
    """
    Carrega os dados da coleção 'ocorrencias' do Firebase e retorna um DataFrame
    tratado com colunas padronizadas e metadados para filtros.
    """
    try:
        ref = obter_referencia("ocorrencias")
        dados = ref.get()
        if not dados:
            return pd.DataFrame()

        # Converte para DataFrame, tratando lista ou dicionário
        if isinstance(dados, list):
            dados_dict = {str(i): v for i, v in enumerate(dados) if v is not None}
            df = pd.DataFrame.from_dict(dados_dict, orient='index')
        else:
            df = pd.DataFrame.from_dict(dados, orient='index')

        # Colunas obrigatórias com valores padrão
        colunas_padrao = {
            'tipo': 'Não Informado',
            'encaminhamento': 'Não Informado',
            'risco': 'MÉDIO',
            'data': '',
            'bairro': 'Não Informado',
            'municipio': 'Manaus',
            'endereco': '',
            'solicitante': 'Não Informado'
        }
        for col, padrao in colunas_padrao.items():
            if col not in df.columns:
                df[col] = padrao

        # Enriquecimento do DataFrame
        df['tipo_emoji'] = df['tipo'].apply(adicionar_emoji_natureza)
        df['risco_padrao'] = df['risco'].astype(str).str.strip().str.upper()
        df['data_dt'] = pd.to_datetime(df['data'], errors='coerce', dayfirst=True)
        df['Ano_Filtro'] = df['data_dt'].dt.year.fillna(0).astype(int).astype(str).replace('0', 'Desconhecido')
        df['Mes_Filtro'] = df['data_dt'].dt.strftime('%m').fillna('Desconhecido')
        return df

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def navegar(rota: str):
    """Altera a rota atual e força a reexecução do script."""
    st.session_state["rota"] = rota
    st.rerun()

# =============================================================================
# ESTILOS CSS INSTITUCIONAIS
# =============================================================================
def aplicar_css_global():
    """Injeta CSS customizado para manter a identidade visual da Defesa Civil."""
    st.markdown("""
        <style>
        /* Remove elementos padrão do Streamlit */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}

        /* Fundo institucional azul escuro */
        .stApp {
            background-color: #0B0B2A !important;
        }

        /* Container principal com espaçamento adequado */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 1.5rem !important;
            max-width: 95% !important;
        }

        /* Tipografia padrão */
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText, .stNumberInput, .stSelectbox, .stDateInput, .stTimeInput {
            color: #FFFFFF !important;
            font-family: 'Segoe UI', Roboto, Arial, sans-serif !important;
        }

        /* Barra superior de título */
        .barra-superior {
            background-color: #0B0B2A;
            color: #FFFFFF;
            padding: 0.8rem 1.5rem;
            border-radius: 8px;
            font-weight: 700;
            font-size: 1.3rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-left: 6px solid #FF8C00;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            margin-bottom: 1.5rem;
        }

        /* Cartões escuros com borda sutil */
        .card-escuro {
            background-color: rgba(20, 20, 50, 0.7) !important;
            backdrop-filter: blur(2px);
            border-radius: 12px;
            padding: 1.2rem 1.5rem;
            border: 1px solid rgba(255,255,255,0.15);
            box-shadow: 0 8px 16px rgba(0,0,0,0.4);
            height: 100%;
        }

        /* Título de cartão */
        .titulo-cartao {
            font-size: 0.9rem;
            font-weight: 800;
            color: #FF8C00 !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 2px solid #FF8C00;
            padding-bottom: 0.4rem;
            margin-bottom: 1rem;
        }

        /* Inputs e selects com tema escuro */
        .stTextInput>div>div>input,
        .stNumberInput>div>div>input,
        .stDateInput>div>div>input,
        .stTimeInput>div>div>input,
        div[data-baseweb="select"]>div {
            background-color: #1E1E3F !important;
            border: 1px solid #3A3A6E !important;
            border-radius: 8px !important;
            color: #FFFFFF !important;
            font-size: 0.95rem !important;
        }

        div[data-baseweb="select"] * {
            color: #FFFFFF !important;
        }

        ul[data-baseweb="menu"] {
            background-color: #1E1E3F !important;
            border: 1px solid #3A3A6E !important;
        }

        li[role="option"] {
            color: #FFFFFF !important;
        }

        li[role="option"]:hover {
            background-color: #2D2D5A !important;
        }

        /* Botões */
        div.stButton > button[kind="secondary"] {
            background-color: #1E1E3F !important;
            color: #FFFFFF !important;
            border: 1px solid #3A3A6E !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            height: 2.8rem !important;
            transition: all 0.2s;
        }

        div.stButton > button[kind="secondary"]:hover {
            background-color: #2D2D5A !important;
            border-color: #FF8C00 !important;
        }

        div.stButton > button[kind="primary"] {
            background-color: #FF8C00 !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
            border: none !important;
            border-radius: 8px !important;
            height: 3rem !important;
            box-shadow: 0 4px 10px rgba(255,140,0,0.3);
        }

        div.stButton > button[kind="primary"]:hover {
            background-color: #E67E00 !important;
        }

        /* Métricas */
        div[data-testid="metric-container"] {
            background-color: rgba(255,255,255,0.05) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: 10px !important;
            padding: 0.8rem !important;
            text-align: center;
        }

        div[data-testid="stMetricValue"] > div {
            color: #FF8C00 !important;
            font-size: 2rem !important;
            font-weight: 900 !important;
        }

        /* Tabelas */
        [data-testid="stDataFrame"] {
            background-color: #1E1E3F !important;
            border-radius: 8px;
        }

        /* Divisórias */
        hr {
            border-color: rgba(255,255,255,0.2) !important;
            margin: 1rem 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# COMPONENTES DE INTERFACE REUTILIZÁVEIS
# =============================================================================
def cabecalho_com_voltar(titulo: str, rota_destino: str = "hub"):
    """Exibe um cabeçalho com botão de voltar e título institucional."""
    col_voltar, col_titulo = st.columns([1, 10])
    with col_voltar:
        if st.button("⬅ VOLTAR", type="secondary", use_container_width=True):
            navegar(rota_destino)
    with col_titulo:
        st.markdown(f"<div class='barra-superior'>{titulo}</div>", unsafe_allow_html=True)

def cartao(titulo: str, conteudo, altura_auto=False):
    """Cria um cartão escuro com título e conteúdo (qualquer elemento Streamlit)."""
    with st.container():
        st.markdown(f"<div class='card-escuro'>", unsafe_allow_html=True)
        st.markdown(f"<div class='titulo-cartao'>{titulo}</div>", unsafe_allow_html=True)
        conteudo()
        st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# TELAS DO SISTEMA
# =============================================================================
def tela_login():
    """Tela de autenticação do sistema."""
    with st.container():
        # Centraliza o cartão de login
        _, col_centro, _ = st.columns([1.5, 2, 1.5])
        with col_centro:
            st.markdown("<div class='card-escuro' style='margin-top: 10vh; text-align: center;'>", unsafe_allow_html=True)
            st.image(ASSETS_URL, width=130)
            st.markdown("<h2 style='margin-top: 0.5rem;'>DEFESA CIVIL</h2>", unsafe_allow_html=True)
            st.markdown("<p style='color: #FF8C00; font-weight: 600;'>SISTEMA INTEGRADO DE GESTÃO</p>", unsafe_allow_html=True)
            st.write("")

            usuario = st.text_input("Usuário", placeholder="Digite seu usuário", label_visibility="collapsed")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha", label_visibility="collapsed")

            if st.button("AUTENTICAR", type="primary", use_container_width=True):
                if (usuario in CREDENCIAIS and CREDENCIAIS[usuario] == senha):
                    st.session_state["autenticado"] = True
                    navegar("hub")
                else:
                    st.error("Acesso negado. Verifique suas credenciais.")
            st.markdown("</div>", unsafe_allow_html=True)

def tela_hub():
    """Tela principal (hub) com acesso aos módulos."""
    _, col_centro, _ = st.columns([1.5, 2, 1.5])
    with col_centro:
        st.markdown("<div class='card-escuro' style='margin-top: 8vh; text-align: center;'>", unsafe_allow_html=True)
        st.image(ASSETS_URL, width=130)
        st.markdown("<h2>DEFESA CIVIL</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #FF8C00;'>BEM-VINDO AO PORTAL OPERACIONAL</p>", unsafe_allow_html=True)
        st.markdown("---")

        if st.button("📝 REGISTRAR OCORRÊNCIA", type="secondary", use_container_width=True):
            navegar("registro")
        if st.button("📊 PAINEL DE MONITORAMENTO", type="secondary", use_container_width=True):
            navegar("dashboard")
        if st.button("⚙️ ADMINISTRAÇÃO DO BANCO", type="secondary", use_container_width=True):
            navegar("admin")

        st.write("")
        if st.button("ENCERRAR SESSÃO", type="primary", use_container_width=True):
            st.session_state["autenticado"] = False
            navegar("login")
        st.markdown("</div>", unsafe_allow_html=True)

def tela_registro():
    """Tela de registro de novas ocorrências com mapa interativo."""
    cabecalho_com_voltar("CENTRAL DE MONITORAMENTO - REGISTRO E DESPACHO")

    col_form, col_meio, col_mapa = st.columns([1.5, 1, 2.5])

    # Coluna do mapa (interativo para captura de coordenadas)
    with col_mapa:
        def _conteudo_mapa():
            st.markdown("<p style='font-weight:600;'>📍 Toque no mapa para capturar a coordenada</p>", unsafe_allow_html=True)
            # Mapa base (CartoDB Positron)
            m_registro = folium.Map(location=[-3.119, -60.021], zoom_start=12, tiles="CartoDB positron")

            # Se já existe um ponto capturado, exibe o marcador
            if st.session_state["lat_capturada"] and st.session_state["lon_capturada"]:
                folium.Marker(
                    [st.session_state["lat_capturada"], st.session_state["lon_capturada"]],
                    icon=folium.Icon(color="red", icon="map-marker")
                ).add_to(m_registro)

            mapa_clicado = st_folium(m_registro, height=400, use_container_width=True, key="mapa_novo")

            if mapa_clicado and mapa_clicado.get("last_clicked"):
                lat = mapa_clicado["last_clicked"]["lat"]
                lon = mapa_clicado["last_clicked"]["lng"]
                if lat != st.session_state["lat_capturada"]:
                    st.session_state["lat_capturada"] = lat
                    st.session_state["lon_capturada"] = lon
                    st.session_state["endereco_capturado"] = buscar_endereco_por_coordenada(lat, lon)
                    st.rerun()

            if st.session_state["lat_capturada"]:
                st.success("✅ GPS capturado com sucesso!")
        cartao("MAPA DE CAPTURA", _conteudo_mapa)

    # Coluna do formulário de cadastro
    with col_form:
        def _conteudo_form():
            solicitante = st.text_input("SOLICITANTE", placeholder="Nome completo")
            municipio = st.text_input("MUNICÍPIO", value="Manaus")
            bairro = st.text_input("BAIRRO", placeholder="Bairro da ocorrência")
            endereco = st.text_input("LOGRADOURO", value=st.session_state["endereco_capturado"])

            c_num, c_comp = st.columns([1, 2])
            numero = c_num.text_input("NÚMERO", placeholder="Nº")
            complemento = c_comp.text_input("COMPLEMENTO", placeholder="Ex: Apto 101")

            natureza = st.selectbox("NATUREZA DA OCORRÊNCIA",
                                    ["Alagamento", "Incêndio", "Deslizamento", "Desabamento", "Outros"])
            risco = st.selectbox("GRAU DE RISCO", ["BAIXO", "MÉDIO", "ALTO", "CRÍTICO"])

            c_data, c_hora = st.columns(2)
            data_ocorrencia = c_data.date_input("DATA", datetime.now())
            hora_ocorrencia = c_hora.time_input("HORA", datetime.now().time())

            encaminhamento = st.selectbox("ENCAMINHAMENTO",
                                          ["Aguardando Triagem", "Polícia Militar", "Corpo de Bombeiros", "Defesa Civil Municipal"])

            if st.button("SALVAR OCORRÊNCIA", type="primary", use_container_width=True):
                if not bairro or not endereco:
                    st.warning("Preencha o bairro e o logradouro.")
                elif not st.session_state["lat_capturada"]:
                    st.warning("Toque no mapa para capturar a coordenada GPS!")
                else:
                    lat = st.session_state["lat_capturada"]
                    lon = st.session_state["lon_capturada"]
                    end_completo = f"{endereco}, {numero} - {complemento}".strip(" ,-")
                    novo_registro = {
                        "tipo": natureza,
                        "municipio": municipio,
                        "bairro": bairro,
                        "endereco": end_completo,
                        "risco": risco,
                        "encaminhamento": encaminhamento,
                        "data": datetime.now().strftime("%d/%m/%Y"),
                        "solicitante": solicitante,
                        "latitude": lat,
                        "longitude": lon
                    }
                    try:
                        obter_referencia("ocorrencias").push(novo_registro)
                        st.success("Ocorrência salva com sucesso!")
                        st.balloons()
                        carregar_dados.clear()
                        # Limpa os dados da sessão
                        st.session_state["endereco_capturado"] = ""
                        st.session_state["lat_capturada"] = None
                        st.session_state["lon_capturada"] = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
        cartao("DADOS CADASTRAIS", _conteudo_form)

    # Coluna do meio (monitoramento rápido)
    with col_meio:
        def _conteudo_monitoramento():
            c_and, c_fin = st.columns(2)
            # Exemplo estático (poderia ser dinâmico)
            c_and.metric("EM ANDAMENTO", "0")
            c_fin.metric("FINALIZADOS", "0")
            st.markdown("---")
            st.markdown("<div style='font-size:0.8rem; background:#1E1E3F; padding:0.5rem; border-radius:6px;'>"
                        "<b>TIPO</b> &nbsp;&nbsp; <b>RISCO</b> &nbsp;&nbsp; <b>STATUS</b> &nbsp;&nbsp; <b>AÇÃO</b></div>",
                        unsafe_allow_html=True)
            st.info("Nenhuma ocorrência ativa no momento.")
        cartao("MONITORAMENTO DO TURNO", _conteudo_monitoramento)

def tela_dashboard():
    """Painel tático com gráficos, mapa e filtros."""
    df = carregar_dados()
    if df.empty:
        st.info("Sincronizando base de dados...")
        return

    cabecalho_com_voltar("PAINEL TÁTICO - MONITORAMENTO DE OCORRÊNCIAS")

    # Filtros em linha
    with st.container():
        st.markdown("<div class='card-escuro'>", unsafe_allow_html=True)
        c_f1, c_f2, c_f3, c_f4, c_f5 = st.columns(5)
        f_tipo = c_f1.selectbox("NATUREZA", ["Todas"] + sorted(df['tipo'].dropna().unique().tolist()))
        f_mun = c_f2.selectbox("MUNICÍPIO", ["Todas"] + sorted(df['municipio'].dropna().unique().tolist()))
        f_bairro = c_f3.selectbox("BAIRRO", ["Todos"] + sorted(df['bairro'].dropna().unique().tolist()))
        f_ano = c_f4.selectbox("ANO", ["Todos"] + sorted([a for a in df['Ano_Filtro'].unique() if a != 'Desconhecido']))
        f_mes = c_f5.selectbox("MÊS", ["Todos"] + sorted([m for m in df['Mes_Filtro'].unique() if m != 'Desconhecido']))
        st.markdown("</div>", unsafe_allow_html=True)

    # Aplicar filtros
    df_filtrado = df.copy()
    if f_tipo != "Todas":
        df_filtrado = df_filtrado[df_filtrado['tipo'] == f_tipo]
    if f_mun != "Todas":
        df_filtrado = df_filtrado[df_filtrado['municipio'] == f_mun]
    if f_bairro != "Todos":
        df_filtrado = df_filtrado[df_filtrado['bairro'] == f_bairro]
    if f_ano != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Ano_Filtro'] == f_ano]
    if f_mes != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Mes_Filtro'] == f_mes]

    col_esq, col_dir = st.columns([1, 1.8])

    with col_esq:
        # Gráfico de pizza: natureza
        def _graf_natureza():
            st.dataframe(df_filtrado['tipo_emoji'].value_counts().reset_index(),
                         hide_index=True, use_container_width=True, height=200)
        cartao("NATUREZA", _graf_natureza)

        # Gráfico de pizza: encaminhamento
        def _graf_encaminhamento():
            st.dataframe(df_filtrado['encaminhamento'].value_counts().reset_index(),
                         hide_index=True, use_container_width=True, height=200)
        cartao("ENCAMINHAMENTO", _graf_encaminhamento)

        # Total e gráfico de risco
        col_tot, col_pie = st.columns([1, 1.5])
        with col_tot:
            def _total():
                st.metric("", len(df_filtrado))
            cartao("TOTAL", _total)
        with col_pie:
            def _risco():
                fig = px.pie(df_filtrado['risco_padrao'].value_counts().reset_index(),
                             values='count', names='risco_padrao', hole=0.4,
                             color='risco_padrao', color_discrete_map=CORES_RISCO_HEX)
                fig.update_layout(height=140, margin=dict(t=0, b=0, l=0, r=0),
                                  paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
                st.plotly_chart(fig, use_container_width=True, theme=None)
            cartao("RISCO", _risco)

    with col_dir:
        # Mapa operacional
        def _mapa():
            m = folium.Map(location=[-3.119, -60.021], zoom_start=11.5, tiles="CartoDB positron")
            for _, row in df_filtrado.iterrows():
                try:
                    lat, lon = float(row['latitude']), float(row['longitude'])
                    cor = CORES_RISCO_PINO.get(row.get('risco_padrao', 'MÉDIO'), 'gray')
                    folium.Marker(
                        [lat, lon],
                        tooltip=row.get('tipo', 'Ocorrência'),
                        icon=folium.Icon(color=cor)
                    ).add_to(m)
                except Exception:
                    continue
            st_folium(m, use_container_width=True, height=300)
        cartao("MAPA OPERACIONAL", _mapa)

        # Gráfico de barras: ocorrências por mês
        def _grafico_mes():
            df_mes = df_filtrado[df_filtrado['Mes_Filtro'] != 'Desconhecido']
            if not df_mes.empty:
                fig = px.bar(df_mes['Mes_Filtro'].value_counts().reset_index().sort_values(by='Mes_Filtro'),
                             x='Mes_Filtro', y='count')
                fig.update_traces(marker_color='#FF8C00')
                fig.update_layout(height=150, margin=dict(t=0, b=0, l=0, r=0),
                                  paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                  font=dict(color='white'))
                st.plotly_chart(fig, use_container_width=True, theme=None)
            else:
                st.info("Sem dados mensais")
        cartao("EVOLUÇÃO MENSAL", _grafico_mes)

def tela_admin():
    """Tela administrativa para exclusão de registros."""
    cabecalho_com_voltar("PAINEL DO ADMINISTRADOR", "hub")

    df = carregar_dados()
    if df.empty:
        st.info("Nenhum registro encontrado.")
        return

    def _conteudo_admin():
        opcoes = {
            f"{row.get('data', '')} | {row.get('tipo', '')} | {row.get('bairro', '')} [ID: {idx}]": idx
            for idx, row in df.iterrows()
        }
        selecao = st.selectbox("Selecione o registro para exclusão:", list(opcoes.keys()))

        st.warning("Esta operação é irreversível.")
        if st.button("EXCLUIR PERMANENTEMENTE", type="primary"):
            try:
                obter_referencia(f"ocorrencias/{opcoes[selecao]}").delete()
                st.success("Registro excluído com sucesso.")
                carregar_dados.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Erro na exclusão: {e}")
    cartao("AUDITORIA E EXCLUSÃO DE REGISTROS", _conteudo_admin)

# =============================================================================
# ROTEADOR PRINCIPAL
# =============================================================================
def main():
    """Função principal que controla o fluxo da aplicação."""
    aplicar_css_global()

    if not st.session_state["autenticado"]:
        tela_login()
    else:
        rota = st.session_state["rota"]
        if rota == "hub":
            tela_hub()
        elif rota == "dashboard":
            tela_dashboard()
        elif rota == "registro":
            tela_registro()
        elif rota == "admin":
            tela_admin()
        else:
            # Rota desconhecida, volta para o hub
            navegar("hub")

if __name__ == "__main__":
    main()
