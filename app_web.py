import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime
from core.database import obter_referencia

# ==========================================
# CONFIGURAÇÃO GERAL E CSS
# ==========================================
st.set_page_config(page_title="Gestão Defesa Civil", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #F4F6F9; }
    
    /* Login Limpo e Centralizado */
    .login-container {
        max-width: 400px;
        margin: 10vh auto;
        padding: 40px;
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .cabecalho {
        background-color: #191970; color: white; padding: 12px 20px; 
        border-radius: 4px; margin-bottom: 15px; font-weight: bold;
        font-family: 'Segoe UI', Arial, sans-serif; font-size: 18px;
        text-transform: uppercase;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# VARIÁVEIS DE SESSÃO (ROTEAMENTO)
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
if "rota" not in st.session_state:
    st.session_state["rota"] = "login"

def navegar(nova_rota):
    st.session_state["rota"] = nova_rota
    st.rerun()

# ==========================================
# FUNÇÕES DE APOIO
# ==========================================
def adicionar_emoji_natureza(tipo):
    t = str(tipo).upper()
    if 'INCÊNDIO' in t: return f"🔥 {tipo}"
    elif 'DESLIZAMENTO' in t: return f"⛰️ {tipo}"
    elif 'ALAGAMENTO' in t: return f"🌊 {tipo}"
    elif 'DESABAMENTO' in t: return f"🏚️ {tipo}"
    else: return f"📝 {tipo}"

CORES_RISCO_HEX = {'ALTO': '#FF9800', 'MÉDIO': '#FFEB3B', 'MEDIO': '#FFEB3B', 'BAIXO': '#4CAF50', 'CRÍTICO': '#F44336', 'CRITICO': '#F44336'}
CORES_RISCO_PINO = {'ALTO': 'orange', 'MÉDIO': 'beige', 'MEDIO': 'beige', 'BAIXO': 'green', 'CRÍTICO': 'red', 'CRITICO': 'red'}

@st.cache_data(ttl=60)
def carregar_dados():
    try:
        ref = obter_referencia("ocorrencias")
        dados = ref.get()
        if not dados: return pd.DataFrame()
        df = pd.DataFrame.from_dict(dados, orient='index')
        df['tipo_emoji'] = df['tipo'].apply(adicionar_emoji_natureza)
        df['risco_padrao'] = df['risco'].astype(str).str.strip().str.upper()
        df['data_dt'] = pd.to_datetime(df['data'], errors='coerce', dayfirst=True)
        df['Ano_Filtro'] = df['data_dt'].dt.year.fillna(0).astype(int).astype(str).replace('0', 'Desconhecido')
        df['Mes_Filtro'] = df['data_dt'].dt.strftime('%m').fillna('Desconhecido')
        return df
    except: return pd.DataFrame()

# ==========================================
# TELA 1: LOGIN
# ==========================================
def tela_login():
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.image("https://raw.githubusercontent.com/EBRlock/dashboard-defesa-civil/main/assets/logo_defesa.png", use_container_width=True)
    st.markdown("<h3 style='color: #191970; margin-top: 15px;'>🔐 Acesso Restrito</h3>", unsafe_allow_html=True)
    
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar", use_container_width=True, type="primary"):
        if usuario == "gestaodefesacivil" and senha == "defesacivilam26":
            st.session_state["autenticado"] = True
            navegar("dashboard")
        else:
            st.error("Credenciais inválidas.")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# MENU LATERAL (HUB)
# ==========================================
def renderizar_sidebar():
    with st.sidebar:
        st.image("https://raw.githubusercontent.com/EBRlock/dashboard-defesa-civil/main/assets/logo_defesa.png", width=150)
        st.markdown("### 🎛️ HUB DEFESA CIVIL")
        st.divider()
        
        if st.button("📊 Dashboard de Monitoramento", use_container_width=True):
            navegar("dashboard")
        if st.button("📝 Registrar Ocorrência", use_container_width=True):
            navegar("registro")
            
        st.divider()
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state["autenticado"] = False
            navegar("login")

# ==========================================
# TELA 2: REGISTRAR OCORRÊNCIA
# ==========================================
def tela_registro():
    st.markdown("<div class='cabecalho'>📝 REGISTRO DE NOVA OCORRÊNCIA</div>", unsafe_allow_html=True)
    
    with st.form("form_registro", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            natureza = st.selectbox("Natureza", ["Incêndio", "Alagamento", "Deslizamento", "Desabamento", "Outros"])
            municipio = st.text_input("Município", value="Manaus")
            bairro = st.text_input("Bairro")
        with col2:
            risco = st.selectbox("Nível de Risco", ["Baixo", "Médio", "Alto", "Crítico"])
            encaminhamento = st.selectbox("Encaminhamento", ["Aguardando Vistoria", "Atendido", "Em Andamento"])
            data_ocorrencia = st.date_input("Data da Ocorrência")
            
        endereco = st.text_input("Endereço Completo (Rua, Número, Referência)")
        
        st.markdown("### 📍 Localização Exata (Toque no mapa para marcar a rua)")
        st.info("A coordenada será salva automaticamente ao tocar no mapa.")
        
        # Mapa para captura de clique
        m_registro = folium.Map(location=[-3.119, -60.021], zoom_start=12, tiles="CartoDB positron")
        mapa_clicado = st_folium(m_registro, height=350, use_container_width=True, key="mapa_novo")
        
        submit = st.form_submit_button("💾 Salvar Registro no Banco", type="primary")
        
        if submit:
            if not bairro or not endereco:
                st.warning("Por favor, preencha o Bairro e o Endereço.")
            elif not mapa_clicado.get("last_clicked"):
                st.warning("⚠️ Você precisa tocar no mapa para marcar o local exato da ocorrência!")
            else:
                lat = mapa_clicado["last_clicked"]["lat"]
                lon = mapa_clicado["last_clicked"]["lng"]
                
                # Monta os dados para o Firebase
                novo_registro = {
                    "tipo": natureza,
                    "municipio": municipio,
                    "bairro": bairro,
                    "endereco": endereco,
                    "risco": risco,
                    "encaminhamento": encaminhamento,
                    "data": data_ocorrencia.strftime("%d/%m/%Y"),
                    "latitude": lat,
                    "longitude": lon
                }
                
                try:
                    ref = obter_referencia("ocorrencias")
                    ref.push(novo_registro)
                    st.success("✅ Ocorrência registrada com sucesso na nuvem!")
                    st.balloons()
                    # Limpa os dados de cache para o Dashboard atualizar imediatamente
                    carregar_dados.clear()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# ==========================================
# TELA 3: DASHBOARD (SEU CÓDIGO ANTIGO COMPACTADO)
# ==========================================
def tela_dashboard():
    df = carregar_dados()
    if df.empty:
        st.info("Nenhum dado encontrado no banco de dados.")
        return

    st.markdown("<div class='cabecalho'>📋 PAINEL DE ATENDIMENTO DO CALL CENTER</div>", unsafe_allow_html=True)
    
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    filtro_tipo = col_f1.selectbox("NATUREZA", ["Todas"] + df['tipo_emoji'].dropna().unique().tolist())
    filtro_mun = col_f2.selectbox("MUNICÍPIO", ["Todas"] + df['municipio'].dropna().unique().tolist()) 
    filtro_bairro = col_f3.selectbox("BAIRRO", ["Todos"] + df['bairro'].dropna().unique().tolist()) 
    filtro_ano = col_f4.selectbox("ANO", ["Todos"] + sorted([a for a in df['Ano_Filtro'].unique() if a != 'Desconhecido'])) 
    filtro_mes = col_f5.selectbox("MÊS", ["Todos"] + sorted([m for m in df['Mes_Filtro'].unique() if m != 'Desconhecido'])) 
    
    df_f = df.copy()
    if filtro_tipo != "Todas": df_f = df_f[df_f['tipo_emoji'] == filtro_tipo]
    if filtro_mun != "Todas": df_f = df_f[df_f['municipio'] == filtro_mun]
    if filtro_bairro != "Todos": df_f = df_f[df_f['bairro'] == filtro_bairro]
    if filtro_ano != "Todos": df_f = df_f[df_f['Ano_Filtro'] == filtro_ano]
    if filtro_mes != "Todos": df_f = df_f[df_f['Mes_Filtro'] == filtro_mes]

    st.markdown("<hr style='margin: 10px 0; border-color: #D0D0D0;'>", unsafe_allow_html=True)

    col_sup_esq, col_sup_dir = st.columns([1, 1.3])
    with col_sup_esq:
        c1, c2 = st.columns(2)
        c1.dataframe(df_f['tipo_emoji'].value_counts().reset_index(), hide_index=True, use_container_width=True)
        c2.dataframe(df_f['encaminhamento'].value_counts().reset_index(), hide_index=True, use_container_width=True)

    with col_sup_dir:
        m = folium.Map(location=[-3.119, -60.021], zoom_start=11.5, tiles="CartoDB positron") 
        for idx, row in df_f.iterrows():
            try:
                lat, lon = float(row['latitude']), float(row['longitude'])
                risco = row.get('risco_padrao', 'MÉDIO')
                cor_hex = CORES_RISCO_HEX.get(risco, '#9E9E9E') 
                cor_icone = CORES_RISCO_PINO.get(risco, 'gray')
                
                folium.Marker([lat, lon], tooltip=row.get('tipo_emoji'), icon=folium.Icon(color=cor_icone, icon="info-sign")).add_to(m)
                folium.Circle([lat, lon], radius=260, color=cor_hex, fill=True, fill_opacity=0.35).add_to(m)
            except: continue
        st_folium(m, use_container_width=True, height=350)

    st.markdown("<hr style='margin: 10px 0; border-color: #D0D0D0;'>", unsafe_allow_html=True)
    col_inf_esq, col_inf_dir = st.columns([1, 1.3])

    with col_inf_esq:
        c_met, c_pie = st.columns([1, 2])
        c_met.metric("Total", len(df_f))
        fig_pie = px.pie(df_f['risco_padrao'].value_counts().reset_index(), values='count', names='risco_padrao', color='risco_padrao', color_discrete_map=CORES_RISCO_HEX, hole=0.4)
        fig_pie.update_layout(height=180, margin=dict(t=0, b=0, l=0, r=0))
        c_pie.plotly_chart(fig_pie, use_container_width=True, theme=None)

    with col_inf_dir:
        df_g = df_f[df_f['Mes_Filtro'] != 'Desconhecido']
        if not df_g.empty:
            fig_bar = px.bar(df_g['Mes_Filtro'].value_counts().reset_index(), x='Mes_Filtro', y='count')
            fig_bar.update_traces(marker_color='#191970') 
            fig_bar.update_layout(height=180, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_bar, use_container_width=True, theme=None)

# ==========================================
# ROTEADOR PRINCIPAL (EXECUÇÃO)
# ==========================================
if not st.session_state["autenticado"]:
    tela_login()
else:
    # Mostra a barra lateral se estiver logado
    renderizar_sidebar()
    
    # Chama a tela correta baseada no menu clicado
    if st.session_state["rota"] == "dashboard":
        tela_dashboard()
    elif st.session_state["rota"] == "registro":
        tela_registro()
