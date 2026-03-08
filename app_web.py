import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from core.database import obter_referencia

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Gestão Defesa Civil - Login", layout="wide", initial_sidebar_state="collapsed")

# CSS para Estilização Geral
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #F4F6F9; }
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
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# SISTEMA DE LOGIN
# ==========================================
def tela_login():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.write("") 
        st.image("https://raw.githubusercontent.com/EBRlock/dashboard-defesa-civil/main/assets/logo_defesa.png", width=200)
        st.subheader("🔐 Acesso Restrito")
        
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        
        if st.button("Entrar"):
            if usuario == "gestaodefesacivil" and senha == "defesacivilam26":
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Usuário ou Senha incorretos.")

# Verifica se o usuário já logou nesta sessão
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    tela_login()
    st.stop() # Interrompe a execução aqui até logar

# ==========================================
# FUNÇÕES DE APOIO (EMOJIS E CORES)
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
# CONTEÚDO DO DASHBOARD (SÓ APARECE APÓS LOGIN)
# ==========================================
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
                
                # RAIO REDUZIDO 3X (De 800m para 260m)
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
            fig.update_layout(height=200, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True, theme=None)
    with col_inf_dir:
        df_g = df_filtrado[df_filtrado['Mes_Filtro'] != 'Desconhecido']
        if not df_g.empty:
            fig_bar = px.bar(df_g['Mes_Filtro'].value_counts().reset_index(), x='Mes_Filtro', y='count')
            fig_bar.update_layout(height=200, margin=dict(t=10, b=0, l=0, r=0))
            st.plotly_chart(fig_bar, use_container_width=True, theme=None)
