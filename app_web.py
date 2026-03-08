import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from core.database import obter_referencia

# ==========================================
# CONFIGURAÇÃO E COMPACTAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Painel Call Center - Defesa Civil", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .block-container {
        padding-top: 3rem; 
        padding-bottom: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    
    .stApp { background-color: #F4F6F9; }
    
    .cabecalho {
        background-color: #191970; 
        color: white; 
        padding: 12px 20px; 
        border-radius: 4px; 
        margin-bottom: 15px;
        font-weight: bold;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 18px;
        text-transform: uppercase;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    div[data-testid="metric-container"] {
        background-color: white; 
        border: 1px solid #D0D0D0; 
        border-radius: 4px; 
        padding: 15px; 
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricValue"] > div { 
        color: #191970 !important; 
        font-size: 36px !important; 
        font-weight: bold; 
    }
    
    h3, p, strong { color: #333333 !important; font-family: 'Segoe UI', Arial, sans-serif; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# FUNÇÃO DE DADOS (AGORA COM TRATAMENTO DE DATAS)
# ==========================================
@st.cache_data(ttl=60)
def carregar_dados():
    try:
        ref = obter_referencia("ocorrencias")
        dados = ref.get()
        if dados:
            df = pd.DataFrame.from_dict(dados, orient='index')
            colunas_padrao = {'tipo': 'Não Informado', 'encaminhamento': 'Não Informado', 
                              'risco': 'Médio', 'data': '', 'bairro': 'Não Informado', 'municipio': 'Manaus'}
            for col, padrao in colunas_padrao.items():
                if col not in df.columns:
                    df[col] = padrao
            
            # --- INTELIGÊNCIA DE DATAS ---
            # Tenta converter a string de data para um formato datetime compreensível
            df['data_dt'] = pd.to_datetime(df['data'], errors='coerce', dayfirst=True)
            # Extrai o Ano (como texto para não ficar 2026.0)
            df['Ano_Filtro'] = df['data_dt'].dt.year.fillna(0).astype(int).astype(str).replace('0', 'Desconhecido')
            # Extrai o Mês (ex: '03', '12')
            df['Mes_Filtro'] = df['data_dt'].dt.strftime('%m').fillna('Desconhecido')
            
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"🛑 ERRO DETALHADO DO SISTEMA: {e}")
        return pd.DataFrame()

df = carregar_dados()

if not df.empty:
    # ==========================================
    # BARRA SUPERIOR (FILTROS)
    # ==========================================
    st.markdown("<div class='cabecalho'>PAINEL DE ATENDIMENTO DO CALL CENTER - DEFESA CIVIL DO ESTADO DO AMAZONAS</div>", unsafe_allow_html=True)
    
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    
    tipos = ["Todas"] + df['tipo'].dropna().unique().tolist()
    municipios = ["Todas"] + df['municipio'].dropna().unique().tolist()
    bairros = ["Todos"] + df['bairro'].dropna().unique().tolist()
    
    # Puxa anos e meses reais do banco, removendo os 'Desconhecidos' para a lista ficar limpa
    anos_reais = sorted([a for a in df['Ano_Filtro'].unique() if a != 'Desconhecido'])
    meses_reais = sorted([m for m in df['Mes_Filtro'].unique() if m != 'Desconhecido'])
    
    filtro_tipo = col_f1.selectbox("NATUREZA", tipos)
    filtro_mun = col_f2.selectbox("MUNICÍPIO", municipios) 
    filtro_bairro = col_f3.selectbox("BAIRRO", bairros) 
    filtro_ano = col_f4.selectbox("ANO", ["Todos"] + anos_reais) 
    filtro_mes = col_f5.selectbox("MÊS", ["Todos"] + meses_reais) 
    
    # Aplicação em Cascata de Filtros
    df_filtrado = df.copy()
    if filtro_tipo != "Todas": df_filtrado = df_filtrado[df_filtrado['tipo'] == filtro_tipo]
    if filtro_mun != "Todas": df_filtrado = df_filtrado[df_filtrado['municipio'] == filtro_mun]
    if filtro_bairro != "Todos": df_filtrado = df_filtrado[df_filtrado['bairro'] == filtro_bairro]
    if filtro_ano != "Todos": df_filtrado = df_filtrado[df_filtrado['Ano_Filtro'] == filtro_ano]
    if filtro_mes != "Todos": df_filtrado = df_filtrado[df_filtrado['Mes_Filtro'] == filtro_mes]

    st.markdown("<hr style='margin: 10px 0; border-color: #D0D0D0;'>", unsafe_allow_html=True)

    # ==========================================
    # GRID PRINCIPAL: SUPERIOR (Tabelas e Mapa)
    # ==========================================
    col_sup_esq, col_sup_dir = st.columns([1, 1.3])

    with col_sup_esq:
        tab1, tab2 = st.columns(2)
        with tab1:
            st.markdown("<div style='font-size: 13px; font-weight: bold; margin-bottom: 5px; color: #555;'>NATUREZA</div>", unsafe_allow_html=True)
            contagem_nat = df_filtrado['tipo'].value_counts().reset_index()
            contagem_nat.columns = ['NATUREZA', 'QUANTIDADE']
            st.dataframe(contagem_nat, hide_index=True, use_container_width=True, height=250)
            
        with tab2:
            st.markdown("<div style='font-size: 13px; font-weight: bold; margin-bottom: 5px; color: #555;'>ENCAMINHAMENTO</div>", unsafe_allow_html=True)
            contagem_enc = df_filtrado['encaminhamento'].value_counts().reset_index()
            contagem_enc.columns = ['ENCAMINHAMENTO', 'QUANTIDADE']
            st.dataframe(contagem_enc, hide_index=True, use_container_width=True, height=250)

    with col_sup_dir:
        m = folium.Map(location=[-3.119, -60.021], zoom_start=11.5, tiles="CartoDB positron") 
        
        for idx, row in df_filtrado.iterrows():
            try:
                lat, lon = float(row.get('latitude')), float(row.get('longitude'))
                tipo = str(row.get('tipo', 'Ocorrência'))
                bairro = row.get('bairro', 'Não informado')
                endereco = row.get('endereco', '')
                risco = row.get('risco', 'Médio')
                data_reg = row.get('data', '')
                
                # Definição de Cores da Natureza
                tipo_upper = tipo.upper()
                if 'INCÊNDIO' in tipo_upper:
                    cor_icone, cor_hex = 'red', '#F44336'
                elif 'DESLIZAMENTO' in tipo_upper:
                    cor_icone, cor_hex = 'orange', '#FF9800'
                elif 'ALAGAMENTO' in tipo_upper:
                    cor_icone, cor_hex = 'blue', '#2196F3'
                elif 'DESABAMENTO' in tipo_upper:
                    cor_icone, cor_hex = 'darkred', '#B71C1C'
                else:
                    cor_icone, cor_hex = 'cadetblue', '#607D8B'

                html_popup = f"""
                <div style="font-family: Arial; min-width: 200px;">
                    <div style="background-color: {cor_hex}; color: white; padding: 5px; font-weight: bold; border-radius: 3px 3px 0 0; text-align: center;">
                        {tipo.upper()}
                    </div>
                    <div style="padding: 10px; border: 1px solid #CCC; border-top: none; background-color: #FAFAFA;">
                        <span style="font-size: 11px; color: #888;">{data_reg}</span><br>
                        <b>Bairro:</b> {bairro}<br>
                        <b>Risco:</b> <span>{risco.upper()}</span><br>
                        <hr style="margin: 8px 0; border-color: #EEE;">
                        <span style="font-size: 11px;">{endereco}</span>
                    </div>
                </div>
                """
                
                # 1. O Alfinete (Marcador Principal)
                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(html_popup, max_width=300),
                    tooltip=f"{tipo} - {bairro}",
                    icon=folium.Icon(color=cor_icone, icon="info-sign")
                ).add_to(m)
                
                # 2. A Área de Impacto (Círculo Translúcido)
                folium.Circle(
                    location=[lat, lon],
                    radius=800, # Raio em metros (800m = Área afetada estimada)
                    color=cor_hex, # Bordas na cor exata do evento
                    fill=True,
                    fill_color=cor_hex, # Preenchimento na mesma cor
                    fill_opacity=0.3, # Transparência para não tampar as ruas
                    weight=1.5
                ).add_to(m)

            except:
                continue
        
        st_folium(m, use_container_width=True, height=350)

    st.markdown("<hr style='margin: 10px 0; border-color: #D0D0D0;'>", unsafe_allow_html=True)

    # ==========================================
    # GRID PRINCIPAL: INFERIOR
    # ==========================================
    col_inf_esq, col_inf_dir = st.columns([1, 1.3])

    with col_inf_esq:
        metrica_col, pizza_col = st.columns([1, 2])
        
        with metrica_col:
            st.markdown("<div style='font-size: 13px; font-weight: bold; color: #555;'>Total de Registros</div>", unsafe_allow_html=True)
            st.metric("", len(df_filtrado))
            
        with pizza_col:
            st.markdown("<div style='font-size: 13px; font-weight: bold; color: #555; text-align: center;'>Nível de Risco</div>", unsafe_allow_html=True)
            contagem_risco = df_filtrado['risco'].value_counts().reset_index()
            contagem_risco.columns = ['Risco', 'Qtd']
            cores_risco = {'Alto': '#FF9800', 'Médio': '#FFEB3B', 'Baixo': '#4CAF50', 'Crítico': '#F44336'}
            
            fig_pie = px.pie(contagem_risco, values='Qtd', names='Risco', hole=0.4, 
                             color='Risco', color_discrete_map=cores_risco)
            
            fig_pie.update_layout(
                margin=dict(t=10, b=10, l=10, r=10), 
                height=180,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='black'),
                showlegend=True
            )
            st.plotly_chart(fig_pie, use_container_width=True, theme=None) 

    with col_inf_dir:
        st.markdown("<div style='font-size: 13px; font-weight: bold; color: #555;'>Registros por Mês</div>", unsafe_allow_html=True)
        
        # Filtra registros onde o mês conseguiu ser identificado com sucesso
        df_grafico = df_filtrado[df_filtrado['Mes_Filtro'] != 'Desconhecido']
        
        if not df_grafico.empty:
            contagem_mes = df_grafico['Mes_Filtro'].value_counts().reset_index()
            contagem_mes.columns = ['Mês', 'Quantidade']
            contagem_mes = contagem_mes.sort_values(by='Mês') # Ordena de Janeiro (01) a Dezembro (12)
            
            fig_bar = px.bar(contagem_mes, x='Mês', y='Quantidade')
            fig_bar.update_traces(marker_color='#191970') 
            
            fig_bar.update_layout(
                margin=dict(t=10, b=10, l=10, r=10), 
                height=180, 
                paper_bgcolor='white',
                plot_bgcolor='white',
                font=dict(color='black'),
                xaxis_title="Mês",
                yaxis_title=None
            )
            st.plotly_chart(fig_bar, use_container_width=True, theme=None)
        else:
            st.info("Aguardando registros com datas válidas para montar o gráfico.")

else:
    st.info("Nenhum dado encontrado no banco de dados para montar o painel.")
