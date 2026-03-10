import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime
import requests
from core.database import obter_referencia

# ==========================================
# 1. CONFIGURAÇÃO GERAL
# ==========================================
st.set_page_config(page_title="Sistema Defesa Civil", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# 2. SESSÃO E ROTEAMENTO
# ==========================================
if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
if "rota" not in st.session_state: st.session_state["rota"] = "login"
if "endereco_capturado" not in st.session_state: st.session_state["endereco_capturado"] = ""
if "lat_capturada" not in st.session_state: st.session_state["lat_capturada"] = None
if "lon_capturada" not in st.session_state: st.session_state["lon_capturada"] = None

def navegar(nova_rota):
    st.session_state["rota"] = nova_rota
    st.rerun()

# ==========================================
# 3. DADOS E REGRAS DE NEGÓCIO
# ==========================================
def adicionar_emoji_natureza(tipo):
    t = str(tipo).upper()
    if 'INCÊNDIO' in t: return f"🔥 {tipo}"
    elif 'DESLIZAMENTO' in t: return f"⛰️ {tipo}"
    elif 'ALAGAMENTO' in t: return f"🌊 {tipo}"
    elif 'DESABAMENTO' in t: return f"🏚️ {tipo}"
    else: return f"📝 {tipo}"

CORES_RISCO_HEX = {'ALTO': '#F97316', 'MÉDIO': '#EAB308', 'MEDIO': '#EAB308', 'BAIXO': '#22C55E', 'CRÍTICO': '#EF4444', 'CRITICO': '#EF4444'}
CORES_RISCO_PINO = {'ALTO': 'orange', 'MÉDIO': 'beige', 'MEDIO': 'beige', 'BAIXO': 'green', 'CRÍTICO': 'red', 'CRITICO': 'red'}

def buscar_endereco_por_coordenada(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        headers = {'User-Agent': 'DefesaCivilAM/1.0'}
        response = requests.get(url, headers=headers).json()
        return response.get('display_name', 'Endereço não encontrado no satélite')
    except: return ""

@st.cache_data(ttl=15) # Atualiza mais rápido (15 segundos)
def carregar_dados():
    try:
        ref = obter_referencia("ocorrencias")
        dados = ref.get()
        if not dados: return pd.DataFrame()
        
        # TRADUTOR BLINDADO: Resolve o bug do Dashboard vazio
        if isinstance(dados, list):
            dados_dict = {str(i): v for i, v in enumerate(dados) if v is not None}
            df = pd.DataFrame.from_dict(dados_dict, orient='index')
        else:
            df = pd.DataFrame.from_dict(dados, orient='index')
            
        colunas_padrao = {'tipo': 'Não Informado', 'encaminhamento': 'Não Informado', 'risco': 'MÉDIO', 'data': '', 'bairro': 'Não Informado', 'municipio': 'Manaus', 'endereco': '', 'solicitante': 'Não Informado'}
        for col, padrao in colunas_padrao.items():
            if col not in df.columns: df[col] = padrao
            
        df['tipo_emoji'] = df['tipo'].apply(adicionar_emoji_natureza)
        df['risco_padrao'] = df['risco'].astype(str).str.strip().str.upper()
        df['data_dt'] = pd.to_datetime(df['data'], errors='coerce', dayfirst=True)
        df['Ano_Filtro'] = df['data_dt'].dt.year.fillna(0).astype(int).astype(str).replace('0', 'Desconhecido')
        df['Mes_Filtro'] = df['data_dt'].dt.strftime('%m').fillna('Desconhecido')
        return df
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame()

# ==========================================
# 4. CSS GLOBAL UNIFICADO (100% TEMA ESCURO)
# ==========================================
def aplicar_css_global():
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
        
        /* Fundo Oficial Azul Marinho */
        .stApp { background-color: #19194D !important; }
        .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; max-width: 98% !important; }
        
        /* Textos, Fontes Maiores e Brancas */
        h1, h2, h3, h4, p, label, .stMarkdown { color: #FFFFFF !important; font-family: 'Segoe UI', Arial, sans-serif !important; font-size: 16px !important; }
        .texto-laranja { color: #FF8C00 !important; font-weight: bold; font-size: 16px !important; letter-spacing: 1px;}
        
        /* Barra Superior (Top Bar) */
        .barra-superior {
            background-color: #0B0B2A; color: #FFFFFF; padding: 15px 20px; border-radius: 6px;
            font-weight: 800; font-size: 20px; text-transform: uppercase;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-bottom: 20px; border: 1px solid #4A4A8C;
        }

        /* Cartões Translucidos (Containers) */
        .card-escuro {
            background-color: rgba(255, 255, 255, 0.05) !important; border-radius: 8px; padding: 25px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1);
            height: 100%;
        }
        
        .titulo-cartao { 
            font-size: 15px; font-weight: 800; color: #FF8C00; 
            text-transform: uppercase; margin-bottom: 15px; 
            border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 8px; 
        }

        /* Inputs e Formulários Escuros */
        .stTextInput label p, .stSelectbox label p, .stDateInput label p, .stTimeInput label p { font-weight: 700 !important; color: #FFFFFF !important; }
        input, select, div[data-baseweb="select"] > div, .stDateInput > div > div > input, .stTimeInput > div > div > input {
            background-color: #23235B !important; color: #FFFFFF !important; 
            border: 1px solid #4A4A8C !important; border-radius: 6px !important; padding: 10px !important; font-size: 16px !important;
        }
        ul[data-baseweb="menu"] { background-color: #23235B !important; color: #FFFFFF !important; border: 1px solid #4A4A8C !important; }
        li[role="option"] { color: #FFFFFF !important; font-size: 15px !important; }

        /* Compressão de Espaços (Menos Gaps) */
        [data-testid="stVerticalBlock"] { gap: 0.6rem !important; }

        /* Botões */
        div.stButton > button[kind="secondary"] { 
            background-color: #23235B !important; color: #FFFFFF !important; 
            border: 1px solid #4A4A8C !important; font-weight: bold !important; height: 50px !important; font-size: 16px !important;
        }
        div.stButton > button[kind="secondary"]:hover { background-color: #2D2D70 !important; border-color: #FF8C00 !important; }
        
        div.stButton > button[kind="primary"] { 
            background-color: #FF8C00 !important; color: #FFFFFF !important; 
            border: none !important; font-weight: bold !important; height: 50px !important; margin-top: 15px !important; font-size: 18px !important;
        }
        div.stButton > button[kind="primary"]:hover { background-color: #E67E00 !important; }
        div.stButton > button[kind="primary"] p { color: #FFFFFF !important; font-size: 18px !important; font-weight: bold !important; }
        
        /* Métricas */
        div[data-testid="metric-container"] { background-color: rgba(255,255,255,0.05) !important; padding: 15px !important; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); text-align: center; }
        div[data-testid="stMetricValue"] > div { color: #FF8C00 !important; font-size: 45px !important; font-weight: 900 !important; }
        div[data-testid="stMetricLabel"] > div p { color: #FFFFFF !important; font-size: 14px !important; font-weight: 600 !important; text-transform: uppercase; }
        
        /* Tabelas (Dataframes) Escuras */
        [data-testid="stDataFrame"] { background-color: #23235B !important; border-radius: 6px; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 5. TELAS DO SISTEMA
# ==========================================

def tela_login():
    _, col_centro, _ = st.columns([1.5, 2, 1.5])
    with col_centro:
        st.markdown('<div class="card-escuro" style="margin-top: 10vh; text-align: center;">', unsafe_allow_html=True)
        st.image("https://raw.githubusercontent.com/EBRlock/dashboard-defesa-civil/main/assets/logo_defesa.png", width=140)
        st.markdown("<h2 style='margin-top: 15px;'>DEFESA CIVIL</h2>", unsafe_allow_html=True)
        st.markdown("<p class='texto-laranja'>SISTEMA INTEGRADO DE GESTÃO</p>", unsafe_allow_html=True)
        st.write("")
        
        usuario = st.text_input("Usuário", placeholder="Credencial", label_visibility="collapsed")
        senha = st.text_input("Senha", type="password", placeholder="Palavra-passe", label_visibility="collapsed")
        
        if st.button("AUTENTICAR", type="primary", use_container_width=True):
            if (usuario == "gestaodefesacivil" and senha == "defesacivilam26") or (usuario == "admin" and senha == "1234"):
                st.session_state["autenticado"] = True; navegar("hub")
            else: st.error("Acesso negado. Credenciais incorretas.")
        st.markdown('</div>', unsafe_allow_html=True)

def tela_hub():
    _, col_centro, _ = st.columns([1.5, 2, 1.5])
    with col_centro:
        st.markdown('<div class="card-escuro" style="margin-top: 10vh; text-align: center;">', unsafe_allow_html=True)
        st.image("https://raw.githubusercontent.com/EBRlock/dashboard-defesa-civil/main/assets/logo_defesa.png", width=140)
        st.markdown("<h2 style='margin-top: 15px;'>DEFESA CIVIL</h2>", unsafe_allow_html=True)
        st.markdown("<p class='texto-laranja'>BEM-VINDO AO PORTAL OPERACIONAL</p>", unsafe_allow_html=True)
        st.write("---")
        
        if st.button("📝 REGISTRAR OCORRÊNCIA", type="secondary", use_container_width=True): navegar("registro")
        if st.button("📊 PAINEL DE MONITORAMENTO", type="secondary", use_container_width=True): navegar("dashboard")
        if st.button("⚙️ ADMINISTRAÇÃO DO BANCO", type="secondary", use_container_width=True): navegar("admin")
        
        st.write("")
        if st.button("ENCERRAR SESSÃO", type="primary", use_container_width=True):
            st.session_state["autenticado"] = False; navegar("login")
        st.markdown('</div>', unsafe_allow_html=True)

def tela_registro():
    col_v, col_t = st.columns([1, 10])
    with col_v: 
        if st.button("⬅ VOLTAR", type="secondary", use_container_width=True): navegar("hub")
    with col_t: 
        st.markdown("<div class='barra-superior'>CENTRAL DE MONITORAMENTO - REGISTRO E DESPACHO</div>", unsafe_allow_html=True)

    col_form, col_meio, col_mapa = st.columns([1.3, 1, 2.5])
    
    # === ÁREA 1: O MAPA INTERATIVO (Processado primeiro para gerar o endereço) ===
    with col_mapa:
        st.markdown("<div class='card-escuro'>", unsafe_allow_html=True)
        st.markdown("<p class='texto-laranja'>📍 TOQUE NO MAPA PARA CAPTURAR A COORDENADA</p>", unsafe_allow_html=True)
        m_registro = folium.Map(location=[-3.119, -60.021], zoom_start=12, tiles="CartoDB dark_matter")
        mapa_clicado = st_folium(m_registro, height=500, use_container_width=True, key="mapa_novo")
        
        if mapa_clicado and mapa_clicado.get("last_clicked"):
            lat = mapa_clicado["last_clicked"]["lat"]
            lon = mapa_clicado["last_clicked"]["lng"]
            if lat != st.session_state["lat_capturada"]:
                st.session_state["lat_capturada"] = lat
                st.session_state["lon_capturada"] = lon
                st.session_state["endereco_capturado"] = buscar_endereco_por_coordenada(lat, lon)
                st.rerun() # Atualiza a tela preenchendo o formulário na hora!
                
        if st.session_state["lat_capturada"]:
            st.success("✅ GPS Capturado com sucesso!")
        st.markdown("</div>", unsafe_allow_html=True)

    # === ÁREA 2: FORMULÁRIO (Sem st.form, para ser atualizado ao vivo) ===
    with col_form:
        st.markdown("<div class='card-escuro'>", unsafe_allow_html=True)
        st.markdown("<div class='titulo-cartao'>Dados Cadastrais</div>", unsafe_allow_html=True)
        
        solicitante = st.text_input("SOLICITANTE", placeholder="Nome completo")
        municipio = st.text_input("MUNICÍPIO", value="Manaus")
        bairro = st.text_input("BAIRRO", placeholder="Bairro da ocorrência")
        
        # Recebe o endereço do clique no mapa automaticamente
        endereco = st.text_input("LOGRADOURO (RUA / AV)", value=st.session_state["endereco_capturado"])
        
        c_num, c_comp = st.columns([1, 2])
        numero = c_num.text_input("NÚMERO", placeholder="Nº")
        complemento = c_comp.text_input("COMPLEMENTO", placeholder="Ex: Apto 101")
        
        natureza = st.selectbox("NATUREZA DA OCORRÊNCIA", ["Alagamento", "Incêndio", "Deslizamento", "Desabamento", "Outros"])
        risco = st.selectbox("GRAU DE RISCO", ["BAIXO", "MÉDIO", "ALTO", "CRÍTICO"])
        
        encaminhamento = st.selectbox("ÓRGÃO DE ENCAMINHAMENTO", ["Aguardando Triagem", "Polícia Militar", "Corpo de Bombeiros", "Defesa Civil Municipal"])
        
        if st.button("SALVAR OCORRÊNCIA", type="primary", use_container_width=True):
            if not bairro or not endereco: st.warning("Preencha Bairro e Logradouro.")
            elif not st.session_state["lat_capturada"]: st.warning("Toque no mapa para capturar o GPS!")
            else:
                lat, lon = st.session_state["lat_capturada"], st.session_state["lon_capturada"]
                end_completo = f"{endereco}, {numero} - {complemento}"
                novo_registro = {"tipo": natureza, "municipio": municipio, "bairro": bairro, "endereco": end_completo, "risco": risco, "encaminhamento": encaminhamento, "data": datetime.now().strftime("%d/%m/%Y"), "solicitante": solicitante, "latitude": lat, "longitude": lon}
                try:
                    obter_referencia("ocorrencias").push(novo_registro)
                    st.success("Salvo com sucesso!"); st.balloons()
                    carregar_dados.clear()
                    st.session_state["endereco_capturado"] = ""
                    st.session_state["lat_capturada"] = None
                except Exception as e: st.error(f"Erro: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    # === ÁREA 3: CONTADORES DO TURNO ===
    with col_meio:
        st.markdown("<div class='card-escuro'>", unsafe_allow_html=True)
        st.markdown("<div class='titulo-cartao'>Monitoramento do Turno</div>", unsafe_allow_html=True)
        c_and, c_fin = st.columns(2)
        c_and.metric("EM ANDAMENTO", "0")
        c_fin.metric("FINALIZADOS", "0")
        st.write("---")
        st.markdown("<div style='font-size: 13px; font-weight: bold; color: #FFF; background: #0B0B2A; padding: 10px; border-radius: 4px; border: 1px solid #4A4A8C;'>TIPO &nbsp;&nbsp;&nbsp; RISCO &nbsp;&nbsp;&nbsp; STATUS &nbsp;&nbsp;&nbsp; AÇÃO</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

def tela_dashboard():
    df = carregar_dados()
    if df.empty: st.info("Sincronizando banco de dados..."); return

    col_v, col_t = st.columns([1, 10])
    with col_v: 
        if st.button("⬅ VOLTAR", type="secondary", use_container_width=True): navegar("hub")
    with col_t: 
        st.markdown("<div class='barra-superior'>PAINEL TÁTICO - MONITORAMENTO DE OCORRÊNCIAS</div>", unsafe_allow_html=True)

    st.markdown("<div class='card-escuro'>", unsafe_allow_html=True)
    c_f1, c_f2, c_f3, c_f4, c_f5 = st.columns(5)
    f_tipo = c_f1.selectbox("NATUREZA", ["Todas"] + sorted(df['tipo'].dropna().unique().tolist()))
    f_mun = c_f2.selectbox("MUNICÍPIO", ["Todas"] + sorted(df['municipio'].dropna().unique().tolist())) 
    f_bairro = c_f3.selectbox("BAIRRO", ["Todos"] + sorted(df['bairro'].dropna().unique().tolist())) 
    f_ano = c_f4.selectbox("ANO", ["Todos"] + sorted([a for a in df['Ano_Filtro'].unique() if a != 'Desconhecido'])) 
    f_mes = c_f5.selectbox("MÊS", ["Todos"] + sorted([m for m in df['Mes_Filtro'].unique() if m != 'Desconhecido'])) 
    st.markdown("</div><br>", unsafe_allow_html=True)
    
    df_f = df.copy()
    if f_tipo != "Todas": df_f = df_f[df_f['tipo'] == f_tipo]
    if f_mun != "Todas": df_f = df_f[df_f['municipio'] == f_mun]
    if f_bairro != "Todos": df_f = df_f[df_f['bairro'] == f_bairro]
    if f_ano != "Todas": df_f = df_f[df_f['Ano_Filtro'] == f_ano]
    if f_mes != "Todas": df_f = df_f[df_f['Mes_Filtro'] == f_mes]

    col_esq, col_dir = st.columns([1, 1.8])
    with col_esq:
        c_nat, c_enc = st.columns(2)
        with c_nat:
            st.markdown("<div class='card-escuro'><div class='titulo-cartao'>NATUREZA</div>", unsafe_allow_html=True)
            st.dataframe(df_f['tipo_emoji'].value_counts().reset_index(), hide_index=True, use_container_width=True, height=220)
            st.markdown("</div>", unsafe_allow_html=True)
        with c_enc:
            st.markdown("<div class='card-escuro'><div class='titulo-cartao'>ENCAMINHAMENTO</div>", unsafe_allow_html=True)
            st.dataframe(df_f['encaminhamento'].value_counts().reset_index(), hide_index=True, use_container_width=True, height=220)
            st.markdown("</div>", unsafe_allow_html=True)
            
        c_tot, c_piz = st.columns([1, 1.5])
        with c_tot:
            st.markdown("<div class='card-escuro'><div class='titulo-cartao'>TOTAL</div>", unsafe_allow_html=True)
            st.metric("", len(df_f))
            st.markdown("</div>", unsafe_allow_html=True)
        with c_piz:
            st.markdown("<div class='card-escuro'><div class='titulo-cartao'>Risco</div>", unsafe_allow_html=True)
            fig_pie = px.pie(df_f['risco_padrao'].value_counts().reset_index(), values='count', names='risco_padrao', hole=0.4, color='risco_padrao', color_discrete_map=CORES_RISCO_HEX)
            fig_pie.update_layout(height=160, margin=dict(t=0, b=0, l=0, r=0), showlegend=True, paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
            st.plotly_chart(fig_pie, use_container_width=True, theme=None)
            st.markdown("</div>", unsafe_allow_html=True)

    with col_dir:
        st.markdown("<div class='card-escuro'>", unsafe_allow_html=True)
        st.markdown("<div class='titulo-cartao'>Mapa Operacional</div>", unsafe_allow_html=True)
        m = folium.Map(location=[-3.119, -60.021], zoom_start=11.5, tiles="CartoDB dark_matter") 
        for _, row in df_f.iterrows():
            try:
                lat, lon = float(row['latitude']), float(row['longitude'])
                folium.Marker([lat, lon], tooltip=row.get('tipo', 'Ocorrência'), icon=folium.Icon(color=CORES_RISCO_PINO.get(row.get('risco_padrao', 'MÉDIO'), 'gray'))).add_to(m)
            except: continue
        st_folium(m, use_container_width=True, height=350)
        st.markdown("</div><br>", unsafe_allow_html=True)
        
        st.markdown("<div class='card-escuro'><div class='titulo-cartao'>Registros por Mês</div>", unsafe_allow_html=True)
        df_g = df_f[df_f['Mes_Filtro'] != 'Desconhecido']
        if not df_g.empty:
            fig_bar = px.bar(df_g['Mes_Filtro'].value_counts().reset_index().sort_values(by='Mes_Filtro'), x='Mes_Filtro', y='count')
            fig_bar.update_traces(marker_color='#FF8C00') 
            fig_bar.update_layout(height=140, margin=dict(t=0, b=0, l=0, r=0), xaxis_title=None, yaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
            st.plotly_chart(fig_bar, use_container_width=True, theme=None)
        st.markdown("</div>", unsafe_allow_html=True)

def tela_admin():
    col_v, col_t = st.columns([1, 10])
    with col_v: 
        if st.button("⬅ VOLTAR", type="secondary", use_container_width=True): navegar("hub")
    with col_t: 
        st.markdown("<div class='barra-superior' style='background-color: #8B0000; border-color: #FF0000;'>PAINEL DO ADMINISTRADOR DE SISTEMAS</div>", unsafe_allow_html=True)
    
    df = carregar_dados()
    if df.empty: st.info("Banco vazio."); return
    
    st.markdown("<div class='card-escuro'><div class='titulo-cartao'>Auditoria e Exclusão</div>", unsafe_allow_html=True)
    opcoes = {f"{row.get('data', '')} | {row.get('tipo', '')} | {row.get('bairro', '')} [ID: {idx}]": idx for idx, row in df.iterrows()}
    selecao = st.selectbox("Selecione o registro alvo para exclusão:", list(opcoes.keys()))
    
    st.write("")
    if st.button("EXCLUIR REGISTRO PERMANENTEMENTE", type="primary"):
        try:
            obter_referencia(f"ocorrencias/{opcoes[selecao]}").delete()
            st.success("Exclusão realizada com sucesso."); carregar_dados.clear(); st.rerun()
        except Exception as e: st.error(f"Erro: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 6. ROTEADOR
# ==========================================
aplicar_css_global() # Aplica o CSS Escuro em TODAS as páginas

if not st.session_state["autenticado"]: tela_login()
else:
    if st.session_state["rota"] == "hub": tela_hub()
    elif st.session_state["rota"] == "dashboard": tela_dashboard()
    elif st.session_state["rota"] == "registro": tela_registro()
    elif st.session_state["rota"] == "admin": tela_admin()
