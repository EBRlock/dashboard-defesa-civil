"""
SISTEMA INTEGRADO DE GESTÃO DA DEFESA CIVIL
Versão 3.1 - Dashboard com fundo branco e busca integrada
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime
import requests
import socket
import time
from core.database import obter_referencia

# =============================================================================
# CONFIGURAÇÕES GLOBAIS E CONSTANTES
# =============================================================================
st.set_page_config(page_title="Sistema Defesa Civil", layout="wide", initial_sidebar_state="collapsed")

CREDENCIAIS = {
    "gestaodefesacivil": "defesacivilam26",
    "admin": "1234"
}

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
EMOJIS_TIPO = {
    'Alagamento': '🌊',
    'Incêndio': '🔥',
    'Deslizamento': '⛰️',
    'Desabamento': '🏚️',
    'Outros': '📝'
}
ASSETS_URL = "https://raw.githubusercontent.com/EBRlock/dashboard-defesa-civil/main/assets/logo_defesa.png"

# =============================================================================
# INICIALIZAÇÃO DA SESSÃO
# =============================================================================
def inicializar_sessao():
    defaults = {
        "autenticado": False,
        "rota": "login",
        "endereco_capturado": "",
        "lat_capturada": None,
        "lon_capturada": None,
        "map_center": [-3.119, -60.021],
        "map_zoom": 12,
        "ocorrencias_sessao": [],
        "cont_andamento": 0,
        "cont_finalizado": 0,
        "conexao_verificada": None
    }
    for chave, valor in defaults.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor

inicializar_sessao()

# =============================================================================
# FUNÇÕES DE UTILIDADE
# =============================================================================
def adicionar_emoji_natureza(tipo: str) -> str:
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
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        headers = {'User-Agent': 'DefesaCivilAM/3.0'}
        resposta = requests.get(url, headers=headers, timeout=5).json()
        return resposta.get('display_name', 'Endereço não encontrado')
    except Exception:
        return ""

def pesquisar_endereco(query: str):
    """Busca coordenadas a partir de um endereço e retorna (lat, lon, display_name) ou None"""
    try:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={query}"
        headers = {'User-Agent': 'DefesaCivilAM/3.0'}
        resposta = requests.get(url, headers=headers, timeout=5).json()
        if resposta:
            lat = float(resposta[0]['lat'])
            lon = float(resposta[0]['lon'])
            display = resposta[0]['display_name']
            return lat, lon, display
    except Exception:
        pass
    return None

def verificar_conexao():
    """Verifica se há acesso à internet (cache por 30 segundos)"""
    if st.session_state["conexao_verificada"] is not None:
        if time.time() - st.session_state["conexao_verificada"][1] < 30:
            return st.session_state["conexao_verificada"][0]
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        st.session_state["conexao_verificada"] = (True, time.time())
        return True
    except OSError:
        st.session_state["conexao_verificada"] = (False, time.time())
        return False

@st.cache_data(ttl=15)
def carregar_dados() -> pd.DataFrame:
    """Carrega dados do Firebase e retorna DataFrame padronizado"""
    try:
        ref = obter_referencia("ocorrencias")
        dados = ref.get()
        if not dados:
            return pd.DataFrame()

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
            'hora': '',
            'bairro': 'Não Informado',
            'municipio': 'Manaus',
            'endereco': '',
            'solicitante': 'Não Informado',
            'status': 'Em andamento',
            'latitude': None,
            'longitude': None
        }
        for col, padrao in colunas_padrao.items():
            if col not in df.columns:
                df[col] = padrao

        # Converter latitude/longitude para float
        for col in ['latitude', 'longitude']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

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
    st.session_state["rota"] = rota
    st.rerun()

# =============================================================================
# ESTILOS CSS (CARDS COM FUNDO BRANCO)
# =============================================================================
def aplicar_css_global():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
        .stApp { background-color: #0B0B2A !important; }
        .block-container { padding-top: 1.5rem !important; padding-bottom: 1.5rem !important; max-width: 95% !important; }
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown { color: #FFFFFF !important; font-family: 'Segoe UI', Roboto, Arial, sans-serif !important; }
        
        .barra-superior {
            background-color: #0B0B2A; color: #FFFFFF; padding: 0.8rem 1.5rem; border-radius: 8px;
            font-weight: 700; font-size: 1.3rem; text-transform: uppercase; letter-spacing: 1px;
            border-left: 6px solid #FF8C00; box-shadow: 0 4px 10px rgba(0,0,0,0.3); margin-bottom: 1.5rem;
            display: flex; justify-content: space-between; align-items: center;
        }

        /* CARDS COM FUNDO BRANCO */
        .card-branco {
            background-color: #FFFFFF !important;
            border-radius: 12px;
            padding: 1.2rem 1.5rem;
            border: 1px solid #E0E0E0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            height: 100%;
        }
        .titulo-cartao {
            font-size: 0.9rem;
            font-weight: 800;
            color: #0B0B2A !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 2px solid #FF8C00;
            padding-bottom: 0.4rem;
            margin-bottom: 1rem;
        }
        /* Texto dentro dos cards */
        .card-branco p, .card-branco label, .card-branco .stMarkdown, .card-branco .stText, .card-branco .stNumberInput, .card-branco .stSelectbox, .card-branco .stDateInput, .card-branco .stTimeInput {
            color: #333333 !important;
        }
        
        /* Inputs e selects (mantemos escuros para contraste) */
        .stTextInput>div>div>input, .stNumberInput>div>div>input, .stDateInput>div>div>input, .stTimeInput>div>div>input, div[data-baseweb="select"]>div {
            background-color: #F5F5F5 !important;
            border: 1px solid #CCCCCC !important;
            border-radius: 8px !important;
            color: #333333 !important;
            font-size: 0.95rem !important;
        }
        div[data-baseweb="select"] * { color: #333333 !important; }
        ul[data-baseweb="menu"] { background-color: #FFFFFF !important; border: 1px solid #CCCCCC !important; }
        li[role="option"] { color: #333333 !important; }
        li[role="option"]:hover { background-color: #F0F0F0 !important; }
        
        div.stButton > button[kind="secondary"] {
            background-color: #1E1E3F !important;
            color: #FFFFFF !important;
            border: 1px solid #3A3A6E !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            height: 2.8rem !important;
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
        div.stButton > button[kind="primary"]:hover { background-color: #E67E00 !important; }
        
        /* Botão de busca (lupa) */
        .botao-busca {
            background-color: #1976D2 !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            height: 2.8rem !important;
            width: 3rem !important;
            font-size: 1.2rem !important;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        /* Métricas e tabelas */
        div[data-testid="metric-container"] {
            background-color: #FFFFFF !important;
            border: 1px solid #E0E0E0 !important;
            border-radius: 10px !important;
            padding: 0.8rem !important;
            text-align: center;
        }
        div[data-testid="stMetricValue"] > div { color: #0B0B2A !important; font-size: 2rem !important; font-weight: 900 !important; }
        [data-testid="stDataFrame"] { background-color: #FFFFFF !important; border-radius: 8px; }
        
        .status-andamento { color: #F57C00; font-weight: bold; }
        .status-finalizado { color: #2E7D32; font-weight: bold; }
        
        /* Estilo de impressão */
        @media print {
            .stApp { background-color: white !important; }
            .barra-superior { background-color: #0B0B2A !important; color: white !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
            .card-branco { box-shadow: none !important; border: 1px solid #CCC !important; }
            button, .stButton { display: none !important; }
        }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# COMPONENTES REUTILIZÁVEIS
# =============================================================================
def cabecalho_com_voltar(titulo: str, rota_destino: str = "hub", is_dashboard=False):
    col_voltar, col_titulo = st.columns([1, 10])
    with col_voltar:
        if st.button("⬅ VOLTAR", type="secondary", use_container_width=True):
            navegar(rota_destino)
    with col_titulo:
        if is_dashboard:
            html_barra = f"""
            <div class='barra-superior'>
                <span>{titulo}</span>
                <a href='javascript:window.print()' style='background-color: #FF8C00; color: white; padding: 5px 15px; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: bold;'>📄 EXPORTAR PDF</a>
            </div>
            """
            st.markdown(html_barra, unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='barra-superior'>{titulo}</div>", unsafe_allow_html=True)

def cartao(titulo: str, conteudo):
    with st.container():
        st.markdown(f"<div class='card-branco'>", unsafe_allow_html=True)
        st.markdown(f"<div class='titulo-cartao'>{titulo}</div>", unsafe_allow_html=True)
        conteudo()
        st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# FUNÇÕES DE MONITORAMENTO DE TURNO
# =============================================================================
def adicionar_ocorrencia_sessao(tipo, risco, lat, lon, endereco, id_firebase=None):
    ocorrencia = {
        "id": len(st.session_state["ocorrencias_sessao"]),
        "tipo": tipo,
        "risco": risco,
        "lat": lat,
        "lon": lon,
        "endereco": endereco,
        "status": "Em andamento",
        "firebase_id": id_firebase
    }
    st.session_state["ocorrencias_sessao"].append(ocorrencia)
    st.session_state["cont_andamento"] += 1

def finalizar_ocorrencia_sessao(indice):
    ocorrencia = st.session_state["ocorrencias_sessao"][indice]
    if ocorrencia["status"] == "Em andamento":
        ocorrencia["status"] = "Finalizado"
        st.session_state["cont_andamento"] -= 1
        st.session_state["cont_finalizado"] += 1
        if ocorrencia.get("firebase_id"):
            try:
                ref = obter_referencia(f"ocorrencias/{ocorrencia['firebase_id']}")
                ref.update({"status": "Finalizado"})
            except Exception as e:
                st.warning(f"Erro ao atualizar Firebase: {e}")

def renderizar_monitoramento_turno():
    st.markdown(f"<div class='card-branco'>", unsafe_allow_html=True)
    st.markdown("<div class='titulo-cartao'>MONITORAMENTO DO TURNO</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("EM ANDAMENTO", st.session_state["cont_andamento"])
    with col2:
        st.metric("FINALIZADOS", st.session_state["cont_finalizado"])
    
    st.markdown("---")
    
    # Cabeçalho
    cabecalho = st.columns([2, 1, 1.5, 1])
    cabecalho[0].markdown("**TIPO**")
    cabecalho[1].markdown("**RISCO**")
    cabecalho[2].markdown("**STATUS**")
    cabecalho[3].markdown("**AÇÃO**")
    
    if not st.session_state["ocorrencias_sessao"]:
        st.info("Nenhuma ocorrência registrada no turno.")
    else:
        for i, occ in enumerate(st.session_state["ocorrencias_sessao"]):
            cols = st.columns([2, 1, 1.5, 1])
            with cols[0]:
                emoji = EMOJIS_TIPO.get(occ['tipo'], '📍')
                st.write(f"{emoji} {occ['tipo']}")
            with cols[1]:
                risco = occ['risco']
                cor = CORES_RISCO_HEX.get(risco.upper(), '#333')
                st.markdown(f"<span style='color:{cor}; font-weight:bold;'>{risco}</span>", unsafe_allow_html=True)
            with cols[2]:
                status = occ['status']
                if status == "Em andamento":
                    st.markdown("<span class='status-andamento'>EM ANDAMENTO</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='status-finalizado'>FINALIZADO</span>", unsafe_allow_html=True)
            with cols[3]:
                if status == "Em andamento":
                    if st.button("FINALIZAR", key=f"fin_{i}"):
                        finalizar_ocorrencia_sessao(i)
                        st.rerun()
                else:
                    st.button("FINALIZADO", disabled=True, key=f"fin_disabled_{i}")
    st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# FUNÇÃO PARA CRIAR MAPA NO REGISTRO (COM MARCADORES DA SESSÃO)
# =============================================================================
def criar_mapa_registro():
    center = st.session_state["map_center"]
    zoom = st.session_state["map_zoom"]
    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron")
    
    # Marcador de busca atual
    if st.session_state["lat_capturada"] and st.session_state["lon_capturada"]:
        folium.Marker(
            [st.session_state["lat_capturada"], st.session_state["lon_capturada"]],
            popup="Ponto selecionado",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)
    
    # Ocorrências da sessão
    for occ in st.session_state["ocorrencias_sessao"]:
        lat = occ["lat"]
        lon = occ["lon"]
        if lat and lon:
            cor = "#F57C00" if occ["status"] == "Em andamento" else "#2E7D32"
            folium.Circle(
                radius=250,
                location=[lat, lon],
                color=cor,
                fill=True,
                fillOpacity=0.2,
                weight=2
            ).add_to(m)
            emoji = EMOJIS_TIPO.get(occ['tipo'], '📍')
            html = f"""
            <div style="font-size: 24px; background-color: white; border-radius: 50%; padding: 5px; border: 3px solid {cor}; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;">
                {emoji}
            </div>
            """
            folium.Marker(
                [lat, lon],
                popup=f"<b>{occ['tipo']}</b><br>Status: {occ['status']}",
                icon=folium.DivIcon(html=html)
            ).add_to(m)
    return m

# =============================================================================
# FUNÇÃO PARA MAPA DO DASHBOARD
# =============================================================================
def criar_mapa_dashboard(df):
    m = folium.Map(location=[-3.119, -60.021], zoom_start=11.5, tiles="CartoDB positron")
    for _, row in df.iterrows():
        try:
            lat, lon = float(row['latitude']), float(row['longitude'])
            cor = CORES_RISCO_PINO.get(row.get('risco_padrao', 'MÉDIO'), 'gray')
            folium.Marker(
                [lat, lon],
                tooltip=f"{row.get('tipo', 'Ocorrência')} - {row.get('bairro', '')}",
                icon=folium.Icon(color=cor)
            ).add_to(m)
        except:
            continue
    return m

# =============================================================================
# TELAS DO SISTEMA
# =============================================================================
def tela_login():
    with st.container():
        _, col_centro, _ = st.columns([1, 1, 1])
        with col_centro:
            st.markdown("<div class='card-branco' style='margin-top: 15vh; text-align: center;'>", unsafe_allow_html=True)
            st.image(ASSETS_URL, width=130)
            st.markdown("<h2 style='margin-top: 0.5rem; color:#0B0B2A;'>DEFESA CIVIL</h2>", unsafe_allow_html=True)
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
    _, col_centro, _ = st.columns([1, 1, 1])
    with col_centro:
        st.markdown("<div class='card-branco' style='margin-top: 15vh; text-align: center;'>", unsafe_allow_html=True)
        st.image(ASSETS_URL, width=130)
        st.markdown("<h2 style='color:#0B0B2A;'>DEFESA CIVIL</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #FF8C00;'>BEM-VINDO AO PORTAL OPERACIONAL</p>", unsafe_allow_html=True)
        st.markdown("---")

        if st.button("📝 REGISTRAR OCORRÊNCIA", type="secondary", use_container_width=True):
            navegar("registro")
        if st.button("📊 PAINEL DE MONITORAMENTO", type="secondary", use_container_width=True):
            navegar("dashboard")
        st.write("")
        if st.button("ENCERRAR SESSÃO", type="primary", use_container_width=True):
            st.session_state["autenticado"] = False
            st.session_state["ocorrencias_sessao"] = []
            st.session_state["cont_andamento"] = 0
            st.session_state["cont_finalizado"] = 0
            navegar("login")
        st.markdown("</div>", unsafe_allow_html=True)

def tela_registro():
    cabecalho_com_voltar("CENTRAL DE MONITORAMENTO - REGISTRO E DESPACHO")

    col_form, col_monitor, col_mapa = st.columns([1.5, 1.5, 2.5])

    # --- COLUNA MAPA ---
    with col_mapa:
        def _conteudo_mapa():
            st.markdown("<p style='font-weight:600;'>📍 Clique no mapa para capturar coordenada</p>")
            
            # Gerar mapa
            m = criar_mapa_registro()
            mapa_clicado = st_folium(m, height=500, use_container_width=True, key="mapa_registro")
            
            if mapa_clicado and mapa_clicado.get("last_clicked"):
                lat = mapa_clicado["last_clicked"]["lat"]
                lon = mapa_clicado["last_clicked"]["lng"]
                if mapa_clicado.get("center"):
                    st.session_state["map_center"] = [mapa_clicado["center"]["lat"], mapa_clicado["center"]["lng"]]
                if mapa_clicado.get("zoom"):
                    st.session_state["map_zoom"] = mapa_clicado["zoom"]
                
                if lat != st.session_state["lat_capturada"]:
                    st.session_state["lat_capturada"] = lat
                    st.session_state["lon_capturada"] = lon
                    st.session_state["endereco_capturado"] = buscar_endereco_por_coordenada(lat, lon)
                    st.rerun()
            
            if st.session_state["lat_capturada"]:
                st.success("✅ GPS capturado")
        cartao("MAPA TÁTICO", _conteudo_mapa)

    # --- COLUNA FORMULÁRIO ---
    with col_form:
        def _conteudo_form():
            solicitante = st.text_input("SOLICITANTE", placeholder="Nome completo")
            municipio = st.text_input("MUNICÍPIO", value="Manaus")
            bairro = st.text_input("BAIRRO", placeholder="Bairro da ocorrência")
            
            # Linha com campo de logradouro e botão de busca
            col_log, col_busca = st.columns([5, 1])
            with col_log:
                logradouro = st.text_input("LOGRADOURO", value=st.session_state["endereco_capturado"], key="logradouro_input")
            with col_busca:
                st.markdown("<div style='margin-top: 1.5rem;'>", unsafe_allow_html=True)
                if st.button("🔍", key="btn_busca"):
                    if logradouro:
                        resultado = pesquisar_endereco(logradouro)
                        if resultado:
                            lat, lon, display = resultado
                            st.session_state["lat_capturada"] = lat
                            st.session_state["lon_capturada"] = lon
                            st.session_state["endereco_capturado"] = display
                            st.session_state["map_center"] = [lat, lon]
                            st.session_state["map_zoom"] = 17
                            st.rerun()
                        else:
                            st.warning("Endereço não encontrado")
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Número com checkbox
            col_num, col_chk_num = st.columns([2, 1])
            with col_num:
                numero = st.text_input("NÚMERO", placeholder="Nº", disabled=st.session_state.get("sem_numero", False))
            with col_chk_num:
                sem_numero = st.checkbox("Sem número", key="sem_numero")
            
            # Complemento com checkbox
            col_comp, col_chk_comp = st.columns([2, 1])
            with col_comp:
                complemento = st.text_input("COMPLEMENTO", placeholder="Ex: Apto 101", disabled=st.session_state.get("sem_complemento", False))
            with col_chk_comp:
                sem_complemento = st.checkbox("Sem compl.", key="sem_complemento")
            
            col_nat, col_ris = st.columns(2)
            natureza = col_nat.selectbox("NATUREZA", ["Alagamento", "Incêndio", "Deslizamento", "Desabamento", "Outros"])
            risco = col_ris.selectbox("GRAU DE RISCO", ["BAIXO", "MÉDIO", "ALTO", "CRÍTICO"])
            
            agora = datetime.now()
            col_data, col_hora = st.columns(2)
            data_occ = col_data.date_input("DATA", agora)
            hora_occ = col_hora.time_input("HORA", agora.time())
            
            encaminhamento = st.selectbox("ENCAMINHAMENTO", ["Aguardando Triagem", "Polícia Militar", "Corpo de Bombeiros", "Defesa Civil Municipal"])
            
            if st.button("SALVAR OCORRÊNCIA", type="primary", use_container_width=True):
                if not bairro or not logradouro:
                    st.warning("Preencha bairro e logradouro.")
                elif not st.session_state["lat_capturada"]:
                    st.warning("Clique no mapa para capturar a coordenada.")
                else:
                    if not verificar_conexao():
                        st.error("Sem conexão com a internet. Verifique a rede do quartel.")
                        return
                    
                    num_final = "S/N" if sem_numero else (numero if numero else "")
                    comp_final = "" if sem_complemento else (f" - {complemento}" if complemento else "")
                    end_completo = f"{logradouro}, {num_final}{comp_final}".strip(" ,-")
                    
                    dados = {
                        "tipo": natureza,
                        "municipio": municipio,
                        "bairro": bairro,
                        "endereco": end_completo,
                        "risco": risco,
                        "encaminhamento": encaminhamento,
                        "data": data_occ.strftime("%d/%m/%Y"),
                        "hora": hora_occ.strftime("%H:%M:%S"),
                        "solicitante": solicitante,
                        "status": "Em andamento",
                        "latitude": st.session_state["lat_capturada"],
                        "longitude": st.session_state["lon_capturada"],
                        "operador": "Operador"
                    }
                    try:
                        ref = obter_referencia("ocorrencias")
                        novo_reg = ref.push(dados)
                        firebase_id = novo_reg.key
                        
                        adicionar_ocorrencia_sessao(
                            tipo=natureza,
                            risco=risco,
                            lat=st.session_state["lat_capturada"],
                            lon=st.session_state["lon_capturada"],
                            endereco=end_completo,
                            id_firebase=firebase_id
                        )
                        
                        st.success("Ocorrência salva com sucesso!")
                        st.balloons()
                        st.session_state["endereco_capturado"] = ""
                        st.session_state["lat_capturada"] = None
                        st.session_state["lon_capturada"] = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
        cartao("DADOS CADASTRAIS", _conteudo_form)

    # --- COLUNA MONITORAMENTO ---
    with col_monitor:
        renderizar_monitoramento_turno()

def tela_dashboard():
    df = carregar_dados()
    if df.empty:
        st.info("Sincronizando base de dados...")
        return

    cabecalho_com_voltar("PAINEL TÁTICO - MONITORAMENTO DE OCORRÊNCIAS", is_dashboard=True)

    # Filtros
    with st.container():
        st.markdown("<div class='card-branco'>", unsafe_allow_html=True)
        c_f1, c_f2, c_f3, c_f4, c_f5 = st.columns(5)
        f_tipo = c_f1.selectbox("NATUREZA", ["Todas"] + sorted(df['tipo'].dropna().unique().tolist()))
        f_mun = c_f2.selectbox("MUNICÍPIO", ["Todas"] + sorted(df['municipio'].dropna().unique().tolist()))
        f_bairro = c_f3.selectbox("BAIRRO", ["Todos"] + sorted(df['bairro'].dropna().unique().tolist()))
        f_ano = c_f4.selectbox("ANO", ["Todos"] + sorted([a for a in df['Ano_Filtro'].unique() if a != 'Desconhecido']))
        f_mes = c_f5.selectbox("MÊS", ["Todos"] + sorted([m for m in df['Mes_Filtro'].unique() if m != 'Desconhecido']))
        st.markdown("</div>", unsafe_allow_html=True)

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
        # Tabela Natureza
        def _graf_natureza():
            if not df_filtrado.empty:
                contagem = df_filtrado['tipo_emoji'].value_counts().reset_index()
                contagem.columns = ['NATUREZA', 'QUANTIDADE']
                st.dataframe(contagem, hide_index=True, use_container_width=True, height=200)
        cartao("NATUREZA", _graf_natureza)

        # Tabela Encaminhamento
        def _graf_encaminhamento():
            if not df_filtrado.empty:
                contagem = df_filtrado['encaminhamento'].value_counts().reset_index()
                contagem.columns = ['ENCAMINHAMENTO', 'QUANTIDADE']
                st.dataframe(contagem, hide_index=True, use_container_width=True, height=200)
        cartao("ENCAMINHAMENTO", _graf_encaminhamento)

        col_tot, col_pie = st.columns([1, 1.5])
        with col_tot:
            def _total():
                st.metric("Total de Registros", len(df_filtrado))
            cartao("TOTAL", _total)
        with col_pie:
            def _risco():
                if not df_filtrado.empty and 'risco_padrao' in df_filtrado.columns:
                    fig = px.pie(
                        df_filtrado['risco_padrao'].value_counts().reset_index(),
                        values='count',
                        names='risco_padrao',
                        hole=0.4,
                        color='risco_padrao',
                        color_discrete_map=CORES_RISCO_HEX
                    )
                    fig.update_layout(
                        height=140,
                        margin=dict(t=0, b=0, l=0, r=0),
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#333')
                    )
                    st.plotly_chart(fig, use_container_width=True, theme=None)
                else:
                    st.info("Sem dados")
            cartao("NÍVEL DE RISCO", _risco)

    with col_dir:
        # Mapa
        def _mapa():
            m = criar_mapa_dashboard(df_filtrado)
            st_folium(m, use_container_width=True, height=300)
        cartao("MAPA OPERACIONAL", _mapa)

        # Gráfico de barras mensal
        def _grafico_mes():
            df_mes = df_filtrado[df_filtrado['Mes_Filtro'] != 'Desconhecido']
            if not df_mes.empty:
                # Ordem dos meses
                ordem_meses = ['01','02','03','04','05','06','07','08','09','10','11','12']
                contagem = df_mes['Mes_Filtro'].value_counts().reindex(ordem_meses, fill_value=0).reset_index()
                contagem.columns = ['Mês', 'Quantidade']
                # Mapear números para nomes
                nomes = {'01':'Jan','02':'Fev','03':'Mar','04':'Abr','05':'Mai','06':'Jun',
                         '07':'Jul','08':'Ago','09':'Set','10':'Out','11':'Nov','12':'Dez'}
                contagem['Mês'] = contagem['Mês'].map(nomes)
                fig = px.bar(contagem, x='Mês', y='Quantidade', text='Quantidade')
                fig.update_traces(marker_color='#191970', textposition='outside')
                fig.update_layout(
                    height=180,
                    margin=dict(t=0, b=0, l=0, r=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#333'),
                    xaxis_title=None,
                    yaxis_title=None
                )
                st.plotly_chart(fig, use_container_width=True, theme=None)
            else:
                st.info("Sem dados mensais")
        cartao("EVOLUÇÃO MENSAL", _grafico_mes)

# =============================================================================
# ROTEADOR PRINCIPAL
# =============================================================================
def main():
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
        else:
            navegar("hub")

if __name__ == "__main__":
    main()
