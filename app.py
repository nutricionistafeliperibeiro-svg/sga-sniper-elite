import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
import unicodedata
import json
from scipy.stats import poisson, nbinom
from datetime import datetime
import streamlit.components.v1 as components

# Configuração da página
st.set_page_config(page_title="Sistema de Apostas — Futebol", layout="wide", page_icon="📈")

# Inicialização do Estado
if 'menu' not in st.session_state: st.session_state.menu = 'Principal'
if 'selected_clube' not in st.session_state: st.session_state.selected_clube = ""
if 'home_view' not in st.session_state: st.session_state.home_view = 'Over'
if 'block_matches' not in st.session_state: st.session_state.block_matches = []
if 'block_notice' not in st.session_state: st.session_state.block_notice = ''
if 'block_results' not in st.session_state: st.session_state.block_results = []

# --- ESTILOS CSS (GLASSMORPHISM & PREMIUM DARK) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: #0F172A;
        color: #F8FAFC;
    }
    
    .main-header {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        padding: 2rem;
        border-radius: 24px;
        border: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .title-main {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38BDF8, #818CF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .subtitle-main {
        color: #94A3B8;
        font-size: 1.1rem;
        font-weight: 400;
    }

    /* Cards Estilizados */
    .card-container {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .card-container:hover {
        transform: translateY(-5px);
        border-color: rgba(56, 189, 248, 0.4);
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
    }

    .rating-badge {
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 10px;
        display: inline-block;
    }
    
    .rating-ouro { background: linear-gradient(135deg, #FCD34D, #D97706); color: #000; }
    .rating-prata { background: linear-gradient(135deg, #CBD5E1, #64748B); color: #fff; }
    .rating-risco { background: linear-gradient(135deg, #F87171, #B91C1C); color: #fff; }

    .ivc-box {
        background: rgba(56, 189, 248, 0.1);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 8px;
        padding: 4px 10px;
        color: #38BDF8;
        font-weight: 800;
        font-size: 0.85rem;
        display: inline-block;
        margin-right: 8px;
    }

    .stat-label { color: #94A3B8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
    .stat-value { font-size: 1.1rem; font-weight: 800; }
    .stat-value-green { color: #34D399; }
    .stat-value-red { color: #F87171; }
    
    .stButton > button {
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        background-color: rgba(30, 41, 59, 0.8) !important;
        color: #F8FAFC !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        border-color: #38BDF8 !important;
        color: #38BDF8 !important;
        background-color: rgba(56, 189, 248, 0.1) !important;
    }

    /* Scrollbar Customizada */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #0F172A; }
    ::-webkit-scrollbar-thumb { background: #1E293B; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #334155; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE DADOS ---
@st.cache_data(ttl=60)
def load_data(file_path):
    try:
        sheets = ['Dados', 'Equipes', 'Ligas', 'Radar Over', 'Modelo 01', 'Modelo 02', 'Prova Real', 'Bilhetes', 'Track Record']
        data_dict = {}
        with pd.ExcelFile(file_path) as xls:
            available_sheets = xls.sheet_names
            for s in sheets:
                if s in available_sheets:
                    data_dict[s] = pd.read_excel(xls, sheet_name=s)
        if 'Dados' in data_dict:
            df = data_dict['Dados']
            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            data_dict['Dados'] = df
        return data_dict
    except Exception as e:
        st.error(f"Erro no Excel: {e}")
        return None

EXCEL_PATH = "tabela_de_dados_apostas_V3.xlsx"
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
    code = country_map.get(normalize_text(country_name), country_name[:2].lower())
    return f"https://flagcdn.com/w40/{code}.png"

# --- LÓGICA DE CLASSIFICAÇÃO (V7.1) ---
def get_rating_info(ivc):
    if ivc >= 2.40: return "Classe A — Faixa Ouro", "rating-ouro", "🥇"
    if ivc >= 1.83: return "Classe B — Faixa Prata", "rating-prata", "🥈"
    return "Classe C — Faixa de Risco", "rating-risco", "🛑"

def calculate_ivc_soberano(row, df_dados):
    clube = row['Clube']
    liga = row['Liga']
    jogos = df_dados[((df_dados['Mandante'] == clube) | (df_dados['Visitante'] == clube)) & (df_dados['Liga'] == liga)].head(12)
    if len(jogos) == 0: return 0, 0, 0, 0
    media_geral = (jogos['Gols Mandante'].sum() + jogos['Gols Visitante'].sum()) / len(jogos)
    def normalize_outlier(gols, team_avg):
        if gols >= 6: return team_avg * 0.9
        return gols
    jogos_casa = jogos[jogos['Mandante'] == clube]
    if len(jogos_casa) > 0:
        outliers_casa = (jogos_casa['Gols Mandante'] >= 6).sum()
        gols_casa = jogos_casa['Gols Mandante'].apply(lambda x: normalize_outlier(x, media_geral)).mean() if outliers_casa == 1 else jogos_casa['Gols Mandante'].mean()
        gs_casa = jogos_casa['Gols Visitante'].mean()
    else: gols_casa, gs_casa = 0, 0
    jogos_fora = jogos[jogos['Visitante'] == clube]
    if len(jogos_fora) > 0:
        outliers_fora = (jogos_fora['Gols Visitante'] >= 6).sum()
        gols_fora = jogos_fora['Gols Visitante'].apply(lambda x: normalize_outlier(x, media_geral)).mean() if outliers_fora == 1 else jogos_fora['Gols Visitante'].mean()
        gs_fora = jogos_fora['Gols Mandante'].mean()
    else: gols_fora, gs_fora = 0, 0
    return media_geral, gols_casa * gs_casa, gols_fora * gs_fora, media_geral

def get_team_stats(team_name, df_dados, df_equipes):
    all_matches = df_dados[(df_dados['Mandante'] == team_name) | (df_dados['Visitante'] == team_name)].sort_values(by='Data', ascending=False)
    team_row = df_equipes[df_equipes['Equipe'] == team_name]
    pts_m, pts_v, zero_zero = 0, 0, 0
    gmc, gsc, gmv, gsv = 0, 0, 0, 0
    form = []
    for _, row in all_matches.iterrows():
        m, v = int(row['GM_M']), int(row['GM_V'])
        if m == 0 and v == 0: zero_zero += 1
        is_mandante = row['Mandante'] == team_name
        if is_mandante:
            gmc += m; gsc += v
            res = 'V' if m > v else ('E' if m == v else 'D')
            if len(form) < 5: form.append(res)
        else:
            gmv += v; gsv += m
            res = 'V' if v > m else ('E' if v == m else 'D')
            if len(form) < 5: form.append(res)
    stats = {'jogos': len(all_matches), 'gm': gmc + gmv, 'gs': gsc + gsv, 'zero_zero': zero_zero, 'form': form}
    if not team_row.empty:
        r = team_row.iloc[0].fillna(0)
        stats.update({'fam': r['FAM'], 'vdm': r['VDM'], 'fav': r['FAV'], 'vdv': r['VDV'], 'dispersao': r['Dispersão'] if r['Dispersão'] > 0 else 1.0})
    return stats

# --- INTERFACE PRINCIPAL ---
st.markdown(f"""
    <div class="main-header">
        <p class="title-main">Inteligência de Dados Pré-Live</p>
        <p class="subtitle-main">SGA V7.1 — Sniper Elite (Fato Soberano)</p>
    </div>
""", unsafe_allow_html=True)

cols_menu = st.columns([1,1,1,1,1,1])
with cols_menu[0]: 
    if st.button("📁 Principal", use_container_width=True): st.session_state.menu = 'Principal'
with cols_menu[1]:
    if st.button("⚖️ Confronto", use_container_width=True): st.session_state.menu = 'Confronto'
with cols_menu[2]:
    if st.button("🎯 Análise", use_container_width=True): st.session_state.menu = 'Análise'
with cols_menu[3]:
    if st.button("🏆 Ranking", use_container_width=True): st.session_state.menu = 'Ranking'
with cols_menu[4]:
    if st.button("🎫 Bilhetes", use_container_width=True): st.session_state.menu = 'Bilhetes'
with cols_menu[5]:
    if st.button("📊 Track Record", use_container_width=True): st.session_state.menu = 'Track Record'

st.divider()

if all_data:
    df_dados, df_equipes = all_data['Dados'], all_data['Equipes']

    if st.session_state.menu == 'Principal':
        st.subheader("🔥 Máquinas de Gols (Over)")
        df_equipes['IVC_Geral'], df_equipes['IVC_Casa'], df_equipes['IVC_Fora'], df_equipes['Média Geral'] = zip(*df_equipes.apply(lambda x: calculate_ivc_soberano(x, df_dados), axis=1))
        df_maquinas = df_equipes[df_equipes['TGM'] >= 25].sort_values(by='IVC_Geral', ascending=False).head(15)
        
        cols = st.columns(2)
        for idx, (i, row) in enumerate(df_maquinas.iterrows()):
            col = cols[idx % 2]
            rating_text, rating_class, emoji = get_rating_info(row['IVC_Geral'])
            with col:
                st.markdown(f"""
                <div class="card-container">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <span style="font-size: 1.2rem; font-weight: 800;">{idx+1}. {row['Clube']}</span><br>
                            <img src="{get_flag_img(row['País'])}" style="width:20px; vertical-align:middle;"> 
                            <span style="font-size: 0.8rem; color: #94A3B8;">{row['Liga']}</span>
                        </div>
                        <div style="text-align: right;">
                            <div class="ivc-box">IVC: {row['IVC_Geral']:.2f}</div>
                            <div class="ivc-box">CASA: {row['IVC_Casa']:.2f}</div>
                            <div class="ivc-box">FORA: {row['IVC_Fora']:.2f}</div>
                        </div>
                    </div>
                    <div class="rating-badge {rating_class}">{emoji} {rating_text}</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 10px;">
                        <div>
                            <p class="stat-label">Casa (Avg)</p>
                            <p><span class="stat-value stat-value-green">{"**" if row['FAM']>=3 else ""}{row['FAM']:.2f}{"**" if row['FAM']>=3 else ""}</span> 
                               <span style="color:#94A3B8; font-size:0.8rem;">M</span> | 
                               <span class="stat-value stat-value-red">{row['VDM']:.2f}</span> 
                               <span style="color:#94A3B8; font-size:0.8rem;">S</span></p>
                            <p class="stat-label" style="font-size:0.6rem;">Força de Ataque Casa: {row['FAM']/1.35:.2f}</p>
                        </div>
                        <div>
                            <p class="stat-label">Fora (Avg)</p>
                            <p><span class="stat-value stat-value-green">{"**" if row['FAV']>=3 else ""}{row['FAV']:.2f}{"**" if row['FAV']>=3 else ""}</span> 
                               <span style="color:#94A3B8; font-size:0.8rem;">M</span> | 
                               <span class="stat-value stat-value-red">{row['VDV']:.2f}</span> 
                               <span style="color:#94A3B8; font-size:0.8rem;">S</span></p>
                            <p class="stat-label" style="font-size:0.6rem;">Força de Ataque Fora: {row['FAV']/1.35:.2f}</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.info("""
        🛡️ **Doutrina de Classificação Soberana (V7.1)**
        1. **Força de Ataque**: Casa ≥ 1.40 | Fora ≥ 1.30 (em relação à média da liga).
        2. **Frequência**: Mínimo de 4 em 6 jogos cumprindo a meta (2+ em casa, 1+ fora).
        3. **Volume Mínimo**: A equipe deve ter marcado pelo menos 25 gols na janela analisada.
        4. **IVC (Índice de Volume Cruzado)**: Mede o cruzamento entre ataque e fragilidade defensiva.
           - 🥇 **Classe A (Ouro)**: IVC ≥ 2.40 | 🥈 **Classe B (Prata)**: IVC ≥ 1.83 | 🛑 **Classe C (Risco)**: IVC < 1.83.
        """)

    elif st.session_state.menu == 'Confronto':
        st.subheader("⚔️ Simulador de Confronto & Prova Real")
        clubes_list = sorted(df_equipes['Equipe'].unique().tolist())
        c1, c_vs, c2 = st.columns([2, 0.5, 2])
        with c1: mandante = st.selectbox("Mandante", ["Selecione..."] + clubes_list)
        with c_vs: st.markdown('<div style="font-size:2rem; text-align:center; padding-top:20px;">VS</div>', unsafe_allow_html=True)
        with c2: visitante = st.selectbox("Visitante", ["Selecione..."] + clubes_list)
        
        if mandante != "Selecione..." and visitante != "Selecione...":
            m, v = get_team_stats(mandante, df_dados, df_equipes), get_team_stats(visitante, df_dados, df_equipes)
            l_m, l_v = (m.get('fam', 0) + v.get('vdv', 0)) / 2, (v.get('fav', 0) + m.get('vdm', 0)) / 2
            l_total = l_m + l_v
            ge_real = l_total * np.sqrt((m.get('dispersao', 1) + v.get('dispersao', 1)) / 2)
            
            st.markdown(f"""
            <div class="card-container" style="text-align:center;">
                <p class="stat-label">GE Real (Fato Soberano)</p>
                <p style="font-size:3rem; font-weight:800; color:#38BDF8;">{ge_real:.2f}</p>
                <p class="stat-label">λ Mandante: {l_m:.2f} | λ Visitante: {l_v:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            p0x0 = (poisson.pmf(0, l_m) * poisson.pmf(0, l_v)) * 100
            st.metric("Risco de 0x0", f"{p0x0:.1f}%", delta="ALERTA" if p0x0 > 8 else "SEGURO", delta_color="inverse")

    elif st.session_state.menu == 'Análise':
        st.subheader("🎯 Análise — Montagem em Bloco")
        # Restauração simplificada do bloco para evitar NameError
        clubes_bloco = sorted(df_equipes['Equipe'].unique().tolist())
        with st.form("add_bloco"):
            b1, b2 = st.columns(2)
            with b1: m_b = st.selectbox("Mandante", ["Selecione..."] + clubes_bloco)
            with b2: v_b = st.selectbox("Visitante", ["Selecione..."] + clubes_bloco)
            if st.form_submit_button("Adicionar"):
                if m_b != "Selecione..." and v_b != "Selecione...":
                    st.session_state.block_matches.append({'mandante': m_b, 'visitante': v_b})
                    st.rerun()
        
        if st.session_state.block_matches:
            for idx, conf in enumerate(st.session_state.block_matches):
                st.write(f"{idx+1}. {conf['mandante']} x {conf['visitante']}")
            if st.button("Limpar"):
                st.session_state.block_matches = []
                st.rerun()

    elif st.session_state.menu == 'Ranking':
        st.subheader("🏆 Radar Over — Aderência")
        if 'Radar Over' in all_data:
            st.dataframe(all_data['Radar Over'].head(50), use_container_width=True)

    elif st.session_state.menu == 'Bilhetes':
        st.subheader("🎫 Bilhetes Processados")
        if 'Bilhetes' in all_data:
            st.dataframe(all_data['Bilhetes'], use_container_width=True)

    elif st.session_state.menu == 'Track Record':
        st.subheader("📊 Track Record — Histórico")
        if 'Track Record' in all_data:
            st.dataframe(all_data['Track Record'], use_container_width=True)
else:
    st.error("Erro ao carregar banco de dados V3.")
