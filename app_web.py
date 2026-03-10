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

@st.cache_data(ttl=60)
def carregar_dados():
    try:
        ref = obter_referencia("ocorrencias")
        dados = ref.get()
        if not dados: return pd.DataFrame()
        
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

def buscar_endereco_por_coordenada(lat, lon):
    """Faz a engenharia reversa para achar o nome da rua baseado no clique do mapa"""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        headers = {'User-Agent': 'DefesaCivilApp/1.0'}
        response = requests.get(url, headers=headers).json()
        return response.get('display_name', 'Endereço não encontrado no satélite')
    except:
        return ""

# ==========================================
# 4. CSS DINÂMICO (Tema Escuro vs Tema Claro)
# ==========================================
def aplicar_css_escuro():
    """CSS para Login, Hub e Registro (Fundo Azul Escuro, Textos Maiores, Sem Espaços)"""
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
        .stApp { background-color: #19194D !important; }
        .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; max-width: 98% !important; }
        
        /* Ajuste do Cartão Central do Login */
        .cartao-login {
            background-color: rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important; padding: 40px !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
            margin-top: 8vh !important; text-align: center;
        }

        /* Textos, Labels e Fontes Maiores */
        h1, h2, h3, h4, h5, h6, p, label { color: #FFFFFF !important; font-family: 'Segoe UI', Arial, sans-serif !important; }
        .texto-laranja { color: #FF8C00 !important; font-weight: bold; font-size: 15px; letter-spacing: 1px;}
        
        /* Esmagando os espaços e aumentando a fonte no Registro */
        .stTextInput label p, .stSelectbox label p, .stDateInput label p, .stTimeInput label p {
            font-size: 15px !important; font-weight: bold !important; margin-bottom: 2px !important;
        }
        
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stDateInput input, .stTimeInput input {
            background-color: #23235B !important; color: white !important;
            border: 1px solid #4A4A8C !important; border-radius: 4px !important;
            font-size: 15px !important; padding: 6px 10px !important;
        }
        
        /* Reduzindo o GAP (espaçamento) geral */
        [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
        
        /* Botões */
        div.stButton > button[kind="primary"] {
            background-color: #FF8C00 !important; color: white !important;
            border: none !important; border-radius: 6px !important; font-weight: bold !important; font-size: 16px !important;
            height: 45px !important; margin-top: 10px !important;
        }
        div.stButton > button[kind="primary"]:hover { background-color: #E67E00 !important; }

        div.stButton > button[kind="secondary"] {
            background-color: #23235B !important; color: white !important;
            border: 1px solid #4A4A8C !important; border-radius: 6px !important; font-weight: bold !important;
            height: 45px !important; margin-bottom: 5px !important;
        }
        div.stButton > button[kind="secondary"]:hover { background-color: #2D2D70 !important; border-color: #FF8C00 !important; }
        
        /* Barra Superior Simulada no Registro */
        .barra-superior-dark {
            background-color: #0B0B2A; color: white; padding: 12px 15px; border-radius: 4px;
            display: flex; align-items: center; margin-bottom: 10px; font-weight: bold; font-size: 18px;
            border: 1px solid #4A4A8C;
        }
        </style>
    """, unsafe_allow_html=True)

def aplicar_css_dashboard():
    """CSS Claro apenas para o Painel de Monitoramento"""
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
        .stApp { background-color: #F0F2F6 !important; }
        .block-container { padding-top: 1rem !important; max-width: 98% !important; }
        .barra-superior { background-color: #19194D; color: white; padding: 10px 15px; border-radius: 4px; margin-bottom: 15px; font-weight: bold; }
        .card-branco { background-color: white; border-radius: 4px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 15px; border: 1px solid #E0E0E0; }
        .titulo-cartao { font-size: 13px; font-weight: bold; color: #555555; text-transform: uppercase; margin-bottom: 10px; border-bottom: 1px solid #EEEEEE; padding-bottom: 5px; }
        .stTextInput input, .stSelectbox div[data-baseweb="select"] { background-color: white !important; color: black !important; border-radius: 4px !important; border: 1px solid #CCC !important; }
        .stTextInput label p, .stSelectbox label p { color: #19194D !important; font-weight: bold !important; }
        div.stButton > button[kind="secondary"] { background-color: white !important; color: #19194D !important; border: 1px solid #19194D !important; font-weight: bold !important; }
        div[data-testid="stMetricValue"] > div { color: #19194D !important; font-size: 48px !important; font-weight: bold !important; }
        </style>
    """, unsafe_allow_html=True)

# ==========================================
# 5. TELAS DO SISTEMA
# ==========================================

def tela_login():
    aplicar_css_escuro()
    _, col_centro, _ = st.columns([1.5, 2, 1.5])
    
    with col_centro:
        st.markdown('<div class="cartao-login">', unsafe_allow_html=True)
        st.image("https://raw.githubusercontent.com/EBRlock/dashboard-defesa-civil/main/assets/logo_defesa.png", width=120)
        st.markdown("<h2 style='margin-top: 10px;'>DEFESA CIVIL</h2>", unsafe_allow_html=True)
        st.markdown("<p class='texto-laranja'>ACESSO RESTRITO</p>", unsafe_allow_html=True)
        st.write("")
        
        usuario = st.text_input("Usuário", placeholder="admin", label_visibility="collapsed")
        senha = st.text_input("Senha", type="password", placeholder="Senha", label_visibility="collapsed")
        
        if st.button("ENTRAR NO SISTEMA", type="primary", use_container_width=True):
            if (usuario == "gestaodefesacivil" and senha == "defesacivilam26") or (usuario == "admin" and senha == "1234"):
                st.session_state["autenticado"] = True; navegar("hub")
            else: st.error("Credenciais inválidas.")
        st.markdown('</div>', unsafe_allow_html=True)

def tela_hub():
    aplicar_css_escuro()
    _, col_centro, _ = st.columns([1.5, 2, 1.5])
    
    with col_centro:
        st.markdown('<div class="cartao-login">', unsafe_allow_html=True)
        st.image("https://raw.githubusercontent.com/EBRlock/dashboard-defesa-civil/main/assets/logo_defesa.png", width=120)
        st.markdown("<h2 style='margin-top: 10px;'>DEFESA CIVIL</h2>", unsafe_allow_html=True)
        st.markdown("<p class='texto-laranja'>BEM-VINDO, ADMINISTRADOR GERAL<br>[ADMINISTRADOR]</p>", unsafe_allow_html=True)
        st.write("")
        
        if st.button("📝 REGISTRAR OCORRÊNCIA", type="secondary", use_container_width=True): navegar("registro")
        if st.button("📊 PAINEL DE DADOS", type="secondary", use_container_width=True): navegar("dashboard")
        if st.button("⚙️ PAINEL ADMINISTRADOR", type="secondary", use_container_width=True): navegar("admin")
        
        st.write("")
        if st.button("SAIR DO SISTEMA", type="primary", use_container_width=True):
            st.session_state["autenticado"] = False; navegar("login")
        st.markdown('</div>', unsafe_allow_html=True)

def tela_registro():
    aplicar_css_escuro()
    
    col_v, col_t = st.columns([1, 10])
    with col_v: 
        if st.button("⬅ VOLTAR", type="secondary", use_container_width=True): navegar("hub")
    with col_t: 
        st.markdown("<div class='barra-superior-dark'>CENTRAL DE MONITORAMENTO - REGISTRO E DESPACHO</div>", unsafe_allow_html=True)

    col_form, col_mapa = st.columns([1.5, 2])
    
    # 1. ÁREA DO MAPA (Processado antes para atualizar os inputs)
    with col_mapa:
        st.markdown("<p class='texto-laranja'>📍 Toque no mapa abaixo para capturar o endereço exato</p>", unsafe_allow_html=True)
        m_registro = folium.Map(location=[-3.119, -60.021], zoom_start=12, tiles="CartoDB dark_matter")
        mapa_clicado = st_folium(m_registro, height=450, use_container_width=True, key="mapa_novo")
        
        # Lógica de Captura do Mapa
        if mapa_clicado.get("last_clicked"):
            lat = mapa_clicado["last_clicked"]["lat"]
            lon = mapa_clicado["last_clicked"]["lng"]
            
            # Só busca na internet se for um clique novo (evita lentidão)
            if lat != st.session_state["lat_capturada"]:
                st.session_state["lat_capturada"] = lat
                st.session_state["lon_capturada"] = lon
                endereco_satelite = buscar_endereco_por_coordenada(lat, lon)
                st.session_state["endereco_capturado"] = endereco_satelite
                st.rerun() # Força a tela a atualizar com o novo endereço preenchido

        # Exibe Feedback Visual
        if st.session_state["lat_capturada"]:
            st.success("✅ Coordenada e Endereço capturados com sucesso pelo Satélite!")

    # 2. ÁREA DO FORMULÁRIO (Agora sem st.form para não apagar ao clicar no mapa)
    with col_form:
        solicitante = st.text_input("SOLICITANTE", placeholder="Nome completo", key="f_sol")
        municipio = st.text_input("MUNICÍPIO", value="Manaus", key="f_mun")
        bairro = st.text_input("BAIRRO", placeholder="Bairro da ocorrência", key="f_bai")
        
        # Aqui a mágica acontece: O campo de endereço é preenchido automaticamente pela sessão do mapa
        endereco = st.text_input("LOGRADOURO (ENDEREÇO CAPTURADO)", value=st.session_state["endereco_capturado"], key="f_end")
        
        c_num, c_comp = st.columns([1, 2])
        numero = c_num.text_input("NÚMERO", placeholder="Nº", key="f_num")
        complemento = c_comp.text_input("COMPLEMENTO", placeholder="Ex: Apto 101", key="f_comp")
        
        natureza = st.selectbox("NATUREZA DA OCORRÊNCIA", ["Alagamento", "Incêndio", "Deslizamento", "Desabamento", "Outros"], key="f_nat")
        risco = st.selectbox("GRAU DE RISCO", ["BAIXO", "MÉDIO", "ALTO", "CRÍTICO"], key="f_risc")
        
        c_data, c_hora = st.columns(2)
        data_ocorrencia = c_data.date_input("DATA DO REGISTRO", key="f_dat")
        hora_ocorrencia = c_hora.time_input("HORA", key="f_hor")
        
        encaminhamento = st.selectbox("ÓRGÃO DE ENCAMINHAMENTO", ["Aguardando Triagem", "Polícia Militar", "Corpo de Bombeiros", "Defesa Civil Municipal"], key="f_enc")
        
        if st.button("SALVAR OCORRÊNCIA", type="primary", use_container_width=True):
            if not bairro or not endereco: st.warning("Preencha Bairro e Logradouro.")
            elif not st.session_state["lat_capturada"]: st.warning("Toque no mapa para capturar a coordenada!")
            else:
                lat, lon = st.session_state["lat_capturada"], st.session_state["lon_capturada"]
                end_completo = f"{endereco}, {numero} - {complemento}"
                novo_registro = {"tipo": natureza, "municipio": municipio, "bairro": bairro, "endereco": end_completo, "risco": risco, "encaminhamento": encaminhamento, "data": data_ocorrencia.strftime("%d/%m/%Y"), "solicitante": solicitante, "latitude": lat, "longitude": lon}
                try:
                    obter_referencia("ocorrencias").push(novo_registro)
                    st.success("Ocorrência Salva!"); st.balloons()
                    carregar_dados.clear()
                    # Reseta a sessão após salvar
                    st.session_state["endereco_capturado"] = ""
                    st.session_state["lat_capturada"] = None
                except Exception as e: st.error(f"Erro: {e}")

def tela_dashboard():
    aplicar_css_dashboard()
    df = carregar_dados()
    if df.empty: st.info("Sem dados."); return

    col_v, col_t = st.columns([1, 10])
    with col_v: 
        if st.button("⬅ VOLTAR", type="secondary", use_container_width=True): navegar("hub")
    with col_t: 
        st.markdown("<div class='barra-superior'>PAINEL DE ATENDIMENTO DO CALL CENTER - DEFESA CIVIL DO ESTADO DO AMAZONAS</div>", unsafe_allow_html=True)

    c_f1, c_f2, c_f3, c_f4, c_f5 = st.columns(5)
    f_tipo = c_f1.selectbox("NATUREZA", ["Todas"] + sorted(df['tipo'].dropna().unique().tolist()))
    f_mun = c_f2.selectbox("MUNICÍPIO", ["Todas"] + sorted(df['municipio'].dropna().unique().tolist())) 
    f_bairro = c_f3.selectbox("BAIRRO", ["Todos"] + sorted(df['bairro'].dropna().unique().tolist())) 
    f_ano = c_f4.selectbox("ANO", ["Todos"] + sorted([a for a in df['Ano_Filtro'].unique() if a != 'Desconhecido'])) 
    f_mes = c_f5.selectbox("MÊS", ["Todos"] + sorted([m for m in df['Mes_Filtro'].unique() if m != 'Desconhecido'])) 
    
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
            st.markdown("<div class='card-branco'><div class='titulo-cartao'>NATUREZA</div>", unsafe_allow_html=True)
            st.dataframe(df_f['tipo_emoji'].value_counts().reset_index(), hide_index=True, use_container_width=True, height=200)
            st.markdown("</div>", unsafe_allow_html=True)
        with c_enc:
            st.markdown("<div class='card-branco'><div class='titulo-cartao'>ENCAMINHAMENTO</div>", unsafe_allow_html=True)
            st.dataframe(df_f['encaminhamento'].value_counts().reset_index(), hide_index=True, use_container_width=True, height=200)
            st.markdown("</div>", unsafe_allow_html=True)
            
        c_tot, c_piz = st.columns([1, 1.5])
        with c_tot:
            st.markdown("<div class='card-branco'><div class='titulo-cartao'>Total de Registros</div>", unsafe_allow_html=True)
            st.metric("", len(df_f))
            st.markdown("</div>", unsafe_allow_html=True)
        with c_piz:
            st.markdown("<div class='card-branco'><div class='titulo-cartao'>Nível de Risco</div>", unsafe_allow_html=True)
            fig_pie = px.pie(df_f['risco_padrao'].value_counts().reset_index(), values='count', names='risco_padrao', hole=0.4, color='risco_padrao', color_discrete_map=CORES_RISCO_HEX)
            fig_pie.update_layout(height=150, margin=dict(t=0, b=0, l=0, r=0), showlegend=True)
            st.plotly_chart(fig_pie, use_container_width=True, theme=None)
            st.markdown("</div>", unsafe_allow_html=True)

    with col_dir:
        m = folium.Map(location=[-3.119, -60.021], zoom_start=11.5, tiles="OpenStreetMap") 
        for _, row in df_f.iterrows():
            try:
                lat, lon = float(row['latitude']), float(row['longitude'])
                folium.Marker([lat, lon], tooltip=row.get('tipo', 'Ocorrência'), icon=folium.Icon(color=CORES_RISCO_PINO.get(row.get('risco_padrao', 'MÉDIO'), 'gray'))).add_to(m)
            except: continue
        st_folium(m, use_container_width=True, height=300)
        
        st.markdown("<div class='card-branco'><div class='titulo-cartao'>Registros por Mês</div>", unsafe_allow_html=True)
        df_g = df_f[df_f['Mes_Filtro'] != 'Desconhecido']
        if not df_g.empty:
            fig_bar = px.bar(df_g['Mes_Filtro'].value_counts().reset_index().sort_values(by='Mes_Filtro'), x='Mes_Filtro', y='count')
            fig_bar.update_traces(marker_color='#19194D') 
            fig_bar.update_layout(height=120, margin=dict(t=0, b=0, l=0, r=0), xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig_bar, use_container_width=True, theme=None)
        st.markdown("</div>", unsafe_allow_html=True)

def tela_admin():
    aplicar_css_dashboard()
    col_v, col_t = st.columns([1, 10])
    with col_v: 
        if st.button("⬅ VOLTAR", type="secondary", use_container_width=True): navegar("hub")
    with col_t: 
        st.markdown("<div class='barra-superior' style='background-color: #8B0000;'>PAINEL DO ADMINISTRADOR DE SISTEMAS</div>", unsafe_allow_html=True)
    
    df = carregar_dados()
    if df.empty: st.info("Banco vazio."); return
    
    st.markdown("<div class='card-branco'><div class='titulo-cartao'>Banco de Dados (Exclusão)</div>", unsafe_allow_html=True)
    opcoes = {f"{row.get('data', '')} | {row.get('tipo', '')} | {row.get('bairro', '')} [ID: {idx}]": idx for idx, row in df.iterrows()}
    selecao = st.selectbox("Selecione para excluir:", list(opcoes.keys()))
    if st.button("EXCLUIR REGISTRO", type="primary"):
        try:
            obter_referencia(f"ocorrencias/{opcoes[selecao]}").delete()
            st.success("Excluído!"); carregar_dados.clear(); st.rerun()
        except Exception as e: st.error(e)
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 6. ROTEADOR
# ==========================================
if not st.session_state["autenticado"]: tela_login()
else:
    if st.session_state["rota"] == "hub": tela_hub()
    elif st.session_state["rota"] == "dashboard": tela_dashboard()
    elif st.session_state["rota"] == "registro": tela_registro()
    elif st.session_state["rota"] == "admin": tela_admin()
