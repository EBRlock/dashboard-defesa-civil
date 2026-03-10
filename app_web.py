"""
SISTEMA INTEGRADO DE GESTÃO DA DEFESA CIVIL
Versão 3.0 - Monitoramento de Turno e Mapa Avançado
Autor: Defesa Civil AM / DTI
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

CORES_RISCO_HEX = {'ALTO': '#F97316', 'MÉDIO': '#EAB308', 'MEDIO': '#EAB308', 'BAIXO': '#22C55E', 'CRÍTICO': '#EF4444', 'CRITICO': '#EF4444'}
CORES_RISCO_PINO = {'ALTO': 'orange', 'MÉDIO': 'beige', 'MEDIO': 'beige', 'BAIXO': 'green', 'CRÍTICO': 'red', 'CRITICO': 'red'}
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
        "ocorrencias_sessao": [],          # Lista de ocorrências do turno atual
        "cont_andamento": 0,
        "cont_finalizado": 0,
        "ultima_busca_coord": None,        # Para manter o marcador de busca
        "conexao_verificada": None          # Cache da verificação de internet
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
    if 'INCÊNDIO' in tipo_upper: return f"🔥 {tipo}"
    if 'DESLIZAMENTO' in tipo_upper: return f"⛰️ {tipo}"
    if 'ALAGAMENTO' in tipo_upper: return f"🌊 {tipo}"
    if 'DESABAMENTO' in tipo_upper: return f"🏚️ {tipo}"
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
    try:
        ref = obter_referencia("ocorrencias")
        dados = ref.get()
        if not dados: return pd.DataFrame()

        if isinstance(dados, list):
            dados_dict = {str(i): v for i, v in enumerate(dados) if v is not None}
            df = pd.DataFrame.from_dict(dados_dict, orient='index')
        else:
            df = pd.DataFrame.from_dict(dados, orient='index')

        colunas_padrao = {'tipo': 'Não Informado', 'encaminhamento': 'Não Informado', 'risco': 'MÉDIO', 'data': '', 'bairro': 'Não Informado', 'municipio': 'Manaus', 'endereco': '', 'solicitante': 'Não Informado', 'status': 'Em andamento'}
        for col, padrao in colunas_padrao.items():
            if col not in df.columns: df[col] = padrao

        df['tipo_emoji'] = df['tipo'].apply(adicionar_emoji_natureza)
        df['encaminhamento'] = df['encaminhamento'].astype(str).str.strip()
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
# ESTILOS CSS INSTITUCIONAIS (idêntico ao anterior, mas com ajustes para os novos elementos)
# =============================================================================
def aplicar_css_global():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
        .stApp { background-color: #0B0B2A !important; }
        .block-container { padding-top: 1.5rem !important; padding-bottom: 1.5rem !important; max-width: 95% !important; }
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, .stText, .stNumberInput, .stSelectbox, .stDateInput, .stTimeInput { color: #FFFFFF !important; font-family: 'Segoe UI', Roboto, Arial, sans-serif !important; }
        
        .barra-superior {
            background-color: #0B0B2A; color: #FFFFFF; padding: 0.8rem 1.5rem; border-radius: 8px;
            font-weight: 700; font-size: 1.3rem; text-transform: uppercase; letter-spacing: 1px;
            border-left: 6px solid #FF8C00; box-shadow: 0 4px 10px rgba(0,0,0,0.3); margin-bottom: 1.5rem;
            display: flex; justify-content: space-between; align-items: center;
        }

        .card-escuro { background-color: rgba(20, 20, 50, 0.7) !important; backdrop-filter: blur(2px); border-radius: 12px; padding: 1.2rem 1.5rem; border: 1px solid rgba(255,255,255,0.15); box-shadow: 0 8px 16px rgba(0,0,0,0.4); height: 100%; }
        .titulo-cartao { font-size: 0.9rem; font-weight: 800; color: #FF8C00 !important; text-transform: uppercase; letter-spacing: 1px; border-bottom: 2px solid #FF8C00; padding-bottom: 0.4rem; margin-bottom: 1rem; }
        
        .stTextInput>div>div>input, .stNumberInput>div>div>input, .stDateInput>div>div>input, .stTimeInput>div>div>input, div[data-baseweb="select"]>div { background-color: #1E1E3F !important; border: 1px solid #3A3A6E !important; border-radius: 8px !important; color: #FFFFFF !important; font-size: 0.95rem !important; }
        div[data-baseweb="select"] * { color: #FFFFFF !important; }
        ul[data-baseweb="menu"] { background-color: #1E1E3F !important; border: 1px solid #3A3A6E !important; }
        li[role="option"] { color: #FFFFFF !important; }
        li[role="option"]:hover { background-color: #2D2D5A !important; }
        
        div.stButton > button[kind="secondary"] { background-color: #1E1E3F !important; color: #FFFFFF !important; border: 1px solid #3A3A6E !important; font-weight: 600 !important; border-radius: 8px !important; height: 2.8rem !important; transition: all 0.2s; }
        div.stButton > button[kind="secondary"]:hover { background-color: #2D2D5A !important; border-color: #FF8C00 !important; }
        div.stButton > button[kind="primary"] { background-color: #FF8C00 !important; color: #FFFFFF !important; font-weight: 700 !important; border: none !important; border-radius: 8px !important; height: 3rem !important; box-shadow: 0 4px 10px rgba(255,140,0,0.3); }
        div.stButton > button[kind="primary"]:hover { background-color: #E67E00 !important; }
        
        /* Botão finalizar (pequeno) */
        .botao-finalizar {
            background-color: #1976D2 !important;
            color: white !important;
            border: none !important;
            border-radius: 4px !important;
            padding: 5px 10px !important;
            font-size: 0.8rem !important;
            font-weight: bold !important;
            cursor: pointer;
            width: 100%;
        }
        .botao-finalizar:hover { background-color: #1565C0 !important; }
        .botao-finalizar:disabled { background-color: #E0E0E0 !important; color: #888 !important; }
        
        div[data-testid="metric-container"] { background-color: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 10px !important; padding: 0.8rem !important; text-align: center; }
        div[data-testid="stMetricValue"] > div { color: #FF8C00 !important; font-size: 2rem !important; font-weight: 900 !important; }
        [data-testid="stDataFrame"] { background-color: #1E1E3F !important; border-radius: 8px; }
        hr { border-color: rgba(255,255,255,0.2) !important; margin: 1rem 0 !important; }
        
        /* Estilo para os itens do monitoramento */
        .linha-monitor {
            background-color: rgba(255,255,255,0.05);
            border-radius: 4px;
            padding: 0.5rem;
            margin-bottom: 0.3rem;
            border-left: 3px solid;
        }
        .status-andamento { color: #F57C00; font-weight: bold; }
        .status-finalizado { color: #2E7D32; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

# =============================================================================
# COMPONENTES REUTILIZÁVEIS
# =============================================================================
def cabecalho_com_voltar(titulo: str, rota_destino: str = "hub", is_dashboard=False):
    col_voltar, col_titulo = st.columns([1, 10])
    with col_voltar:
        if st.button("⬅ VOLTAR", type="secondary", use_container_width=True): navegar(rota_destino)
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
        st.markdown(f"<div class='card-escuro'>", unsafe_allow_html=True)
        st.markdown(f"<div class='titulo-cartao'>{titulo}</div>", unsafe_allow_html=True)
        conteudo()
        st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# FUNÇÕES DE MONITORAMENTO DE TURNO
# =============================================================================
def adicionar_ocorrencia_sessao(tipo, risco, lat, lon, endereco, id_firebase=None):
    """Adiciona uma ocorrência à lista da sessão (turno atual)"""
    ocorrencia = {
        "id": len(st.session_state["ocorrencias_sessao"]),
        "tipo": tipo,
        "risco": risco,
        "lat": lat,
        "lon": lon,
        "endereco": endereco,
        "status": "Em andamento",
        "firebase_id": id_firebase  # para possível atualização futura
    }
    st.session_state["ocorrencias_sessao"].append(ocorrencia)
    st.session_state["cont_andamento"] += 1

def finalizar_ocorrencia_sessao(indice):
    """Muda status da ocorrência para 'Finalizado' e atualiza Firebase se houver ID"""
    ocorrencia = st.session_state["ocorrencias_sessao"][indice]
    if ocorrencia["status"] == "Em andamento":
        ocorrencia["status"] = "Finalizado"
        st.session_state["cont_andamento"] -= 1
        st.session_state["cont_finalizado"] += 1
        # Se tiver ID no Firebase, atualiza lá também
        if ocorrencia.get("firebase_id"):
            try:
                ref = obter_referencia(f"ocorrencias/{ocorrencia['firebase_id']}")
                ref.update({"status": "Finalizado"})
            except Exception as e:
                st.warning(f"Erro ao atualizar Firebase: {e}")

def renderizar_monitoramento_turno():
    """Exibe os contadores e a lista de ocorrências da sessão com botões Finalizar"""
    st.markdown(f"<div class='card-escuro'>", unsafe_allow_html=True)
    st.markdown("<div class='titulo-cartao'>MONITORAMENTO DO TURNO</div>", unsafe_allow_html=True)
    
    # Placar
    col1, col2 = st.columns(2)
    with col1:
        st.metric("EM ANDAMENTO", st.session_state["cont_andamento"])
    with col2:
        st.metric("FINALIZADOS", st.session_state["cont_finalizado"])
    
    st.markdown("---")
    
    # Cabeçalho da tabela
    cabecalho = st.columns([2, 1, 1.5, 1])
    cabecalho[0].markdown("**TIPO**")
    cabecalho[1].markdown("**RISCO**")
    cabecalho[2].markdown("**STATUS**")
    cabecalho[3].markdown("**AÇÃO**")
    
    # Lista de ocorrências
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
                cor = CORES_RISCO_HEX.get(risco.upper(), '#FFFFFF')
                st.markdown(f"<span style='color:{cor}; font-weight:bold;'>{risco}</span>", unsafe_allow_html=True)
            with cols[2]:
                status = occ['status']
                if status == "Em andamento":
                    st.markdown("<span class='status-andamento'>EM ANDAMENTO</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='status-finalizado'>FINALIZADO</span>", unsafe_allow_html=True)
            with cols[3]:
                if status == "Em andamento":
                    if st.button("FINALIZAR", key=f"fin_{i}", help="Finalizar ocorrência"):
                        finalizar_ocorrencia_sessao(i)
                        st.rerun()
                else:
                    st.button("FINALIZADO", disabled=True, key=f"fin_disabled_{i}")
    st.markdown("</div>", unsafe_allow_html=True)

# =============================================================================
# FUNÇÃO PARA CRIAR MAPA FOLIUM COM MARCADORES DA SESSÃO E DE BUSCA
# =============================================================================
def criar_mapa_registro():
    """Gera mapa Folium com marcadores de busca (azul) e ocorrências da sessão"""
    # Centro inicial: último centro salvo ou padrão
    center = st.session_state["map_center"]
    zoom = st.session_state["map_zoom"]
    
    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron")
    
    # Marcador de busca (se houver coordenada de busca)
    if st.session_state["lat_capturada"] and st.session_state["lon_capturada"]:
        folium.Marker(
            [st.session_state["lat_capturada"], st.session_state["lon_capturada"]],
            popup="Ponto selecionado",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)
    
    # Marcadores das ocorrências da sessão
    for occ in st.session_state["ocorrencias_sessao"]:
        lat = occ["lat"]
        lon = occ["lon"]
        if lat and lon:
            # Cor conforme status
            cor = "#F57C00" if occ["status"] == "Em andamento" else "#2E7D32"
            # Círculo de raio
            folium.Circle(
                radius=250,
                location=[lat, lon],
                color=cor,
                fill=True,
                fillOpacity=0.2,
                weight=2
            ).add_to(m)
            # Marcador com emoji
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
# TELAS DO SISTEMA
# =============================================================================
def tela_login():
    with st.container():
        _, col_centro, _ = st.columns([1, 1, 1])
        with col_centro:
            st.markdown("<div class='card-escuro' style='margin-top: 15vh; text-align: center;'>", unsafe_allow_html=True)
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
    _, col_centro, _ = st.columns([1, 1, 1])
    with col_centro:
        st.markdown("<div class='card-escuro' style='margin-top: 15vh; text-align: center;'>", unsafe_allow_html=True)
        st.image(ASSETS_URL, width=130)
        st.markdown("<h2>DEFESA CIVIL</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #FF8C00;'>BEM-VINDO AO PORTAL OPERACIONAL</p>", unsafe_allow_html=True)
        st.markdown("---")

        if st.button("📝 REGISTRAR OCORRÊNCIA", type="secondary", use_container_width=True): navegar("registro")
        if st.button("📊 PAINEL DE MONITORAMENTO", type="secondary", use_container_width=True): navegar("dashboard")
        st.write("")
        if st.button("ENCERRAR SESSÃO", type="primary", use_container_width=True):
            st.session_state["autenticado"] = False
            # Limpar dados da sessão (opcional)
            st.session_state["ocorrencias_sessao"] = []
            st.session_state["cont_andamento"] = 0
            st.session_state["cont_finalizado"] = 0
            navegar("login")
        st.markdown("</div>", unsafe_allow_html=True)

def tela_registro():
    cabecalho_com_voltar("CENTRAL DE MONITORAMENTO - REGISTRO E DESPACHO")

    col_form, col_monitor, col_mapa = st.columns([1.5, 1.5, 2.5])

    # --- COLUNA MAPA (interativo) ---
    with col_mapa:
        def _conteudo_mapa():
            st.markdown("<p style='font-weight:600;'>📍 Clique no mapa para capturar coordenada</p>")
            
            # Botão de busca de endereço
            with st.expander("🔍 Buscar endereço", expanded=False):
                busca = st.text_input("Digite o endereço", key="busca_endereco", label_visibility="collapsed")
                if st.button("Buscar no mapa", use_container_width=True):
                    if busca:
                        resultado = pesquisar_endereco(busca)
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
            
            # Gera o mapa com estado atual
            m = criar_mapa_registro()
            mapa_clicado = st_folium(m, height=500, use_container_width=True, key="mapa_registro")
            
            # Processa clique no mapa
            if mapa_clicado and mapa_clicado.get("last_clicked"):
                lat = mapa_clicado["last_clicked"]["lat"]
                lon = mapa_clicado["last_clicked"]["lng"]
                # Salva centro/zoom
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
            # SOLICITANTE
            solicitante = st.text_input("SOLICITANTE", placeholder="Nome completo")
            municipio = st.text_input("MUNICÍPIO", value="Manaus")
            bairro = st.text_input("BAIRRO", placeholder="Bairro da ocorrência")
            endereco = st.text_input("LOGRADOURO", value=st.session_state["endereco_capturado"], key="logradouro")
            
            # Número com checkbox "Sem número"
            col_num, col_chk_num = st.columns([2, 1])
            with col_num:
                numero = st.text_input("NÚMERO", placeholder="Nº", disabled=st.session_state.get("sem_numero", False))
            with col_chk_num:
                sem_numero = st.checkbox("Sem número", key="sem_numero", help="Marcar se não houver número")
            
            # Complemento com checkbox "Sem complemento"
            col_comp, col_chk_comp = st.columns([2, 1])
            with col_comp:
                complemento = st.text_input("COMPLEMENTO", placeholder="Ex: Apto 101", disabled=st.session_state.get("sem_complemento", False))
            with col_chk_comp:
                sem_complemento = st.checkbox("Sem compl.", key="sem_complemento")
            
            # Natureza e risco
            col_nat, col_ris = st.columns(2)
            natureza = col_nat.selectbox("NATUREZA", ["Alagamento", "Incêndio", "Deslizamento", "Desabamento", "Outros"])
            risco = col_ris.selectbox("GRAU DE RISCO", ["BAIXO", "MÉDIO", "ALTO", "CRÍTICO"])
            
            # Data e hora (pré-preenchidas)
            agora = datetime.now()
            col_data, col_hora = st.columns(2)
            data_occ = col_data.date_input("DATA", agora)
            hora_occ = col_hora.time_input("HORA", agora.time())
            
            # Encaminhamento
            encaminhamento = st.selectbox("ENCAMINHAMENTO", ["Aguardando Triagem", "Polícia Militar", "Corpo de Bombeiros", "Defesa Civil Municipal"])
            
            if st.button("SALVAR OCORRÊNCIA", type="primary", use_container_width=True):
                # Validações
                if not bairro or not endereco:
                    st.warning("Preencha bairro e logradouro.")
                elif not st.session_state["lat_capturada"]:
                    st.warning("Clique no mapa para capturar a coordenada.")
                else:
                    # Verifica conexão
                    if not verificar_conexao():
                        st.error("Sem conexão com a internet. Verifique a rede do quartel.")
                        return
                    
                    # Monta endereço completo
                    num_final = "S/N" if sem_numero else (numero if numero else "")
                    comp_final = "" if sem_complemento else (f" - {complemento}" if complemento else "")
                    end_completo = f"{endereco}, {num_final}{comp_final}".strip(" ,-")
                    
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
                        "operador": "Operador"  # Poderia vir da sessão
                    }
                    try:
                        # Salva no Firebase
                        ref = obter_referencia("ocorrencias")
                        novo_reg = ref.push(dados)
                        firebase_id = novo_reg.key
                        
                        # Adiciona ao monitoramento da sessão
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
                        
                        # Limpa campos de captura (mantém o mapa na mesma posição)
                        st.session_state["endereco_capturado"] = ""
                        st.session_state["lat_capturada"] = None
                        st.session_state["lon_capturada"] = None
                        # Recarrega para limpar o formulário
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
        cartao("DADOS CADASTRAIS", _conteudo_form)

    # --- COLUNA MONITORAMENTO (turno) ---
    with col_monitor:
        renderizar_monitoramento_turno()

def tela_dashboard():
    df = carregar_dados()
    if df.empty:
        st.info("Sincronizando base de dados...")
        return

    cabecalho_com_voltar("PAINEL TÁTICO - MONITORAMENTO DE OCORRÊNCIAS", is_dashboard=True)

    with st.container():
        st.markdown("<div class='card-escuro'>", unsafe_allow_html=True)
        c_f1, c_f2, c_f3, c_f4, c_f5 = st.columns(5)
        f_tipo = c_f1.selectbox("NATUREZA", ["Todas"] + sorted(df['tipo'].dropna().unique().tolist()))
        f_mun = c_f2.selectbox("MUNICÍPIO", ["Todas"] + sorted(df['municipio'].dropna().unique().tolist()))
        f_bairro = c_f3.selectbox("BAIRRO", ["Todos"] + sorted(df['bairro'].dropna().unique().tolist()))
        f_ano = c_f4.selectbox("ANO", ["Todos"] + sorted([a for a in df['Ano_Filtro'].unique() if a != 'Desconhecido']))
        f_mes = c_f5.selectbox("MÊS", ["Todos"] + sorted([m for m in df['Mes_Filtro'].unique() if m != 'Desconhecido']))
        st.markdown("</div>", unsafe_allow_html=True)

    df_filtrado = df.copy()
    if f_tipo != "Todas": df_filtrado = df_filtrado[df_filtrado['tipo'] == f_tipo]
    if f_mun != "Todas": df_filtrado = df_filtrado[df_filtrado['municipio'] == f_mun]
    if f_bairro != "Todas": df_filtrado = df_filtrado[df_filtrado['bairro'] == f_bairro]
    if f_ano != "Todas": df_filtrado = df_filtrado[df_filtrado['Ano_Filtro'] == f_ano]
    if f_mes != "Todas": df_filtrado = df_filtrado[df_filtrado['Mes_Filtro'] == f_mes]

    col_esq, col_dir = st.columns([1, 1.8])

    with col_esq:
        def _graf_natureza(): st.dataframe(df_filtrado['tipo_emoji'].value_counts().reset_index(), hide_index=True, use_container_width=True, height=200)
        cartao("NATUREZA", _graf_natureza)

        def _graf_encaminhamento(): st.dataframe(df_filtrado['encaminhamento'].value_counts().reset_index(), hide_index=True, use_container_width=True, height=200)
        cartao("ENCAMINHAMENTO", _graf_encaminhamento)

        col_tot, col_pie = st.columns([1, 1.5])
        with col_tot:
            def _total(): st.metric("", len(df_filtrado))
            cartao("TOTAL", _total)
        with col_pie:
            def _risco():
                fig = px.pie(df_filtrado['risco_padrao'].value_counts().reset_index(), values='count', names='risco_padrao', hole=0.4, color='risco_padrao', color_discrete_map=CORES_RISCO_HEX)
                fig.update_layout(height=140, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
                st.plotly_chart(fig, use_container_width=True, theme=None)
            cartao("RISCO", _risco)

    with col_dir:
        def _mapa():
            m = folium.Map(location=[-3.119, -60.021], zoom_start=11.5, tiles="CartoDB positron")
            for _, row in df_filtrado.iterrows():
                try:
                    lat, lon = float(row['latitude']), float(row['longitude'])
                    cor = CORES_RISCO_PINO.get(row.get('risco_padrao', 'MÉDIO'), 'gray')
                    folium.Marker([lat, lon], tooltip=row.get('tipo', 'Ocorrência'), icon=folium.Icon(color=cor)).add_to(m)
                except Exception: continue
            st_folium(m, use_container_width=True, height=300)
        cartao("MAPA OPERACIONAL", _mapa)

        def _grafico_mes():
            df_mes = df_filtrado[df_filtrado['Mes_Filtro'] != 'Desconhecido']
            if not df_mes.empty:
                fig = px.bar(df_mes['Mes_Filtro'].value_counts().reset_index().sort_values(by='Mes_Filtro'), x='Mes_Filtro', y='count')
                fig.update_traces(marker_color='#FF8C00')
                fig.update_layout(height=150, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
                st.plotly_chart(fig, use_container_width=True, theme=None)
            else: st.info("Sem dados mensais")
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
        if rota == "hub": tela_hub()
        elif rota == "dashboard": tela_dashboard()
        elif rota == "registro": tela_registro()
        else: navegar("hub")

if __name__ == "__main__":
    main()
