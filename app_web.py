import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime
from core.database import obter_referencia

# ==========================================
# 1. CONFIGURAÇÃO GERAL E TEMA INSTITUCIONAL
# ==========================================
st.set_page_config(page_title="Plataforma Integrada - Defesa Civil AM", layout="wide", initial_sidebar_state="expanded")

# CSS Profissional / Design System
st.markdown("""
    <style>
    /* Ocultar elementos nativos do Streamlit para visual limpo */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Fundo geral da aplicação */
    .stApp { background-color: #F4F7F9 !important; font-family: 'Inter', 'Segoe UI', sans-serif; }

    /* --- TELA DE LOGIN --- */
    .login-wrapper {
        display: flex; justify-content: center; align-items: center; height: 85vh;
    }
    .login-card {
        background: #FFFFFF; border-radius: 12px; padding: 40px; width: 100%; max-width: 450px;
        box-shadow: 0 10px 25px rgba(15, 32, 64, 0.1); border: 1px solid #E2E8F0; text-align: center;
    }
    .login-title { color: #0F2040; font-weight: 800; font-size: 22px; margin-bottom: 5px; letter-spacing: 0.5px; }
    .login-subtitle { color: #64748B; font-size: 14px; margin-bottom: 30px; }

    /* --- COMPONENTES GERAIS (CARTÕES E CABEÇALHOS) --- */
    .institucional-header {
        background: #0F2040; color: #FFFFFF; padding: 18px 24px; border-radius: 8px;
        margin-bottom: 24px; font-weight: 700; font-size: 20px; display: flex; align-items: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-transform: uppercase; letter-spacing: 1px;
    }
    .institucional-card {
        background: #FFFFFF; border-radius: 10px; padding: 24px; margin-bottom: 20px;
        border: 1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(15, 32, 64, 0.04);
    }
    .card-title {
        color: #0F2040; font-weight: 700; font-size: 15px; margin-bottom: 16px;
        text-transform: uppercase; border-bottom: 2px solid #F1F5F9; padding-bottom: 10px;
    }

    /* --- MÉTRICAS E FORMS --- */
    div[data-testid="metric-container"] { background-color: #FFFFFF !important; padding: 15px !important; border-radius: 8px; border: 1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.02); text-align: center; }
    div[data-testid="stMetricValue"] > div { color: #0F2040 !important; font-size: 38px !important; font-weight: 800 !important; }
    div[data-testid="stMetricLabel"] > div { color: #64748B !important; font-size: 14px !important; font-weight: 600 !important; text-transform: uppercase; }
    
    /* Input Fields */
    .stTextInput>div>div>input, .stSelectbox>div>div>div { border-radius: 6px !important; border: 1px solid #CBD5E1 !important; color: #1E293B !important; }
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>div:focus { border-color: #0F2040 !important; box-shadow: 0 0 0 1px #0F2040 !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ROTEAMENTO E SESSÃO
# ==========================================
if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
if "rota" not in st.session_state: st.session_state["rota"] = "login"

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
        colunas_padrao = {'tipo': 'Não Informado', 'encaminhamento': 'Não Informado', 'risco': 'MÉDIO', 'data': '', 'bairro': 'Não Informado', 'municipio': 'Manaus', 'endereco': ''}
        for col, padrao in colunas_padrao.items():
            if col not in df.columns: df[col] = padrao
            
        df['tipo_emoji'] = df['tipo'].apply(adicionar_emoji_natureza)
        df['risco_padrao'] = df['risco'].astype(str).str.strip().str.upper()
        df['data_dt'] = pd.to_datetime(df['data'], errors='coerce', dayfirst=True)
        df['Ano_Filtro'] = df['data_dt'].dt.year.fillna(0).astype(int).astype(str).replace('0', 'Desconhecido')
        df['Mes_Filtro'] = df['data_dt'].dt.strftime('%m').fillna('Desconhecido')
        return df
    except Exception as e:
        st.error(f"Erro de conexão com o Banco de Dados: {e}")
        return pd.DataFrame()

# ==========================================
# 4. TELA: LOGIN
# ==========================================
def tela_login():
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    _, col_centro, _ = st.columns([1, 1.2, 1])
    
    with col_centro:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.image("https://raw.githubusercontent.com/EBRlock/dashboard-defesa-civil/main/assets/logo_defesa.png", width=140)
        st.markdown("<div class='login-title'>DEFESA CIVIL DO AMAZONAS</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-subtitle'>Sistema Integrado de Gestão e Monitoramento</div>", unsafe_allow_html=True)
        
        usuario = st.text_input("Credencial de Acesso", placeholder="Digite seu usuário")
        senha = st.text_input("Palavra-passe", type="password", placeholder="Digite sua senha")
        
        st.write("")
        if st.button("AUTENTICAR", use_container_width=True, type="primary"):
            if (usuario == "gestaodefesacivil" and senha == "defesacivilam26") or (usuario == "admin" and senha == "1234"):
                st.session_state["autenticado"] = True
                navegar("hub")
            else:
                st.error("Acesso negado. Credenciais incorretas.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 5. TELA: HUB CENTRAL
# ==========================================
def tela_hub():
    st.markdown("<div class='institucional-header'>🎛️ PORTAL DE OPERAÇÕES - ESCOLHA O MÓDULO</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='institucional-card'>", unsafe_allow_html=True)
    st.write("Seja bem-vindo ao Sistema Integrado. Selecione abaixo a ferramenta desejada para iniciar sua sessão de trabalho.")
    st.write("")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("📊 **MÓDULO DE INTELIGÊNCIA**\n\nMonitoramento em tempo real, mapas de calor e estatísticas operacionais.")
        if st.button("Abrir Painel Tático", use_container_width=True): navegar("dashboard")
            
    with col2:
        st.success("📝 **MÓDULO DE REGISTRO**\n\nLançamento de novas ocorrências com captura de geolocalização via satélite.")
        if st.button("Registrar Ocorrência", use_container_width=True): navegar("registro")
            
    with col3:
        st.error("⚙️ **MÓDULO DE ADMINISTRAÇÃO**\n\nGestão do banco de dados bruto, exportação de relatórios (CSV) e exclusões.")
        if st.button("Acessar Admin", use_container_width=True): navegar("admin")
        
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 6. MENU LATERAL (SIDEBAR)
# ==========================================
def renderizar_sidebar():
    with st.sidebar:
        col1, col2, col3 = st.columns([1, 8, 1])
        with col2: st.image("https://raw.githubusercontent.com/EBRlock/dashboard-defesa-civil/main/assets/logo_defesa.png", use_container_width=True)
        
        st.markdown("<div style='text-align:center; color:#0F2040; font-weight:bold; margin-bottom: 20px;'>MENU DE NAVEGAÇÃO</div>", unsafe_allow_html=True)
        
        if st.button("🏠 Início (Hub)", use_container_width=True): navegar("hub")
        if st.button("📊 Painel Tático", use_container_width=True): navegar("dashboard")
        if st.button("📝 Novo Registro", use_container_width=True): navegar("registro")
        if st.button("⚙️ Administração", use_container_width=True): navegar("admin")
            
        st.markdown("<br><hr style='border-color: #E2E8F0;'><br>", unsafe_allow_html=True)
        if st.button("🚪 Encerrar Sessão", use_container_width=True, type="secondary"):
            st.session_state["autenticado"] = False; navegar("login")

# ==========================================
# 7. TELA: DASHBOARD TÁTICO
# ==========================================
def tela_dashboard():
    df = carregar_dados()
    if df.empty:
        st.info("Aguardando sincronização com o banco de dados oficial...")
        return

    st.markdown("<div class='institucional-header'>📊 PAINEL TÁTICO DE MONITORAMENTO</div>", unsafe_allow_html=True)
    
    # Filtros
    st.markdown("<div class='institucional-card'><div class='card-title'>Filtros de Operação</div>", unsafe_allow_html=True)
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    f_tipo = col_f1.selectbox("Natureza", ["Todas"] + sorted(df['tipo_emoji'].dropna().unique().tolist()))
    f_mun = col_f2.selectbox("Município", ["Todas"] + sorted(df['municipio'].dropna().unique().tolist())) 
    f_bairro = col_f3.selectbox("Bairro", ["Todos"] + sorted(df['bairro'].dropna().unique().tolist())) 
    f_ano = col_f4.selectbox("Ano", ["Todos"] + sorted([a for a in df['Ano_Filtro'].unique() if a != 'Desconhecido'])) 
    f_mes = col_f5.selectbox("Mês", ["Todos"] + sorted([m for m in df['Mes_Filtro'].unique() if m != 'Desconhecido'])) 
    st.markdown("</div>", unsafe_allow_html=True)
    
    df_f = df.copy()
    if f_tipo != "Todas": df_f = df_f[df_f['tipo_emoji'] == f_tipo]
    if f_mun != "Todas": df_f = df_f[df_f['municipio'] == f_mun]
    if f_bairro != "Todos": df_f = df_f[df_f['bairro'] == f_bairro]
    if f_ano != "Todos": df_f = df_f[df_f['Ano_Filtro'] == f_ano]
    if f_mes != "Todos": df_f = df_f[df_f['Mes_Filtro'] == f_mes]

    # KPIs Superiores
    c1, c2, c3 = st.columns(3)
    c1.metric("Ocorrências Filtradas", len(df_f))
    c2.metric("Críticas / Alto Risco", len(df_f[df_f['risco_padrao'].isin(['CRÍTICO', 'CRITICO', 'ALTO'])]))
    c3.metric("Aguardando Vistoria", len(df_f[df_f['encaminhamento'] == 'Aguardando Vistoria']))

    # Mapa e Tabelas
    col_esq, col_dir = st.columns([1, 1.5])
    
    with col_esq:
        st.markdown("<div class='institucional-card'><div class='card-title'>Classificação por Natureza</div>", unsafe_allow_html=True)
        st.dataframe(df_f['tipo_emoji'].value_counts().reset_index(), hide_index=True, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='institucional-card'><div class='card-title'>Status de Encaminhamento</div>", unsafe_allow_html=True)
        st.dataframe(df_f['encaminhamento'].value_counts().reset_index(), hide_index=True, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_dir:
        st.markdown("<div class='institucional-card'><div class='card-title'>Mapa Estratégico de Risco</div>", unsafe_allow_html=True)
        m = folium.Map(location=[-3.119, -60.021], zoom_start=11.5, tiles="CartoDB positron") 
        for _, row in df_f.iterrows():
            try:
                lat, lon = float(row['latitude']), float(row['longitude'])
                tipo_com_emoji, bairro, endereco, risco, data_reg = row.get('tipo_emoji', ''), row.get('bairro', ''), row.get('endereco', ''), row.get('risco_padrao', 'MÉDIO'), row.get('data', '')
                
                cor_hex = CORES_RISCO_HEX.get(risco, '#94A3B8')
                pino = CORES_RISCO_PINO.get(risco, 'gray')
                cor_texto = CORES_TEXTO_RISCO.get(risco, 'white')

                html_popup = f"""<div style="font-family: Arial; min-width: 220px;"><div style="background-color: {cor_hex}; color: {cor_texto}; padding: 8px; font-weight: bold; border-radius: 4px 4px 0 0; text-align: center;">{tipo_com_emoji.upper()}</div><div style="padding: 12px; border: 1px solid #E2E8F0; border-top: none; background-color: #FFFFFF;"><span style="font-size: 11px; color: #64748B;">📅 Registro: {data_reg}</span><br><br><b>📍 Bairro:</b> {bairro}<br><b>⚠️ Risco:</b> {risco.upper()}<br><hr style="margin: 10px 0; border-color: #F1F5F9;"><span style="font-size: 11px; color: #475569;">{endereco}</span></div></div>"""
                
                folium.Marker([lat, lon], tooltip=f"{tipo_com_emoji} ({risco})", popup=folium.Popup(html_popup, max_width=300), icon=folium.Icon(color=pino, icon="info-sign")).add_to(m)
                folium.Circle([lat, lon], radius=260, color=cor_hex, fill=True, fill_opacity=0.35).add_to(m)
            except: continue
        st_folium(m, use_container_width=True, height=450)
        st.markdown("</div>", unsafe_allow_html=True)

    # Gráficos Inferiores
    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        st.markdown("<div class='institucional-card'><div class='card-title'>Proporção de Risco</div>", unsafe_allow_html=True)
        fig_pie = px.pie(df_f['risco_padrao'].value_counts().reset_index(), values='count', names='risco_padrao', hole=0.5, color='risco_padrao', color_discrete_map=CORES_RISCO_HEX)
        fig_pie.update_layout(height=250, margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', showlegend=True)
        st.plotly_chart(fig_pie, use_container_width=True, theme=None)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_graf2:
        st.markdown("<div class='institucional-card'><div class='card-title'>Volume de Ocorrências (Mês)</div>", unsafe_allow_html=True)
        df_g = df_f[df_f['Mes_Filtro'] != 'Desconhecido']
        if not df_g.empty:
            fig_bar = px.bar(df_g['Mes_Filtro'].value_counts().reset_index().sort_values(by='Mes_Filtro'), x='Mes_Filtro', y='count', text='count')
            fig_bar.update_traces(marker_color='#0F2040', textposition='outside') 
            fig_bar.update_layout(height=250, margin=dict(t=20, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis_title="Mês", yaxis_title=None)
            st.plotly_chart(fig_bar, use_container_width=True, theme=None)
        else:
            st.info("Sem dados temporais para exibição.")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 8. TELA: REGISTRAR OCORRÊNCIA
# ==========================================
def tela_registro():
    st.markdown("<div class='institucional-header'>📝 FORMULÁRIO DE OCORRÊNCIA</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='institucional-card'>", unsafe_allow_html=True)
    with st.form("form_registro", clear_on_submit=True):
        st.markdown("<div class='card-title'>Dados Cadastrais</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            natureza = st.selectbox("Natureza do Evento", ["Incêndio", "Alagamento", "Deslizamento", "Desabamento", "Outros"])
            municipio = st.text_input("Município da Ocorrência", value="Manaus")
            bairro = st.text_input("Bairro")
        with col2:
            risco = st.selectbox("Classificação de Risco", ["Baixo", "Médio", "Alto", "Crítico"])
            encaminhamento = st.selectbox("Status Operacional", ["Aguardando Vistoria", "Atendido", "Em Andamento"])
            data_ocorrencia = st.date_input("Data do Registro")
            
        endereco = st.text_input("Endereço Completo (Rua, Número, Referência)")
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("<div class='card-title'>Captura de Coordenadas</div>", unsafe_allow_html=True)
        st.info("Instrução: Navegue pelo mapa abaixo e clique exatamente sobre a rua do incidente para capturar a Latitude e Longitude oficial.")
        m_registro = folium.Map(location=[-3.119, -60.021], zoom_start=12, tiles="CartoDB positron")
        mapa_clicado = st_folium(m_registro, height=350, use_container_width=True, key="mapa_novo")
        
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.form_submit_button("💾 TRANSMITIR PARA O BANCO DE DADOS (FIREBASE)", type="primary", use_container_width=True)
        
        if submit:
            if not bairro or not endereco: st.warning("Exigência: O Bairro e o Endereço são obrigatórios.")
            elif not mapa_clicado.get("last_clicked"): st.warning("Exigência: A marcação no mapa é obrigatória para o georreferenciamento.")
            else:
                lat, lon = mapa_clicado["last_clicked"]["lat"], mapa_clicado["last_clicked"]["lng"]
                novo_registro = {"tipo": natureza, "municipio": municipio, "bairro": bairro, "endereco": endereco, "risco": risco, "encaminhamento": encaminhamento, "data": data_ocorrencia.strftime("%d/%m/%Y"), "latitude": lat, "longitude": lon}
                try:
                    obter_referencia("ocorrencias").push(novo_registro)
                    st.success("Operação concluída. Registro armazenado na nuvem oficial."); st.balloons()
                    carregar_dados.clear()
                except Exception as e: st.error(f"Falha de transmissão: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 9. TELA: ADMINISTRAÇÃO
# ==========================================
def tela_admin():
    st.markdown("<div class='institucional-header' style='background: #7F1D1D;'>⚙️ PAINEL DO ADMINISTRADOR DE SISTEMAS</div>", unsafe_allow_html=True)
    st.error("**ATENÇÃO:** Módulo restrito. As operações realizadas nesta tela refletem diretamente no banco de dados em produção.")
    
    df = carregar_dados()
    if df.empty: st.info("O repositório de dados está vazio."); return

    tab1, tab2 = st.tabs(["🗄️ Auditoria de Dados Brutos", "🗑️ Manutenção de Registros"])
    
    with tab1:
        st.markdown("<div class='institucional-card'><div class='card-title'>Repositório Firebase</div>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, height=400)
        
        csv = df.to_csv(index=True).encode('utf-8')
        st.download_button(label="📥 GERAR RELATÓRIO OFICIAL (CSV)", data=csv, file_name=f'defesa_civil_backup_{datetime.now().strftime("%Y%m%d")}.csv', mime='text/csv', type="primary")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with tab2:
        st.markdown("<div class='institucional-card'><div class='card-title'>Exclusão Definitiva</div>", unsafe_allow_html=True)
        st.write("Localize e selecione a entrada que deseja revogar do sistema:")
        
        opcoes_delete = {f"Data: {row.get('data', 'N/A')} | Natureza: {row.get('tipo', 'N/A')} | Bairro: {row.get('bairro', 'N/A')} [ID: {idx}]": idx for idx, row in df.iterrows()}
        registro_selecionado = st.selectbox("Registro Alvo:", list(opcoes_delete.keys()))
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚨 CONFIRMAR EXCLUSÃO DO REGISTRO", type="primary"):
            id_firebase = opcoes_delete[registro_selecionado]
            try:
                obter_referencia(f"ocorrencias/{id_firebase}").delete()
                st.success("Ação executada: Registro removido permanentemente da nuvem.")
                carregar_dados.clear(); st.rerun()
            except Exception as e: st.error(f"Falha na exclusão: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 10. ROTEADOR PRINCIPAL DE EXECUÇÃO
# ==========================================
if not st.session_state["autenticado"]:
    tela_login()
else:
    renderizar_sidebar()
    if st.session_state["rota"] == "hub": tela_hub()
    elif st.session_state["rota"] == "dashboard": tela_dashboard()
    elif st.session_state["rota"] == "registro": tela_registro()
    elif st.session_state["rota"] == "admin": tela_admin()
