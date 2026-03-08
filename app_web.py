import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from core.database import obter_referencia

# ==========================================
# CONFIGURAÇÃO DA PÁGINA (Inicia no modo claro)
# ==========================================
st.set_page_config(page_title="Gestão Defesa Civil - Login", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# SISTEMA DE LOGIN COM CSS CORRIGIDO (BLINDADO)
# ==========================================
def tela_login():
    # CSS agressivo para forçar fundo branco na área de login, independente do tema do navegador
    st.markdown("""
        <style>
        /* Esconde menus padrões */
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Fundo geral da tela (cinza claro) */
        .stApp { background-color: #F4F6F9 !important; }
        
        /* Centraliza o conteúdo */
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 80vh;
        }
        
        /* Cria o 'cartão' branco centralizado para o login */
        .login-box {
            background-color: white !important;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            text-align: center;
            width: 400px;
        }
        
        /* Força títulos e labels em preto/azul escuro dentro do cartão */
        .login-box h2, .login-box h3, .login-box label {
            color: #191970 !important;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        
        /* Estiliza o botão Entrar */
        div.stButton > button:first-child {
            background-color: #191970;
            color: white;
            width: 100%;
            border: none;
            padding: 10px;
            border-radius: 4px;
        }
        div.stButton > button:first-child:hover {
            background-color: #2a2a9e;
        }
        </style>
    """, unsafe_allow_html=True)

    # Estrutura HTML/Streamlit para centralizar
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Usamos colunas para centralizar o bloco branco
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Iniciamos o 'cartão' branco
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        # Conteúdo do Login
        st.image("https://raw.githubusercontent.com/EBRlock/dashboard-defesa-civil/main/assets/logo_defesa.png", width=250)
        st.write("")
        st.markdown("<h3>🔐 Acesso Restrito</h3>", unsafe_allow_html=True)
        st.write("")

        usuario = st.text_input("Usuário", key="user_input")
        senha = st.text_input("Senha", type="password", key="pass_input")
        
        st.write("")
        if st.button("Entrar", key="login_btn"):
            if usuario == "gestaodefesacivil" and senha == "defesacivilam26":
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Usuário ou Senha incorretos.")
        
        # Fechamos as divs HTML
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Lógica de Sessão
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    tela_login()
    st.stop() 

# ==========================================
# CSS DO DASHBOARD (SÓ APARECE APÓS LOGIN)
# ==========================================
# Re-aplicamos o CSS do Dashboard para garantir que ele fique bonito
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #F4F6F9 !important; }
    .block-container { padding-top: 3rem; padding-bottom: 1rem; padding-left: 2rem; padding-right: 2rem; }
    
    .cabecalho {
        background-color: #191970; color: white; padding: 12px 20px; 
        border-radius: 4px; margin-bottom: 15px; font-weight: bold;
        font-family: 'Segoe UI', Arial, sans-serif; font-size: 18px;
        text-transform: uppercase; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    div[data-testid="metric-container"] {
        background-color: white; border: 1px solid #D0D0D0; border-radius: 4px; 
        padding: 15px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricValue"] > div { color: #191970 !important; font-size: 36px !important; font-weight: bold; }
    h3, p, strong { color: #333333 !important; font-family: 'Segoe UI', Arial, sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# FUNÇÕES DE APOIO E DADOS
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
CORES_TEXTO_RISCO = {'ALTO': 'white', 'MÉDIO': 'black', 'MEDIO': 'black', 'BAIXO': 'white', 'CRÍTICO': 'white', 'CRITICO': 'white'}

@st.cache_data(ttl=60)
def carregar_dados():
    try:
        ref = obter_referencia("ocorrencias")
        dados = ref.get()
        if dados:
            df = pd.DataFrame.from_dict(dados, orient='index')
            colunas_padrao = {'tipo': 'Não Informado', 'encaminhamento': 'Não Informado', 
                              'risco': 'MÉDIO', 'data': '', 'bairro': 'Não Informado', 'municipio': 'Manaus'}
            for col, padrao in colunas_padrao.items():
                if col not in df.columns: df[col] = padrao
            
            df['tipo_emoji'] = df['tipo'].apply(adicionar_emoji_natureza)
            df['risco_padrao'] = df['risco'].astype(str).str.strip().str.upper()
            df['data_dt'] = pd.to_datetime(df['data'], errors='coerce', dayfirst=True)
            df['Ano_Filtro'] = df['data_dt'].dt.year.fillna(0).astype(int).astype(str).replace('0', 'Desconhecido')
            df['Mes_Filtro'] = df['data_dt'].dt.strftime('%m').fillna('Desconhecido')
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"🛑 Erro: {e}")
        return pd.DataFrame()

# ==========================================
# CONTEÚDO DO DASHBOARD (APÓS LOGIN)
# ==========================================
# Atualiza o título da página para o nome do sistema
st.title("") # Gambiarra para resetar o título do st.set_page_config
st.markdown("<script>document.title = 'Painel Tático - Defesa Civil';</script>", unsafe_allow_html=True)

df = carregar_dados()

if not df.empty:
    st.markdown("<div class='cabecalho'>📋 PAINEL DE ATENDIMENTO DO CALL CENTER - DEFESA CIVIL AM</div>", unsafe_allow_html=True)
    
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    tipos = ["Todas"] + df['tipo_emoji'].dropna().unique().tolist()
    municipios = ["Todas"] + df['municipio'].dropna().unique().tolist()
    bairros = ["Todos"] + df['bairro'].dropna().unique().tolist()
    anos_reais = sorted([a for a in df['Ano_Filtro'].unique() if a != 'Desconhecido'])
    meses_reais = sorted([m for m in df['Mes_Filtro'].unique() if m != 'Desconhecido'])
    
    filtro_tipo = col_f1.selectbox("NATUREZA", tipos)
    filtro_mun = col_f2.selectbox("MUNICÍPIO", municipios) 
    filtro_bairro = col_f3.selectbox("BAIRRO", bairros) 
    filtro_ano = col_f4.selectbox("ANO", ["Todos"] + anos_reais) 
    filtro_mes = col_f5.selectbox("MÊS", ["Todos"] + meses_reais) 
    
    df_filtrado = df.copy()
    if filtro_tipo != "Todas": df_filtrado = df_filtrado[df_filtrado['tipo_emoji'] == filtro_tipo]
    if filtro_mun != "Todas": df_filtrado = df_filtrado[df_filtrado['municipio'] == filtro_mun]
    if filtro_bairro != "Todos": df_filtrado = df_filtrado[df_filtrado['bairro'] == filtro_bairro]
    if filtro_ano != "Todos": df_filtrado = df_filtrado[df_filtrado['Ano_Filtro'] == filtro_ano]
    if filtro_mes != "Todos": df_filtrado = df_filtrado[df_filtrado['Mes_Filtro'] == filtro_mes]

    st.write("---")

    col_sup_esq, col_sup_dir = st.columns([1, 1.3])

    with col_sup_esq:
        tab1, tab2 = st.columns(2)
        with tab1:
            st.markdown("**NATUREZA**")
            contagem_nat = df_filtrado['tipo_emoji'].value_counts().reset_index()
            contagem_nat.columns = ['NATUREZA', 'QUANTIDADE']
            st.dataframe(contagem_nat, hide_index=True, use_container_width=True, height=250)
        with tab2:
            st.markdown("**ENCAMINHAMENTO**")
            contagem_enc = df_filtrado['encaminhamento'].value_counts().reset_index()
            contagem_enc.columns = ['ENCAMINHAMENTO', 'QUANTIDADE']
            st.dataframe(contagem_enc, hide_index=True, use_container_width=True, height=250)

    with col_sup_dir:
        m = folium.Map(location=[-3.119, -60.021], zoom_start=12, tiles="CartoDB positron") 
        for idx, row in df_filtrado.iterrows():
            try:
                lat, lon = float(row.get('latitude')), float(row.get('longitude'))
                risco_upper = row.get('risco_padrao', 'MÉDIO')
                cor_hex = CORES_RISCO_HEX.get(risco_upper, '#9E9E9E') 
                cor_icone = CORES_RISCO_PINO.get(risco_upper, 'gray')
                
                folium.Marker(
                    [lat, lon],
                    popup=f"<b>{row.get('tipo_emoji')}</b>",
                    icon=folium.Icon(color=cor_icone, icon="info-sign")
                ).add_to(m)
                
                folium.Circle(
                    location=[lat, lon],
                    radius=260, 
                    color=cor_hex, fill=True, fill_opacity=0.4
                ).add_to(m)
            except: continue
        st_folium(m, use_container_width=True, height=350)

    st.write("---")
    col_inf_esq, col_inf_dir = st.columns([1, 1.3])
    with col_inf_esq:
        c1, c2 = st.columns([1, 2])
        c1.metric("TOTAL", len(df_filtrado))
        with c2:
            fig = px.pie(df_filtrado, names='risco_padrao', hole=0.4, color='risco_padrao', color_discrete_map=CORES_RISCO_HEX)
            fig.update_layout(height=200, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='white', plot_bgcolor='white', font=dict(color='black'))
            st.plotly_chart(fig, use_container_width=True, theme=None)
    with col_inf_dir:
        df_g = df_filtrado[df_filtrado['Mes_Filtro'] != 'Desconhecido']
        if not df_g.empty:
            fig_bar = px.bar(df_g['Mes_Filtro'].value_counts().reset_index(), x='Mes_Filtro', y='count')
            fig_bar.update_traces(marker_color='#191970')
            fig_bar.update_layout(height=200, margin=dict(t=10, b=0, l=0, r=0), paper_bgcolor='white', plot_bgcolor='white', font=dict(color='black'))
            st.plotly_chart(fig_bar, use_container_width=True, theme=None)
