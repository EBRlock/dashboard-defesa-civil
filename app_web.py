import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime
from core.database import obter_referencia

# ==========================================
# CONFIGURAÇÃO GERAL E CSS PREMIUM
# ==========================================
st.set_page_config(page_title="Gestão Defesa Civil - Plataforma", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<script>document.title = 'Plataforma - Defesa Civil';</script>""", unsafe_allow_html=True)

st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    .stApp { background-color: #F8FAFC !important; }

    /* Login Limpo e Centralizado */
    .login-container {
        max-width: 420px; margin: 12vh auto; padding: 50px;
        background-color: white; border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1); text-align: center; border: 1px solid #E0E0E0;
    }
    .login-container h2, .login-container label { color: #191970 !important; font-weight: bold; }
    
    /* Cartões Premium */
    .premium-card {
        background-color: #FFFFFF; border-radius: 12px; padding: 20px;
        border: 1px solid #E0E0E0; box-shadow: 0 4px 6px rgba(0,0,0,0.03); margin-bottom: 15px;
    }
    .card-header {
        font-weight: bold; color: #191970; text-transform: uppercase; letter-spacing: 1px;
        font-size: 14px; margin-bottom: 12px; border-bottom: 2px solid #D0D0D0; padding-bottom: 6px;
    }
    .cabecalho-principal {
        background: linear-gradient(135deg, #191970 0%, #1a1a9e 100%); color: white;
        padding: 15px 25px; border-radius: 8px; margin-bottom: 18px; font-weight: bold;
        font-family: 'Segoe UI', Arial, sans-serif; font-size: 20px; text-transform: uppercase;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }
    
    /* Métricas e Filtros */
    div[data-testid="metric-container"] { border: none !important; background-color: transparent !important; text-align: center; }
    div[data-testid="stMetricValue"] > div { color: #191970 !important; font-size: 42px !important; font-weight: 800 !important; }
    div[data-testid="stSelectbox"] > div > div > div > div > div { background-color: #FFFFFF !important; border: 1px solid #CCCCCC !important; border-radius: 6px !important; }
    div[data-testid="stSelectbox"] label { color: #555555 !important; font-weight: 600 !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# VARIÁVEIS DE SESSÃO (ROTEAMENTO)
# ==========================================
if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
if "rota" not in st.session_state: st.session_state["rota"] = "login"
def navegar(nova_rota): st.session_state["rota"] = nova_rota; st.rerun()

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
        if not dados: return pd.DataFrame()
        
        # Orient='index' garante que o ID do Firebase vire o index do DataFrame (Crucial para o Admin deletar)
        df = pd.DataFrame.from_dict(dados, orient='index')
        
        colunas_padrao = {'tipo': 'Não Informado', 'encaminhamento': 'Não Informado', 'risco': 'MÉDIO', 'data': '', 'bairro': 'Não Informado', 'municipio': 'Manaus'}
        for col, padrao in colunas_padrao.items():
            if col not in df.columns: df[col] = padrao
        
        df['tipo_emoji'] = df['tipo'].apply(adicionar_emoji_natureza)
        df['risco_padrao'] = df['risco'].astype(str).str.strip().str.upper()
        df['data_dt'] = pd.to_datetime(df['data'], errors='coerce', dayfirst=True)
        df['Ano_Filtro'] = df['data_dt'].dt.year.fillna(0).astype(int).astype(str).replace('0', 'Desconhecido')
        df['Mes_Filtro'] = df['data_dt'].dt.strftime('%m').fillna('Desconhecido')
        return df
    except Exception as e: st.error(f"🛑 Erro ao carregar dados: {e}"); return pd.DataFrame()

# ==========================================
# TELA 1: LOGIN
# ==========================================
def tela_login():
    _, col_central, _ = st.columns([1, 1.3, 1])
    with col_central:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.image("https://raw.githubusercontent.com/EBRlock/dashboard-defesa-civil/main/assets/logo_defesa.png", use_container_width=True)
        st.markdown("<h2 style='margin-top: 15px; margin-bottom: 25px;'>Defesa Civil AM</h2>", unsafe_allow_html=True)
        
        usuario = st.text_input("Usuário", key="usr")
        senha = st.text_input("Senha", type="password", key="pwd")
        
        st.write("")
        if st.button("ENTRAR", use_container_width=True, type="primary"):
            if (usuario == "gestaodefesacivil" and senha == "defesacivilam26") or (usuario == "admin" and senha == "1234"):
                st.session_state["autenticado"] = True; navegar("dashboard")
            else: st.error("Credenciais inválidas.")
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# MENU LATERAL (HUB)
# ==========================================
def renderizar_sidebar():
    with st.sidebar:
        st.image("https://raw.githubusercontent.com/EBRlock/dashboard-defesa-civil/main/assets/logo_defesa.png", width=160)
        st.markdown("<h3 style='color: #191970; text-align: center;'>🎛️ HUB DE GESTÃO</h3>", unsafe_allow_html=True)
        st.divider()
        
        if st.button("📊 Dashboard Tático", use_container_width=True): navegar("dashboard")
        if st.button("📝 Registrar Ocorrência", use_container_width=True): navegar("registro")
        if st.button("⚙️ Painel do Administrador", use_container_width=True): navegar("admin")
            
        st.divider()
        if st.button("🚪 Logoff / Sair", use_container_width=True):
            st.session_state["autenticado"] = False; navegar("login")

# ==========================================
# TELA 2: DASHBOARD (Monitoramento)
# ==========================================
def tela_dashboard():
    df = carregar_dados()
    if df.empty: st.info("Aguardando carregamento de dados do banco Firebase..."); return

    st.markdown("<div class='cabecalho-principal'>📋 PAINEL TÁTICO - MONITORAMENTO EM TEMPO REAL</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='premium-card'><div class='card-header'>🔍 FILTROS RÁPIDOS</div>", unsafe_allow_html=True)
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    f_tipo = col_f1.selectbox("NATUREZA", ["Todas"] + df['tipo_emoji'].dropna().unique().tolist())
    f_mun = col_f2.selectbox("MUNICÍPIO", ["Todas"] + df['municipio'].dropna().unique().tolist()) 
    f_bairro = col_f3.selectbox("BAIRRO", ["Todos"] + df['bairro'].dropna().unique().tolist()) 
    f_ano = col_f4.selectbox("ANO", ["Todos"] + sorted([a for a in df['Ano_Filtro'].unique() if a != 'Desconhecido'])) 
    f_mes = col_f5.selectbox("MÊS", ["Todos"] + sorted([m for m in df['Mes_Filtro'].unique() if m != 'Desconhecido'])) 
    st.markdown("</div>", unsafe_allow_html=True)
    
    df_f = df.copy()
    if f_tipo != "Todas": df_f = df_f[df_f['tipo_emoji'] == f_tipo]
    if f_mun != "Todas": df_f = df_f[df_f['municipio'] == f_mun]
    if f_bairro != "Todos": df_f = df_f[df_f['bairro'] == f_bairro]
    if f_ano != "Todos": df_f = df_f[df_f['Ano_Filtro'] == f_ano]
    if f_mes != "Todos": df_f = df_f[df_f['Mes_Filtro'] == f_mes]

    col_sup_esq, col_sup_dir = st.columns([1, 1.3])
    with col_sup_esq:
        c1, c2 = st.columns(2)
        with c1: st.markdown("<div class='premium-card'><div class='card-header'>📊 Natureza</div>", unsafe_allow_html=True); st.dataframe(df_f['tipo_emoji'].value_counts().reset_index(), hide_index=True, use_container_width=True, height=250); st.markdown("</div>", unsafe_allow_html=True)
        with c2: st.markdown("<div class='premium-card'><div class='card-header'>📋 Encaminhamento</div>", unsafe_allow_html=True); st.dataframe(df_f['encaminhamento'].value_counts().reset_index(), hide_index=True, use_container_width=True, height=250); st.markdown("</div>", unsafe_allow_html=True)

    with col_sup_dir:
        st.markdown("<div class='premium-card'><div class='card-header'>🗺️ MAPA TÁTICO - MANAUS</div>", unsafe_allow_html=True)
        m = folium.Map(location=[-3.119, -60.021], zoom_start=11.5, tiles="CartoDB positron") 
        for _, row in df_f.iterrows():
            try:
                lat, lon = float(row['latitude']), float(row['longitude'])
                tipo_com_emoji, bairro, endereco, risco, data_reg = row.get('tipo_emoji', ''), row.get('bairro', ''), row.get('endereco', ''), row.get('risco_padrao', 'MÉDIO'), row.get('data', '')
                
                tipo_upper = str(row['tipo']).upper()
                if 'INCÊNDIO' in tipo_upper: cor_hex, pino = '#F44336', 'red'
                elif 'DESLIZAMENTO' in tipo_upper: cor_hex, pino = '#FF9800', 'orange'
                elif 'ALAGAMENTO' in tipo_upper: cor_hex, pino = '#2196F3', 'blue'
                elif 'DESABAMENTO' in tipo_upper: cor_hex, pino = '#B71C1C', 'darkred'
                else: cor_hex, pino = '#607D8B', 'cadetblue'

                cor_risco_fundo = CORES_RISCO_HEX.get(risco, '#999')
                cor_risco_texto = CORES_TEXTO_RISCO.get(risco, 'white')

                html_popup = f"""<div style="font-family: Arial; min-width: 200px;"><div style="background-color: {cor_hex}; color: white; padding: 6px; font-weight: bold; border-radius: 4px 4px 0 0; text-align: center; font-size: 14px;">{tipo_com_emoji.upper()}</div><div style="padding: 10px; border: 1px solid #CCC; border-top: none; background-color: #FAFAFA;"><span style="font-size: 11px; color: #888;">📅 {data_reg}</span><br><b>📍 Bairro:</b> {bairro}<br><div style="margin-top: 5px;"><b>Risco:</b> <span style="background-color: {cor_risco_fundo}; color: {cor_risco_texto}; padding: 2px 6px; border-radius: 10px; font-size: 11px; font-weight: bold;">{risco.upper()}</span></div><hr style="margin: 8px 0; border-color: #EEE;"><span style="font-size: 11px;">{endereco}</span></div></div>"""
                
                folium.Marker([lat, lon], tooltip=f"{tipo_com_emoji} - {bairro}", popup=folium.Popup(html_popup, max_width=300), icon=folium.Icon(color=pino, icon="info-sign")).add_to(m)
                folium.Circle([lat, lon], radius=260, color=cor_hex, fill=True, fill_opacity=0.3).add_to(m)
            except: continue
        st_folium(m, use_container_width=True, height=350)
        st.markdown("</div>", unsafe_allow_html=True)

    col_inf_esq, col_inf_dir = st.columns([1, 1.3])
    with col_inf_esq:
        st.markdown("<div class='premium-card'><div class='card-header'>🛡️ RESUMO TÁTICO</div>", unsafe_allow_html=True)
        c_met, c_pie = st.columns([1, 2.2])
        with c_met: st.metric("🛡️ Ocorrências Ativas", len(df_f)); st.write("<div style='font-size: 11px; color: #888;'>Filtro Ativo</div>", unsafe_allow_html=True)
        fig_pie = px.pie(df_f['risco_padrao'].value_counts().reset_index(), values='count', names='risco_padrao', hole=0.4, color='risco_padrao', color_discrete_map=CORES_RISCO_HEX)
        fig_pie.update_layout(height=180, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', showlegend=True)
        c_pie.plotly_chart(fig_pie, use_container_width=True, theme=None)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_inf_dir:
        st.markdown("<div class='premium-card'><div class='card-header'>📉 TENDÊNCIA TEMPORAL (POR MÊS)</div>", unsafe_allow_html=True)
        df_g = df_f[df_f['Mes_Filtro'] != 'Desconhecido']
        if not df_g.empty:
            fig_bar = px.bar(df_g['Mes_Filtro'].value_counts().reset_index().sort_values(by='Mes_Filtro'), x='Mes_Filtro', y='count', text='count')
            fig_bar.update_traces(marker_color='#191970', textposition='outside') 
            fig_bar.update_layout(height=180, margin=dict(t=10, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='white', xaxis_title="Mês do Ano", yaxis_title=None)
            st.plotly_chart(fig_bar, use_container_width=True, theme=None)
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# TELA 3: REGISTRAR OCORRÊNCIA
# ==========================================
def tela_registro():
    st.markdown("<div class='cabecalho-principal'>📝 REGISTRO DE NOVA OCORRÊNCIA</div>", unsafe_allow_html=True)
    
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
        
        st.markdown("<div class='premium-card'><div class='card-header'>📍 LOCALIZAÇÃO EXATA (Clique no mapa)</div>", unsafe_allow_html=True)
        st.info("A coordenada será salva automaticamente ao tocar no local da rua.")
        m_registro = folium.Map(location=[-3.119, -60.021], zoom_start=12, tiles="CartoDB positron")
        mapa_clicado = st_folium(m_registro, height=350, use_container_width=True, key="mapa_novo")
        st.markdown("</div>", unsafe_allow_html=True)
        
        submit = st.form_submit_button("💾 SALVAR REGISTRO NO BANCO DE DADOS", type="primary", use_container_width=True)
        
        if submit:
            if not bairro or not endereco: st.warning("Por favor, preencha o Bairro e o Endereço.")
            elif not mapa_clicado.get("last_clicked"): st.warning("⚠️ Você precisa tocar no mapa para marcar o local exato!")
            else:
                lat, lon = mapa_clicado["last_clicked"]["lat"], mapa_clicado["last_clicked"]["lng"]
                novo_registro = {"tipo": natureza, "municipio": municipio, "bairro": bairro, "endereco": endereco, "risco": risco, "encaminhamento": encaminhamento, "data": data_ocorrencia.strftime("%d/%m/%Y"), "latitude": lat, "longitude": lon}
                try:
                    ref = obter_referencia("ocorrencias")
                    ref.push(novo_registro)
                    st.success("✅ Ocorrência registrada com sucesso na nuvem!"); st.balloons()
                    carregar_dados.clear()
                except Exception as e: st.error(f"Erro ao salvar: {e}")

# ==========================================
# TELA 4: PAINEL DO ADMINISTRADOR
# ==========================================
def tela_admin():
    st.markdown("<div class='cabecalho-principal' style='background: linear-gradient(135deg, #8B0000 0%, #B22222 100%);'>⚙️ PAINEL DO ADMINISTRADOR</div>", unsafe_allow_html=True)
    st.warning("⚠️ **ÁREA RESTRITA:** As ações realizadas aqui afetam permanentemente o banco de dados oficial da Defesa Civil.")
    
    df = carregar_dados()
    if df.empty:
        st.info("O banco de dados está vazio.")
        return

    tab1, tab2 = st.tabs(["🗄️ Banco de Dados Bruto", "🗑️ Gerenciar / Excluir Registros"])
    
    with tab1:
        st.markdown("<div class='premium-card'><div class='card-header'>VISÃO GERAL DO FIREBASE</div>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, height=400)
        
        # Botão de Exportação para Excel/CSV
        csv = df.to_csv(index=True).encode('utf-8')
        st.download_button(
            label="📥 Exportar Dados para Excel (CSV)",
            data=csv,
            file_name=f'defesa_civil_export_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
            type="primary"
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
    with tab2:
        st.markdown("<div class='premium-card'><div class='card-header'>EXCLUSÃO DE OCORRÊNCIAS</div>", unsafe_allow_html=True)
        st.write("Selecione a ocorrência abaixo para apagá-la permanentemente do sistema.")
        
        # Cria um dicionário legível para o usuário selecionar, onde a 'chave' é o visual e o 'valor' é o ID do Firebase
        opcoes_delete = {f"{row.get('data', 'Sem data')} | {row.get('tipo', 'Desconhecido')} - {row.get('bairro', 'Sem Bairro')} (ID: {idx})": idx for idx, row in df.iterrows()}
        
        registro_selecionado = st.selectbox("Selecione o registro para exclusão:", list(opcoes_delete.keys()))
        
        st.write("")
        if st.button("🚨 EXCLUIR REGISTRO PERMANENTEMENTE", type="primary"):
            id_firebase = opcoes_delete[registro_selecionado]
            try:
                # Conecta no caminho exato daquela ocorrência no Firebase e deleta
                ref = obter_referencia(f"ocorrencias/{id_firebase}")
                ref.delete()
                
                st.success(f"✅ O registro foi apagado com sucesso!")
                carregar_dados.clear() # Limpa o cache para o Dashboard atualizar na hora
                st.rerun() # Recarrega a página
            except Exception as e:
                st.error(f"Erro ao tentar excluir: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# ROTEADOR PRINCIPAL (EXECUÇÃO)
# ==========================================
if not st.session_state["autenticado"]:
    tela_login()
else:
    renderizar_sidebar()
    if st.session_state["rota"] == "dashboard": tela_dashboard()
    elif st.session_state["rota"] == "registro": tela_registro()
    elif st.session_state["rota"] == "admin": tela_admin()
