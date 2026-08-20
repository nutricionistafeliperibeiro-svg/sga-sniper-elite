import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
import unicodedata
import json
from scipy.stats import poisson, nbinom
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Inteligência de Dados Pré-Live", layout="wide", page_icon="📈")

# Inicialização do Estado
if 'menu' not in st.session_state: st.session_state.menu = 'Principal'
if 'block_matches' not in st.session_state: st.session_state.block_matches = []
if 'block_results' not in st.session_state: st.session_state.block_results = []

# --- ESTILOS CSS (PROFISSIONAL LIGHT) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: #F8FAFC;
        color: #1E293B;
    }
    
    .main-header {
        background: #FFFFFF;
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .title-main {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E40AF;
        margin-bottom: 0.2rem;
    }
    
    .subtitle-main {
        color: #64748B;
        font-size: 1rem;
        font-weight: 500;
    }

    /* Cards Estilizados */
    .card-container {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .card-container:hover {
        border-color: #3B82F6;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    .rating-badge {
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 8px;
        display: inline-block;
    }
    
    .rating-ouro { background-color: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }
    .rating-prata { background-color: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; }
    .rating-risco { background-color: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }

    .ivc-box {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 6px;
        padding: 2px 8px;
        color: #1D4ED8;
        font-weight: 700;
        font-size: 0.8rem;
        display: inline-block;
        margin-left: 4px;
    }

    .stat-label { color: #64748B; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; margin-bottom: 2px; }
    .stat-value { font-size: 1rem; font-weight: 700; }
    .stat-value-green { color: #059669; }
    .stat-value-red { color: #DC2626; }
    
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE DADOS ---
@st.cache_data(ttl=60)
def load_data(file_path):
    try:
        data_dict = {}
        with pd.ExcelFile(file_path) as xls:
            available_sheets = xls.sheet_names
            sheets_to_load = ['Dados', 'Equipes', 'Ligas', 'Radar Over', 'Modelo 01', 'Modelo 02', 'Prova Real', 'Bilhetes', 'Track Record']
            for s in sheets_to_load:
                if s in available_sheets:
                    data_dict[s] = pd.read_excel(xls, sheet_name=s)
        
        if 'Dados' in data_dict:
            df = data_dict['Dados']
            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            data_dict['Dados'] = df
        return data_dict
    except Exception as e:
        st.error(f"Erro ao carregar Excel: {e}")
        return None

EXCEL_PATH = "/home/ubuntu/upload/tabela_de_dados_apostas_V3.xlsx"
all_data = load_data(EXCEL_PATH)

def normalize_text(text):
    if not isinstance(text, str): return ""
    text = text.strip().lower()
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def get_flag_img(country_name):
    country_map = {
        'brasil': 'br', 'argentina': 'ar', 'equador': 'ec', 'china': 'cn', 'islandia': 'is',
        'suecia': 'se', 'noruega': 'no', 'finlandia': 'fi', 'eua': 'us', 'australia': 'au'
    }
    norm_country = normalize_text(country_name)
    code = country_map.get(norm_country, norm_country[:2])
    return f"https://flagcdn.com/w40/{code}.png"

# --- LÓGICA DE CLASSIFICAÇÃO ---
def get_rating_info(ivc):
    if ivc >= 2.40: return "Classe A — Faixa Ouro", "rating-ouro", "🥇"
    if ivc >= 1.83: return "Classe B — Faixa Prata", "rating-prata", "🥈"
    return "Classe C — Faixa de Risco", "rating-risco", "🛑"

def calculate_ivc_soberano(row, df_dados):
    equipe = row['Equipe']
    pais_liga = str(row['País - Liga'])
    liga = pais_liga.split(' - ')[-1] if ' - ' in pais_liga else pais_liga
    
    jogos = df_dados[((df_dados['Mandante'] == equipe) | (df_dados['Visitante'] == equipe)) & (df_dados['Liga'] == liga)].head(12)
    if len(jogos) == 0: return 0, 0, 0, 0
    
    media_geral = (jogos['GM_M'].sum() + jogos['GM_V'].sum()) / len(jogos)
    
    def normalize_outlier(gols, team_avg):
        return team_avg * 0.9 if gols >= 6 else gols
        
    jogos_casa = jogos[jogos['Mandante'] == equipe]
    if not jogos_casa.empty:
        outliers_casa = (jogos_casa['GM_M'] >= 6).sum()
        gols_casa = jogos_casa['GM_M'].apply(lambda x: normalize_outlier(x, media_geral)).mean() if outliers_casa == 1 else jogos_casa['GM_M'].mean()
        gs_casa = jogos_casa['GM_V'].mean()
    else: gols_casa, gs_casa = 0, 0
    
    jogos_fora = jogos[jogos['Visitante'] == equipe]
    if not jogos_fora.empty:
        outliers_fora = (jogos_fora['GM_V'] >= 6).sum()
        gols_fora = jogos_fora['GM_V'].apply(lambda x: normalize_outlier(x, media_geral)).mean() if outliers_fora == 1 else jogos_fora['GM_V'].mean()
        gs_fora = jogos_fora['GM_M'].mean()
    else: gols_fora, gs_fora = 0, 0
    
    return media_geral, (gols_casa * gs_casa), (gols_fora * gs_fora), media_geral

def get_team_stats(team_name, df_dados, df_equipes):
    all_matches = df_dados[(df_dados['Mandante'] == team_name) | (df_dados['Visitante'] == team_name)].sort_values(by='Data', ascending=False)
    team_row = df_equipes[df_equipes['Equipe'] == team_name]
    stats = {'jogos': len(all_matches)}
    if not team_row.empty:
        r = team_row.iloc[0].fillna(0)
        stats.update({'fam': r['FAM'], 'vdm': r['VDM'], 'fav': r['FAV'], 'vdv': r['VDV'], 'dispersao': r['Dispersão'] if 'Dispersão' in r else 1.0})
    return stats

# --- INTERFACE ---
st.markdown(f"""
    <div class="main-header">
        <p class="title-main">Inteligência de Dados Pré-Live</p>
        <p class="subtitle-main">SGA V7.1 — Sniper Elite (Fato Soberano)</p>
    </div>
""", unsafe_allow_html=True)

menu_options = ["Principal", "Confronto", "Análise", "Ranking", "Bilhetes", "Track Record"]
cols_menu = st.columns(len(menu_options))
for i, option in enumerate(menu_options):
    if cols_menu[i].button(option, use_container_width=True):
        st.session_state.menu = option

st.divider()

if all_data:
    df_dados, df_equipes = all_data['Dados'], all_data['Equipes']

    if st.session_state.menu == 'Principal':
        st.subheader("🔥 Máquinas de Gols (Over)")
        
        # Cálculo dos IVCs Soberanos
        ivc_results = df_equipes.apply(lambda x: calculate_ivc_soberano(x, df_dados), axis=1)
        df_equipes['IVC_Geral'], df_equipes['IVC_Casa'], df_equipes['IVC_Fora'], df_equipes['Média Geral'] = zip(*ivc_results)
        
        # Filtro de Volume Mínimo de 25 gols (TGM)
        df_maquinas = df_equipes[df_equipes['TGM'] >= 25].sort_values(by='IVC_Geral', ascending=False).head(15)
        
        cols = st.columns(2)
        for idx, (i, row) in enumerate(df_maquinas.iterrows()):
            col = cols[idx % 2]
            rating_text, rating_class, emoji = get_rating_info(row['IVC_Geral'])
            pais_liga = str(row['País - Liga'])
            pais = pais_liga.split(' - ')[0] if ' - ' in pais_liga else "N/A"
            liga = pais_liga.split(' - ')[-1] if ' - ' in pais_liga else pais_liga
            
            with col:
                st.markdown(f"""
                <div class="card-container">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <span style="font-size: 1.1rem; font-weight: 800; color: #1E3A8A;">{idx+1}. {row['Equipe']}</span><br>
                            <img src="{get_flag_img(pais)}" style="width:18px; vertical-align:middle; border-radius:2px;"> 
                            <span style="font-size: 0.75rem; color: #64748B;">{pais} - {liga}</span>
                        </div>
                        <div style="text-align: right;">
                            <div class="ivc-box">IVC: {row['IVC_Geral']:.2f}</div>
                            <div class="ivc-box">CASA: {row['IVC_Casa']:.2f}</div>
                            <div class="ivc-box">FORA: {row['IVC_Fora']:.2f}</div>
                        </div>
                    </div>
                    <div class="rating-badge {rating_class}" style="margin-top:8px;">{emoji} {rating_text}</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 10px; padding-top: 10px; border-top: 1px solid #F1F5F9;">
                        <div>
                            <p class="stat-label">Casa (Avg)</p>
                            <p><span class="stat-value stat-value-green">{"<b>" if row['FAM']>=3 else ""}{row['FAM']:.2f}{"</b>" if row['FAM']>=3 else ""}</span> 
                               <span style="color:#94A3B8; font-size:0.7rem;">M</span> | 
                               <span class="stat-value stat-value-red">{row['VDM']:.2f}</span> 
                               <span style="color:#94A3B8; font-size:0.7rem;">S</span></p>
                            <p class="stat-label" style="font-size:0.6rem; margin-top:2px;">Força de Ataque Casa: {row['FAM']/1.35:.2f}</p>
                        </div>
                        <div>
                            <p class="stat-label">Fora (Avg)</p>
                            <p><span class="stat-value stat-value-green">{"<b>" if row['FAV']>=3 else ""}{row['FAV']:.2f}{"</b>" if row['FAV']>=3 else ""}</span> 
                               <span style="color:#94A3B8; font-size:0.7rem;">M</span> | 
                               <span class="stat-value stat-value-red">{row['VDV']:.2f}</span> 
                               <span style="color:#94A3B8; font-size:0.7rem;">S</span></p>
                            <p class="stat-label" style="font-size:0.6rem; margin-top:2px;">Força de Ataque Fora: {row['FAV']/1.35:.2f}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background-color:#EFF6FF; padding:1.5rem; border-radius:12px; border:1px solid #BFDBFE; margin-top:1rem;">
            <h4 style="color:#1E40AF; margin-top:0;">🛡️ Doutrina de Classificação Soberana (V7.1)</h4>
            <p style="font-size:0.9rem; color:#1E3A8A; margin-bottom:5px;"><b>1. Força de Ataque:</b> Casa ≥ 1.40 | Fora ≥ 1.30 (em relação à média da liga).</p>
            <p style="font-size:0.9rem; color:#1E3A8A; margin-bottom:5px;"><b>2. Frequência:</b> Mínimo de 4 em 6 jogos cumprindo a meta (2+ em casa, 1+ fora).</p>
            <p style="font-size:0.9rem; color:#1E3A8A; margin-bottom:5px;"><b>3. Volume Mínimo:</b> A equipe deve ter marcado pelo menos 25 gols na janela analisada.</p>
            <p style="font-size:0.9rem; color:#1E3A8A; margin-bottom:5px;"><b>4. IVC (Índice de Volume Cruzado):</b> Mede o cruzamento entre ataque e fragilidade defensiva.</p>
            <ul style="font-size:0.85rem; color:#1E3A8A;">
                <li>🥇 <b>Classe A (Ouro):</b> IVC ≥ 2.40 | 🥈 <b>Classe B (Prata):</b> IVC ≥ 1.83 | 🛑 <b>Classe C (Risco):</b> IVC < 1.83</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    elif st.session_state.menu == 'Confronto':
        st.subheader("⚔️ Simulador de Confronto")
        clubes_list = sorted(df_equipes['Equipe'].unique().tolist())
        c1, c_vs, c2 = st.columns([2, 0.5, 2])
        with c1: mandante = st.selectbox("Mandante", ["Selecione..."] + clubes_list)
        with c_vs: st.markdown('<div style="font-size:2rem; text-align:center; padding-top:20px; color:#CBD5E0;">VS</div>', unsafe_allow_html=True)
        with c2: visitante = st.selectbox("Visitante", ["Selecione..."] + clubes_list)
        
        if mandante != "Selecione..." and visitante != "Selecione...":
            m = get_team_stats(mandante, df_dados, df_equipes)
            v = get_team_stats(visitante, df_dados, df_equipes)
            l_m = (m.get('fam', 0) + v.get('vdv', 0)) / 2
            l_v = (v.get('fav', 0) + m.get('vdm', 0)) / 2
            ge_real = (l_m + l_v) * np.sqrt((m.get('dispersao', 1) + v.get('dispersao', 1)) / 2)
            
            st.markdown(f"""
            <div class="card-container" style="text-align:center; padding:2rem;">
                <p class="stat-label" style="font-size:1rem;">GE Real (Fato Soberano)</p>
                <p style="font-size:4rem; font-weight:800; color:#2563EB; margin:0;">{ge_real:.2f}</p>
                <p class="stat-label">Expectativa: {l_m:.2f} (M) | {l_v:.2f} (V)</p>
            </div>
            """, unsafe_allow_html=True)
            
            p0x0 = (poisson.pmf(0, l_m) * poisson.pmf(0, l_v)) * 100
            st.metric("Risco de 0x0", f"{p0x0:.1f}%", delta="ALERTA" if p0x0 > 8 else "SEGURO", delta_color="inverse")

    elif st.session_state.menu == 'Análise':
        st.subheader("🎯 Análise — Montagem em Bloco")
        clubes_bloco = sorted(df_equipes['Equipe'].unique().tolist())
        with st.form("add_bloco"):
            b1, b2 = st.columns(2)
            with b1: m_b = st.selectbox("Mandante", ["Selecione..."] + clubes_bloco)
            with b2: v_b = st.selectbox("Visitante", ["Selecione..."] + clubes_bloco)
            if st.form_submit_button("＋ Adicionar ao Bloco"):
                if m_b != "Selecione..." and v_b != "Selecione...":
                    st.session_state.block_matches.append({'mandante': m_b, 'visitante': v_b})
                    st.rerun()
        
        if st.session_state.block_matches:
            st.markdown("### 📦 Confrontos no Bloco")
            for idx, conf in enumerate(st.session_state.block_matches):
                st.write(f"**{idx+1}.** {conf['mandante']} x {conf['visitante']}")
            if st.button("🧹 Limpar Bloco"):
                st.session_state.block_matches = []
                st.rerun()

    elif st.session_state.menu == 'Ranking':
        st.subheader("🏆 Radar Over — Aderência")
        if 'Radar Over' in all_data:
            st.dataframe(all_data['Radar Over'].head(60), use_container_width=True)

    elif st.session_state.menu == 'Bilhetes':
        st.subheader("🎫 Bilhetes Processados")
        if 'Bilhetes' in all_data:
            st.dataframe(all_data['Bilhetes'], use_container_width=True)

    elif st.session_state.menu == 'Track Record':
        st.subheader("📊 Track Record — Histórico")
        if 'Track Record' in all_data:
            st.dataframe(all_data['Track Record'], use_container_width=True)
else:
    st.error("Banco de dados V3 não encontrado ou inválido.")
