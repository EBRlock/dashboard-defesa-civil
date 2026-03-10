"""
SISTEMA INTEGRADO DE GESTÃO DA DEFESA CIVIL
Versão 2.1 - Refatoração Institucional Otimizada
Autor: Defesa Civil AM / DTI
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
st.set_page_config(page_title="Sistema Defesa Civil", layout="wide", initial_sidebar_state="collapsed")

CREDENCIAIS = {
    "gestaodefesacivil": "defesacivilam26",
    "admin": "1234"
}

CORES_RISCO_HEX = {'ALTO': '#F97316', 'MÉDIO': '#EAB308', 'MEDIO': '#EAB308', 'BAIXO': '#22C55E', 'CRÍTICO': '#EF4444', 'CRITICO': '#EF4444'}
CORES_RISCO_PINO = {'ALTO': 'orange', 'MÉDIO': 'beige', 'MEDIO': 'beige', 'BAIXO': 'green', 'CRÍTICO': 'red', 'CRITICO': 'red'}
ASSETS_URL = "https://raw.githubusercontent.com/EBRlock/dashboard-defesa-civil/main/assets/logo_defesa.png"

# =============================================================================
# INICIALIZAÇÃO DA SESSÃO (Memória do Mapa Adicionada)
# =============================================================================
def inicializar_sessao():
    defaults = {
        "autenticado": False,
        "rota": "login",
        "endereco_capturado": "",
        "lat_capturada": None,
        "lon_capturada": None,
        "map_center": [-3.119, -60.021], # Memória do centro do mapa
        "map_zoom": 12 # Memória do zoom do mapa
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
        headers = {'User-Agent': 'DefesaCivilAM/2.0'}
        resposta = requests.get(url, headers=headers, timeout=5).json()
        return resposta.get('display_name', 'Endereço não encontrado')
    except Exception: return ""

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
        df['encaminhamento'] = df['encaminhamento'].astype(str).str.strip() # Correção do Dashboard
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
# ESTILOS CSS INSTITUCIONAIS (Intacto)
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
        
        div[data-testid="metric-container"] { background-color: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 10px !important; padding: 0.8rem !important; text-align: center; }
        div[data-testid="stMetricValue"] > div { color: #FF8C00 !important; font-size: 2rem !important; font-weight: 900 !important; }
        [data-testid="stDataFrame"] { background-color: #1E1E3F !important; border-radius: 8px; }
        hr { border-color: rgba(255,255,255,0.2) !important; margin: 1rem 0 !important; }
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
            # Insere o botão de exportar PDF via Javascript (Impressão) no Dashboard
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
# TELAS DO SISTEMA
# =============================================================================
def tela_login():
    with st.container():
        # Centralização exata com colunas proporcionais
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
        
        # Botão Administrativo removido conforme solicitado

        st.write("")
        if st.button("ENCERRAR SESSÃO", type="primary", use_container_width=True):
            st.session_state["autenticado"] = False; navegar("login")
        st.markdown("</div>", unsafe_allow_html=True)

def tela_registro():
    cabecalho_com_voltar("CENTRAL DE MONITORAMENTO - REGISTRO E DESPACHO")

    col_form, col_meio, col_mapa = st.columns([1.5, 1, 2.5])

    # MAPA COM PRESERVAÇÃO DE ESTADO
    with col_mapa:
        def _conteudo_mapa():
            st.markdown("<p style='font-weight:600;'>📍 Toque no mapa para capturar a coordenada</p>", unsafe_allow_html=True)
            
            m_registro = folium.Map(location=st.session_state["map_center"], zoom_start=st.session_state["map_zoom"], tiles="CartoDB positron")

            if st.session_state["lat_capturada"] and st.session_state["lon_capturada"]:
                folium.Marker([st.session_state["lat_capturada"], st.session_state["lon_capturada"]], icon=folium.Icon(color="red", icon="map-marker")).add_to(m_registro)

            mapa_clicado = st_folium(m_registro, height=560, use_container_width=True, key="mapa_novo")

            if mapa_clicado and mapa_clicado.get("last_clicked"):
                lat, lon = mapa_clicado["last_clicked"]["lat"], mapa_clicado["last_clicked"]["lng"]
                st.session_state["map_center"] = [mapa_clicado["center"]["lat"], mapa_clicado["center"]["lng"]]
                st.session_state["map_zoom"] = mapa_clicado["zoom"]
                
                if lat != st.session_state["lat_capturada"]:
                    st.session_state["lat_capturada"] = lat; st.session_state["lon_capturada"] = lon
                    st.session_state["endereco_capturado"] = buscar_endereco_por_coordenada(lat, lon)
                    st.rerun()

            if st.session_state["lat_capturada"]: st.success("✅ GPS capturado com sucesso!")
        cartao("MAPA DE CAPTURA", _conteudo_mapa)

    # FORMULÁRIO (Herança do form_ocorrencia.py)
    with col_form:
        def _conteudo_form():
            c_solic, c_tel = st.columns([2, 1])
            with c_solic:
                solicitante = st.text_input("SOLICITANTE", placeholder="Nome completo")
            with c_tel:
                telefone = st.text_input("TELEFONE", placeholder="(99) 99999-9999")
                
            municipio = st.text_input("MUNICÍPIO", value="Manaus")
            bairro = st.text_input("BAIRRO", placeholder="Bairro da ocorrência")
            endereco = st.text_input("LOGRADOURO", value=st.session_state["endereco_capturado"])

            c_num, c_comp = st.columns([1, 2])
            with c_num:
                sem_numero = st.checkbox("Sem número", key="chk_num")
                numero = st.text_input("NÚMERO", placeholder="Nº", disabled=sem_numero)
            with c_comp:
                sem_comp = st.checkbox("Sem complemento", key="chk_comp")
                complemento = st.text_input("COMPLEMENTO", placeholder="Ex: Apto 101", disabled=sem_comp)

            c_nat, c_ris = st.columns(2)
            natureza = c_nat.selectbox("NATUREZA DA OCORRÊNCIA", ["Alagamento", "Incêndio", "Deslizamento", "Desabamento", "Outros"])
            risco = c_ris.selectbox("GRAU DE RISCO", ["BAIXO", "MÉDIO", "ALTO", "CRÍTICO"])

            c_data, c_hora = st.columns(2)
            data_ocorrencia = c_data.date_input("DATA", datetime.now())
            hora_ocorrencia = c_hora.time_input("HORA", datetime.now().time())

            status_op = st.selectbox("STATUS DA OCORRÊNCIA", ["Em andamento", "Finalizado"])
            encaminhamento = st.selectbox("ENCAMINHAMENTO", ["Aguardando Triagem", "Polícia Militar", "Corpo de Bombeiros", "Defesa Civil Municipal"])

            if st.button("SALVAR OCORRÊNCIA", type="primary", use_container_width=True):
                # Validação rigorosa igual ao PyQt6
                if not bairro or not endereco: st.warning("Preencha o bairro e o logradouro.")
                elif not st.session_state["lat_capturada"]: st.warning("Toque no mapa para capturar a coordenada GPS!")
                else:
                    num_final = "S/N" if sem_numero else numero
                    comp_final = "" if sem_comp else f" - {complemento}"
                    end_completo = f"{endereco}, {num_final}{comp_final}".strip(" ,-")
                    
                    # Dicionário idêntico ao do form_ocorrencia.py
                    novo_registro = {
                        "tipo": natureza, 
                        "municipio": municipio, 
                        "bairro": bairro, 
                        "endereco": end_completo,
                        "risco": risco, 
                        "encaminhamento": encaminhamento, 
                        "data": data_ocorrencia.strftime("%d/%m/%Y"),
                        "solicitante": solicitante, 
                        "telefone": telefone, # O campo que trouxemos de volta!
                        "status": status_op, 
                        "latitude": st.session_state["lat_capturada"], 
                        "longitude": st.session_state["lon_capturada"]
                    }
                    try:
                        obter_referencia("ocorrencias").push(novo_registro)
                        st.success("Ocorrência salva com sucesso no banco Firebase!"); st.balloons()
                        carregar_dados.clear()
                        # Limpa os campos visuais igual ao `self.clear()` do Desktop
                        st.session_state["endereco_capturado"] = ""
                        st.session_state["lat_capturada"] = None
                        st.session_state["lon_capturada"] = None
                        st.rerun()
                    except Exception as e: st.error(f"Erro ao salvar: {e}")
        cartao("DADOS CADASTRAIS", _conteudo_form)

    # MONITORAMENTO DO TURNO DINÂMICO
    with col_meio:
        def _conteudo_monitoramento():
            df = carregar_dados()
            hoje = datetime.now().strftime("%d/%m/%Y")
            
            qtd_andamento, qtd_finalizados = 0, 0
            if not df.empty and 'status' in df.columns:
                df_hoje = df[df['data'] == hoje]
                qtd_andamento = len(df_hoje[df_hoje['status'] == 'Em andamento'])
                qtd_finalizados = len(df_hoje[df_hoje['status'] == 'Finalizado'])

            c_and, c_fin = st.columns(2)
            c_and.metric("EM ANDAMENTO", qtd_andamento)
            c_fin.metric("FINALIZADOS", qtd_finalizados)
            st.markdown("---")
            st.markdown("<div style='font-size:0.8rem; background:#1E1E3F; padding:0.5rem; border-radius:6px;'><b>TIPO</b> &nbsp;&nbsp; <b>RISCO</b> &nbsp;&nbsp; <b>STATUS</b> &nbsp;&nbsp; <b>AÇÃO</b></div>", unsafe_allow_html=True)
        cartao("MONITORAMENTO DO TURNO", _conteudo_monitoramento)

def tela_dashboard():
    df = carregar_dados()
    if df.empty: st.info("Sincronizando base de dados..."); return

    # Flag True para adicionar o botão de PDF nativo na barra superior
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

        # Encaminhamento Corrigido
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

