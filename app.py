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
if 'menu' not in st.session_state: st.session_state.menu = 'Dados'
if 'selected_clube' not in st.session_state: st.session_state.selected_clube = ""
if 'home_view' not in st.session_state: st.session_state.home_view = 'Over'
if 'block_matches' not in st.session_state: st.session_state.block_matches = []
if 'block_notice' not in st.session_state: st.session_state.block_notice = ''
if 'block_results' not in st.session_state: st.session_state.block_results = []
if 'block_matches_file' not in st.session_state: st.session_state.block_matches_file = 'block_matches.json'

# Processamento de Parâmetros da URL (Links externos)
# Usamos query_params apenas se eles existirem e ainda não foram processados
q_params = st.query_params
if "time" in q_params:
    st.session_state.selected_clube = q_params["time"]
    st.session_state.menu = 'Dados'
    # Limpamos para permitir que o usuário use o menu depois
    st.query_params.clear()
elif "menu" in q_params:
    st.session_state.menu = q_params["menu"]
    st.session_state.selected_clube = ""
    st.query_params.clear()

# Estilização CSS Premium
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {
        --primary-navy: #1A365D;
        --accent-blue: #3182CE;
        --light-blue: #EBF8FF;
        --border-color: #E2E8F0;
        --text-main: #2D3748;
        --text-muted: #718096;
        --bg-main: #FFFFFF;
        --bg-soft: #F7FAFC;
    }

    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; 
        background-color: var(--bg-main); 
        color: var(--text-main); 
    }
    
    .stApp { background-color: var(--bg-main); }
    
    /* Header & Container */
    header { visibility: hidden; height: 0; }
    .block-container { padding-top: 0rem !important; padding-bottom: 1rem !important; max-width: 1200px !important; }
    .header-container { 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        padding: 15px 25px; 
        background: linear-gradient(135deg, #1A365D 0%, #2A4365 100%);
        border-radius: 0 0 16px 16px;
        margin-bottom: 25px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .title-main { font-size: 1.6rem; font-weight: 800; margin: 0; color: #FFFFFF; letter-spacing: -0.5px; }
    .subtitle-main { font-size: 0.85rem; color: #A0AEC0; margin: 0; font-weight: 400; }
    
    /* Navigation Buttons */
    .stButton > button {
        border-radius: 10px !important;
        border: 1px solid var(--border-color) !important;
        background-color: white !important;
        color: var(--text-main) !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        height: 42px !important;
    }
    .stButton > button:hover {
        border-color: var(--accent-blue) !important;
        color: var(--accent-blue) !important;
        background-color: var(--light-blue) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Cards & Links */
    .card-link { 
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        text-decoration: none !important; 
        color: inherit !important; 
        background-color: white; 
        border: 1px solid var(--border-color); 
        border-radius: 14px; 
        padding: 18px; 
        margin-bottom: 15px; 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        height: 140px; /* Altura fixa para alinhamento perfeito */
    }
    .card-link:hover { 
        border-color: var(--accent-blue); 
        box-shadow: 0 10px 20px rgba(49, 130, 206, 0.12); 
        transform: translateY(-4px); 
    }
    
    /* Info Panels */
    .info-card { 
        background: linear-gradient(to bottom right, #FFFFFF, #F8FAFC);
        border: 1px solid var(--border-color); 
        border-radius: 16px; 
        padding: 25px; 
        margin-bottom: 30px; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .team-name { font-size: 1.5rem; font-weight: 800; color: var(--primary-navy); margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }
    
    /* Metrics & Stats */
    .stat-box { display: flex; flex-direction: column; align-items: flex-start; padding: 10px 15px; background: white; border-radius: 10px; border: 1px solid #EDF2F7; min-width: 100px; }
    .stat-v { font-weight: 800; color: var(--accent-blue); font-size: 1.5rem; line-height: 1; }
    .stat-l { color: var(--text-muted); font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 5px; }

    /* Pills & Badges */
    .form-pill { padding: 4px 8px; border-radius: 6px; font-size: 0.7rem; font-weight: 800; margin-right: 4px; color: white; min-width: 22px; text-align: center; display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .pill-v { background: linear-gradient(135deg, #48BB78 0%, #38A169 100%); }
    .pill-e { background: linear-gradient(135deg, #ED8936 0%, #DD6B20 100%); }
    .pill-d { background: linear-gradient(135deg, #F56565 0%, #E53E3E 100%); }
    
    /* Titles & Sections */
    .box-title { 
        font-size: 0.9rem; 
        font-weight: 800; 
        color: var(--primary-navy); 
        margin-bottom: 20px; 
        text-transform: uppercase; 
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .box-title::before { content: ""; display: block; width: 4px; height: 18px; background: var(--accent-blue); border-radius: 2px; }
    
    .details-box { background-color: white; border: 1px solid var(--border-color); border-radius: 14px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .total-gm { color: #38A169; font-weight: 700; }
    .total-gs { color: #E53E3E; font-weight: 700; }
    .side-stat-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #F1F5F9; font-size: 0.9rem; font-weight: 500; }
    .side-stat-row:last-child { border-bottom: none; }
    
    .sim-header { 
        background: var(--light-blue); 
        padding: 20px 25px; 
        border-radius: 14px; 
        border-left: 6px solid var(--accent-blue); 
        margin-bottom: 30px;
        box-shadow: 0 4px 6px -1px rgba(49, 130, 206, 0.05);
    }
    .summary-box {
        background: #F0F9FF;
        border-left: 5px solid #0F5FA8;
        padding: 25px;
        border-radius: 12px;
        margin-bottom: 40px; /* Margem maior para empurrar os cards */
        position: relative;
        display: block;
        width: 100%;
        clear: both;
    }
    
    /* File Uploader Custom */
    [data-testid="stFileUploader"] { padding: 0; margin: 0; }
    [data-testid="stFileUploader"] section { 
        padding: 0 !important; 
        border: 1px solid var(--border-color) !important; 
        background-color: white !important; 
        height: 42px !important; 
        min-height: 42px !important; 
        border-radius: 10px !important; 
        display: flex; 
        align-items: center; 
        justify-content: center;
        transition: all 0.2s;
    }
    [data-testid="stFileUploader"] section:hover { border-color: var(--accent-blue) !important; background-color: var(--light-blue) !important; }
    [data-testid="stFileUploader"] section > div { display: none !important; }
    [data-testid="stFileUploader"] button { 
        height: 38px !important; 
        margin: 0 !important; 
        border: none !important; 
        background: transparent !important; 
        color: var(--primary-navy) !important; 
        font-weight: 700 !important; 
        font-size: 0.75rem !important; 
        width: 100% !important;
        text-transform: uppercase;
    }
    [data-testid="stFileUploader"] button::before { content: '📊 '; margin-right: 5px; }

    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #F7FAFC; }
    ::-webkit-scrollbar-thumb { background: #CBD5E0; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #A0AEC0; }
    </style>
    """, unsafe_allow_html=True)

# Carregamento de Dados com Cache para Performance (Versão 7.1.3)
@st.cache_data(ttl=30) # Cache expira em 30 segundos para garantir sincronia total
def load_data(file_content, force_reload=False):
    try:
        # file_content pode ser um path (string) ou BytesIO (upload)
        data_dict = pd.read_excel(file_content, sheet_name=None)
        if 'Dados' in data_dict:
            df_dados = data_dict['Dados']
            df_dados['Data'] = pd.to_datetime(df_dados['Data'], dayfirst=True, errors='coerce')
            df_dados['Pais_Liga'] = df_dados['País'].astype(str) + " - " + df_dados['Liga'].astype(str)
        return data_dict
    except Exception as e:
        st.error(f"Erro ao carregar Excel: {e}")
        return None

EXCEL_PATH = "tabela_de_dados_apostas_V3.xlsx"

# Lógica de prioridade: Upload > Arquivo Local
uploaded_file = st.session_state.get('uploaded_file', None)
if uploaded_file:
    # Usamos o tamanho do arquivo como chave para forçar recarregamento
    all_data = load_data(uploaded_file, force_reload=str(uploaded_file.size))
else:
    # Para o arquivo local, usamos a data de modificação
    import os
    try:
        mtime = os.path.getmtime(EXCEL_PATH)
    except:
        mtime = "default"
    all_data = load_data(EXCEL_PATH, force_reload=str(mtime))

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

LOGO_B64 = get_base64_image("logo_final.png") if os.path.exists("logo_final.png") else ""

def normalize_text(text):
    if not isinstance(text, str): return ""
    # Normalização ultra-robusta: remove acentos, espaços extras e converte para minúsculas
    text = text.strip().lower()
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def get_hybrid_name(name):
    norm = normalize_text(name)
    if norm == name.lower():
        return name
    return f"{name} [{norm.upper()}]"

def format_avg_html(val, color):
    weight = "800" if val >= 3.0 else "400"
    return f'<span style="color:{color}; font-weight:{weight};">{val:.2f}</span>'

def get_flag_img(pais_liga):
    if not isinstance(pais_liga, str): return ""
    p = pais_liga.split('-')[0].strip().upper()
    # Mapeamento para códigos ISO de 2 letras para usar com flagcdn.com
    iso_map = {
        'BRA': 'br', 'USA': 'us', 'FIN': 'fi', 'NOR': 'no', 'ISL': 'is', 
        'BOL': 'bo', 'ARG': 'ar', 'CHI': 'cl', 'COL': 'co', 'PAR': 'py', 
        'URU': 'uy', 'VEN': 've', 'MEX': 'mx', 'GER': 'de', 'ENG': 'gb-eng', 
        'SPA': 'es', 'ESP': 'es', 'ITA': 'it', 'FRA': 'fr', 'POR': 'pt', 
        'HOL': 'nl', 'NED': 'nl', 'BEL': 'be', 'SWE': 'se', 'DEN': 'dk', 
        'AUT': 'at', 'SWI': 'ch', 'SUI': 'ch', 'JPN': 'jp', 'KOR': 'kr',
        'AUS': 'au', 'CAN': 'ca', 'TUR': 'tr', 'GRE': 'gr', 'RUS': 'ru', 'CHN': 'cn',
        'UKR': 'ua', 'SCO': 'gb-sct', 'WAL': 'gb-wls', 'IRL': 'ie', 'NIR': 'gb-nir'
    }
    code = iso_map.get(p, "un")
    return f'<img src="https://flagcdn.com/w40/{code}.png" style="width:18px; height:auto; margin-right:8px; vertical-align:middle; border-radius:2px; box-shadow:0 1px 2px rgba(0,0,0,0.1);">'

def get_team_stats(team_name, df_dados, df_equipes):
    t_clean = str(team_name).strip().lower()
    # Busca robusta em Dados
    mask_m = df_dados['Mandante'].astype(str).str.strip().str.lower() == t_clean
    mask_v = df_dados['Visitante'].astype(str).str.strip().str.lower() == t_clean
    all_matches = df_dados[mask_m | mask_v].sort_values(by='Data', ascending=False)
    
    # Busca robusta em Equipes
    team_row = df_equipes[df_equipes['Equipe'].astype(str).str.strip().str.lower() == t_clean]
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
            if res == 'V': pts_m += 3
            elif res == 'E': pts_m += 1
        else:
            gmv += v; gsv += m
            res = 'V' if v > m else ('E' if v == m else 'D')
            if len(form) < 5: form.append(res)
            if res == 'V': pts_v += 3
            elif res == 'E': pts_v += 1
    stats = {
        'jogos': len(all_matches), 'gm': gmc + gmv, 'gs': gsc + gsv, 'pts_m': pts_m, 'pts_v': pts_v, 'zero_zero': zero_zero,
        'gmc': gmc, 'gsc': gsc, 'gmv': gmv, 'gsv': gsv, 'saldo_m': gmc - gsc, 'saldo_v': gmv - gsv, 'form': form, 
        'liga': all_matches.iloc[0]['Liga'] if not all_matches.empty else "N/A",
        'pais': all_matches.iloc[0]['País'] if not all_matches.empty else "N/A"
    }
    if not team_row.empty:
        r = team_row.iloc[0].fillna(0)
        # Dispersão deve ser no mínimo 1 se for 0 ou NaN para não zerar o GE Real
        disp = r['Dispersão'] if r['Dispersão'] > 0 else 1.0
        stats.update({
            'fam': r['FAM'], 'vdm': r['VDM'], 'fav': r['FAV'], 'vdv': r['VDV'], 
            'ipm': r['IPM'], 'ipv': r['IPV'], 'tjm': r['TJM'], 'tjv': r['TJV'], 
            'modelo': r['Modelo Estatístico'], 'dispersao': disp
        })
    return stats

def calculate_confronto_probs(ge_total):
    base_lines = [0.5, 1.5, 2.5, 3.5]
    base_probs = {line: 1 - poisson.cdf(int(line), ge_total) for line in base_lines}
    final_probs = {}
    s1 = (base_probs[0.5] - base_probs[1.5]) / 4
    final_probs[0.5], final_probs[0.75], final_probs[1.0], final_probs[1.25], final_probs[1.5] = base_probs[0.5], base_probs[0.5]-s1, base_probs[0.5]-2*s1, base_probs[0.5]-3*s1, base_probs[1.5]
    s2 = (base_probs[1.5] - base_probs[2.5]) / 4
    final_probs[1.75], final_probs[2.0], final_probs[2.25], final_probs[2.5] = base_probs[1.5]-s2, base_probs[1.5]-2*s2, base_probs[1.5]-3*s2, base_probs[2.5]
    s3 = (base_probs[2.5] - base_probs[3.5]) / 4
    final_probs[2.75], final_probs[3.0] = base_probs[2.5]-s3, base_probs[2.5]-2*s3
    return final_probs

def get_probable_scores(lambda_m, lambda_v):
    scores = []
    for m in range(5):
        for v in range(5):
            prob = poisson.pmf(m, lambda_m) * poisson.pmf(v, lambda_v)
            scores.append({'placar': f"{m} x {v}", 'prob': prob})
    return sorted(scores, key=lambda x: x['prob'], reverse=True)[:8]

if all_data:
    df_dados, df_equipes = all_data['Dados'], all_data['Equipes']

    # --- HEADER PREMIUM ---
    st.markdown(f"""
        <div class="header-container">
            <div style="display:flex; align-items:center; gap:20px;">
                <a href="/?menu=Dados" target="_self" class="logo-link">
                    <div style="background: rgba(255,255,255,0.1); padding: 8px; border-radius: 12px; backdrop-filter: blur(4px);">
                        <img src="data:image/png;base64,{LOGO_B64}" style="width:50px; height:50px; object-fit:contain;">
                    </div>
                </a>
                <div>
                    <p class="title-main">SGA V7.1 — Sniper Elite</p>
                    <p class="subtitle-main">Inteligência de Dados Pré-Live</p>
                </div>
            </div>
            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 2px;">
                <span style="color: #63B3ED; font-weight: 800; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px;">Status do Sistema</span>
                <span style="color: #FFFFFF; font-weight: 600; font-size: 0.8rem; display: flex; align-items: center; gap: 5px;">
                    <span style="width: 8px; height: 8px; background: #48BB78; border-radius: 50%; box-shadow: 0 0 8px #48BB78;"></span>
                    Operacional Online
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # NAVEGAÇÃO DO MENU (Ajuste de largura para incluir Ranking)
    m_cols = st.columns([2.5, 1.2, 1.2, 1.2, 1.2, 1.2, 1.5])
    with m_cols[1]:
        if st.button("📁 Dados", use_container_width=True):
            st.session_state.menu = 'Dados'
            st.session_state.selected_clube = ""
            st.rerun()
    with m_cols[2]:
        if st.button("⚔️ Confronto", use_container_width=True):
            st.session_state.menu = 'Modelo 01'
            st.rerun()
    with m_cols[3]:
        if st.button("🚀 Análise", use_container_width=True):
            st.session_state.menu = 'Análise'
            st.session_state.selected_clube = ''
            st.rerun()
    with m_cols[4]:
        if st.button("📊 Ranking", use_container_width=True):
            st.session_state.menu = 'Ranking'
            st.session_state.selected_clube = ''
            st.rerun()
    with m_cols[5]:
        if st.button("📋 Bilhetes", use_container_width=True):
            st.session_state.menu = 'Bilhetes'
            st.rerun()
    with m_cols[6]:
        if st.button("📈 Track Record", use_container_width=True):
            st.session_state.menu = 'Track Record'
            st.session_state.selected_clube = ''
            st.rerun()

    # --- TELAS ---
    if st.session_state.menu == 'Dados':
        if st.session_state.selected_clube:
            st.markdown(f'<a href="/?menu=Dados" target="_self" style="color:#00A3E0; text-decoration:none; font-size:0.85rem; font-weight:600;">⬅ Voltar para o Dashboard Inicial</a>', unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)
            
            stats = get_team_stats(st.session_state.selected_clube, df_dados, df_equipes)
            matches_12 = df_dados[(df_dados['Mandante'] == st.session_state.selected_clube) | (df_dados['Visitante'] == st.session_state.selected_clube)].sort_values(by='Data', ascending=False).head(12)
            form_html = "".join([f'<span class="form-pill pill-{r.lower()}">{r}</span>' for r in stats['form']])
            
            st.markdown(f"""
                <div class="info-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div class="team-name">🛡️ {st.session_state.selected_clube}</div>
                        <div>{form_html}</div>
                    </div>
                    <div class="stats-grid">
                        <div class="stat-box"><span class="stat-v">{stats['jogos']}</span><span class="stat-l">Jogos</span></div>
                        <div class="stat-box"><span class="stat-v">{stats['gm']}</span><span class="stat-l">Gols Pró</span></div>
                        <div class="stat-box"><span class="stat-v">{stats['gs']}</span><span class="stat-l">Gols Contra</span></div>
                        <div class="stat-box"><span class="stat-v">{stats['zero_zero']}</span><span class="stat-l">0x0</span></div>
                        <div class="stat-box"><span class="stat-v">{stats['pts_m']}</span><span class="stat-l">Pts Casa</span></div>
                        <div class="stat-box"><span class="stat-v">{stats['pts_v']}</span><span class="stat-l">Pts Fora</span></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            c_l, c_r = st.columns([2, 1])
            with c_l:
                st.markdown('<div class="box-title">📅 Últimos 12 Confrontos</div>', unsafe_allow_html=True)
                table_rows = "".join([f"<tr><td>{row['Data'].strftime('%d/%m/%y') if pd.notnull(row['Data']) else '--/--/--'}</td><td style='color:#A0AEC0;'>{row['Liga']}</td><td>{row['Mandante']}</td><td style='font-weight:700; text-align:center;'>{int(row['GM_M'])} – {int(row['GM_V'])}</td><td>{row['Visitante']}</td></tr>" for _, row in matches_12.iterrows()])
                components.html(f"<style>table {{ width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif; }} th {{ text-align: left; padding: 10px; color: #718096; font-size: 10px; text-transform: uppercase; border-bottom: 2px solid #EDF2F7; }} td {{ padding: 12px 10px; border-bottom: 1px solid #EDF2F7; font-size: 13px; color: #2D3748; }}</style><table><thead><tr><th>DATA</th><th>LIGA</th><th>MANDANTE</th><th>PLACAR</th><th>VISITANTE</th></tr></thead><tbody>{table_rows}</tbody></table>", height=500, scrolling=True)
            with c_r:
                st.markdown('<div class="box-title">📊 Desempenho por Lado</div>', unsafe_allow_html=True)
                st.markdown(f"""<div class="details-box"><div class="side-stat-row"><span>Gols Marcados (Casa)</span><span>{stats['gmc']}</span></div><div class="side-stat-row"><span>Gols Sofridos (Casa)</span><span>{stats['gsc']}</span></div><div class="side-stat-row" style="background:#F3F4F6; font-weight:700;"><span>Saldo (Casa)</span><span>{stats['saldo_m']}</span></div><div style="margin-top:20px;"></div><div class="side-stat-row"><span>Gols Marcados (Fora)</span><span>{stats['gmv']}</span></div><div class="side-stat-row"><span>Gols Sofridos (Fora)</span><span>{stats['gsv']}</span></div><div class="side-stat-row" style="background:#F3F4F6; font-weight:700;"><span>Saldo (Fora)</span><span>{stats['saldo_v']}</span></div></div>""", unsafe_allow_html=True)
        else:
            # HOME
            st.markdown(f"""<div class="summary-bar"><div>Resultados de partidas · Janela Móvel de 12 jogos</div><div>{len(df_dados)} registros · {len(df_equipes)} clubes</div></div>""", unsafe_allow_html=True)
            col_search, col_liga, col_btns = st.columns([1.5, 1, 1])
            with col_search:
                clubes_list_raw = sorted(df_equipes['Equipe'].dropna().unique().tolist())
                hybrid_clubes = {get_hybrid_name(c): c for c in clubes_list_raw}
                sel_clube_hybrid = st.selectbox("Buscar clube...", ["🔍 Selecione ou digite o nome do clube..."] + list(hybrid_clubes.keys()), key="search_results", label_visibility="collapsed")
                if sel_clube_hybrid != "🔍 Selecione ou digite o nome do clube...":
                    st.session_state.selected_clube = hybrid_clubes[sel_clube_hybrid]
                    st.rerun()
            with col_liga:
                liga_list = ["Todas as Ligas"] + sorted(df_dados['Pais_Liga'].unique().tolist())
                sel_liga = st.selectbox("Filtrar por Liga", liga_list, label_visibility="collapsed")
            with col_btns:
                # Botão de Upload Discreto (Excel)
                new_file = st.file_uploader("EXCEL", type=["xlsx"], label_visibility="collapsed", key="excel_uploader")
                if new_file:
                    st.session_state.uploaded_file = new_file
                    st.rerun()
            
            if sel_liga != "Todas as Ligas":
                st.info(f"Exibindo partidas de: **{sel_liga}**")
                st.dataframe(df_dados[df_dados['Pais_Liga'] == sel_liga].sort_values(by='Data', ascending=False), use_container_width=True)
            else:
                h_col1, h_col2, h_col3 = st.columns([1, 1, 1])
                with h_col1:
                    if st.button("⚡ Máquinas de Gols", use_container_width=True):
                        st.session_state.home_view = 'Over'
                        st.rerun()
                with h_col2:
                    if st.button("🔥 Top 15 Ataques", use_container_width=True):
                        st.session_state.home_view = 'Ataque'
                        st.rerun()
                with h_col3:
                    if st.button("❄️ Bottom 15 Defesas", use_container_width=True):
                        st.session_state.home_view = 'Defesa'
                        st.rerun()
                
                # Filtro Global de Ligas (Excluir MLS-Cross dos Rankings de Elite)
                equipes_mls = df_dados[df_dados['Liga'] == 'MLS-Cross']['Mandante'].unique().tolist() + df_dados[df_dados['Liga'] == 'MLS-Cross']['Visitante'].unique().tolist()
                df_elite_home = df_equipes[~df_equipes['Equipe'].isin(equipes_mls)].copy()

                if st.session_state.home_view == 'Over':
                    st.markdown('<div class="box-title">⚡ Máquinas de Gols (Elite: GM Casa/Fora ≥ 1.8 & GS ≥ 1.5)</div>', unsafe_allow_html=True)
                    # Calcular médias
                    df_elite_home['Avg_GM'] = df_elite_home['TGM'] / df_elite_home['TJT'].replace(0, 1)
                    df_elite_home['Avg_GS'] = df_elite_home['TGS'] / df_elite_home['TJT'].replace(0, 1)
                    df_elite_home['Avg_GM_C'] = df_elite_home['GMC'] / df_elite_home['TJM'].replace(0, 1)
                    df_elite_home['Avg_GM_V'] = df_elite_home['GMV'] / df_elite_home['TJV'].replace(0, 1)
                    
                    # Filtro de Amostra Consolidada: Mínimo de 25 gols marcados E 25 sofridos
                    df_filtered = df_elite_home[(df_elite_home['TGM'] >= 25) & (df_elite_home['TGS'] >= 25)]
                    
                    # Filtro Rígido de Médias: 1.8 em CASA E 1.8 FORA
                    df_filtered = df_filtered[(df_filtered['Avg_GM_C'] >= 1.8) & (df_filtered['Avg_GM_V'] >= 1.8) & (df_filtered['Avg_GS'] >= 1.5)]
                    
                    # Índice de Máquina: Produto das Médias (Avg_GM * Avg_GS)
                    df_filtered['IM'] = df_filtered['Avg_GM'] * df_filtered['Avg_GS']
                    top_data = df_filtered.sort_values(by='IM', ascending=False).head(15)
                elif st.session_state.home_view == 'Ataque':
                    st.markdown('<div class="box-title">🔥 Top 15 Clubes Marcadores (Ataque de Elite)</div>', unsafe_allow_html=True)
                    top_data = df_elite_home.sort_values(by='TGM', ascending=False).head(15)
                else:
                    st.markdown('<div class="box-title">❄️ Bottom 15 Defesas (Defesas Horríveis)</div>', unsafe_allow_html=True)
                    top_data = df_elite_home.sort_values(by='TGS', ascending=False).head(15)
                
                top_list = top_data.to_dict('records')
                cols = st.columns(3)
                for i in range(3):
                    with cols[i]:
                        for j in range(5):
                            idx = i * 5 + j
                            if idx < len(top_list):
                                team = top_list[idx]
                                t_stats = get_team_stats(team['Equipe'], df_dados, df_equipes)
                                form_html = "".join([f'<span class="form-pill pill-{r.lower()}">{r}</span>' for r in t_stats['form']])
                                # Calcular médias por lado
                                avg_gmc = t_stats['gmc'] / t_stats['tjm'] if t_stats['tjm'] > 0 else 0
                                avg_gsc = t_stats['gsc'] / t_stats['tjm'] if t_stats['tjm'] > 0 else 0
                                avg_gmv = t_stats['gmv'] / t_stats['tjv'] if t_stats['tjv'] > 0 else 0
                                avg_gsv = t_stats['gsv'] / t_stats['tjv'] if t_stats['tjv'] > 0 else 0
                                
                                st.markdown(f"""
                                    <a href="/?time={team['Equipe']}" target="_self" class="card-link">
                                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:5px;">
                                            <span style="font-weight:700; font-size:0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 160px;" title="{team['Equipe']}">{idx+1}. {team['Equipe']}</span>
                                            <div>{form_html}</div>
                                        </div>
                                        <div style="font-size:0.7rem; color:#718096; margin-bottom:8px; display:flex; align-items:center; gap:5px;">{t_stats['pais']} - {t_stats['liga']} {get_flag_img(f"{t_stats['pais']} - {t_stats['liga']}")}</div>
                                        <div style="display:flex; flex-direction:column; gap:4px; font-size:0.75rem;">
                                            <div style="display:flex; justify-content:space-between;">
                                                <div><span style="color:#718096;">Casa (Avg):</span> {format_avg_html(avg_gmc, "#38A169")} / {format_avg_html(avg_gsc, "#E53E3E")}</div>
                                                <span class="total-gm">{int(team['TGM'])}M</span>
                                            </div>
                                            <div style="display:flex; justify-content:space-between;">
                                                <div><span style="color:#718096;">Fora (Avg):</span> {format_avg_html(avg_gmv, "#38A169")} / {format_avg_html(avg_gsv, "#E53E3E")}</div>
                                                <span class="total-gs">{int(team['TGS'])}S</span>
                                            </div>
                                        </div>
                                    </a>
                                """, unsafe_allow_html=True)

    elif st.session_state.menu == 'Modelo 01':
        st.markdown(f"""<div class="sim-header"><h3 style="margin:0; color:#2C5282;">⚔️ Simulador de Confronto & Prova Real</h3><p style="margin:0; color:#4A5568; font-size:0.9rem;">Diagnóstico Robusto: Cruzamento Técnico (Confronto) + Validação Empírica (Prova Real)</p></div>""", unsafe_allow_html=True)
        clubes_list_raw = sorted(df_equipes['Equipe'].unique().tolist())
        
        # Filtro de busca por texto para facilitar a seleção
        search_sim = st.text_input("🔍 Filtrar Equipes (ex: Brage ou Orebro)", key="search_sim_input", help="Digite parte do nome para filtrar as listas abaixo.")
        norm_search_sim = normalize_text(search_sim)
        clubes_list = [c for c in clubes_list_raw if norm_search_sim in normalize_text(c)]

        col_s1, col_vs, col_s2 = st.columns([2, 0.5, 2])
        with col_s1: mandante = st.selectbox("Mandante", ["Selecione..."] + clubes_list, key="m_sim")
        with col_vs: st.markdown('<div style="font-size:1.5rem; font-weight:800; color:#CBD5E0; height:80px; display:flex; align-items:center; justify-content:center;">VS</div>', unsafe_allow_html=True)
        with col_s2: visitante = st.selectbox("Visitante", ["Selecione..."] + clubes_list, key="v_sim")
        
        if mandante != "Selecione..." and visitante != "Selecione...":
            m, v = get_team_stats(mandante, df_dados, df_equipes), get_team_stats(visitante, df_dados, df_equipes)
            l_m, l_v = (m.get('fam', 0) + v.get('vdv', 0)) / 2, (v.get('fav', 0) + m.get('vdm', 0)) / 2
            l_total = l_m + l_v
            ge_real = l_total * np.sqrt((m.get('dispersao', 1) + v.get('dispersao', 1)) / 2)
            
            st.markdown("---")
            # CÁLCULOS PRÉVIOS
            m_casa = df_dados[df_dados['Mandante'] == mandante].sort_values('Data', ascending=False).head(12)
            v_fora = df_dados[df_dados['Visitante'] == visitante].sort_values('Data', ascending=False).head(12)
            
            def calc_pr_metrics(df, team, is_m):
                if df.empty: return {"gm":0, "gs":0, "zero":0, "over15":0, "over25":0, "over35":0, "btts":0, "total":0}
                total = len(df)
                gm = df['GM_M'].mean() if is_m else df['GM_V'].mean()
                gs = df['GM_V'].mean() if is_m else df['GM_M'].mean()
                zero = (len(df[(df['GM_M'] == 0) & (df['GM_V'] == 0)]) / total) * 100
                over15 = (len(df[(df['GM_M'] + df['GM_V']) >= 2]) / total) * 100
                over25 = (len(df[(df['GM_M'] + df['GM_V']) >= 3]) / total) * 100
                over35 = (len(df[(df['GM_M'] + df['GM_V']) >= 4]) / total) * 100
                btts = (len(df[(df['GM_M'] > 0) & (df['GM_V'] > 0)]) / total) * 100
                return {"gm":gm, "gs":gs, "zero":zero, "over15":over15, "over25":over25, "over35":over35, "btts":btts, "total": total}

            m_pr = calc_pr_metrics(m_casa, mandante, True)
            v_pr = calc_pr_metrics(v_fora, visitante, False)
            
            # --- PRIMEIRA LINHA (TRINDADE DE DECISÃO) ---
            t_col1, t_col2, t_col3 = st.columns(3)
            
            with t_col1:
                st.markdown('<div class="box-title">📊 Parâmetros do Modelo (λ Cruzado)</div>', unsafe_allow_html=True)
                st.markdown(f"""<div class="details-box">
                    <div class="side-stat-row"><span>Gols esperados (λ)</span><span style="font-weight:700;">{l_m:.3f} | {l_v:.3f}</span></div>
                    <div class="side-stat-row"><span>Índice de força</span><span>{m.get('ipm',0):.2f} | {v.get('ipv',0):.2f}</span></div>
                    <div class="side-stat-row" style="font-weight:700; font-size:1rem; border-top:2px solid #EBF8FF; margin-top:10px; padding-top:10px;"><span>λ TOTAL</span><span style="color:#00A3E0;">{l_total:.4f}</span></div>
                    <div class="side-stat-row" style="background:#EBF8FF; color:#2C5282; font-weight:700; padding:10px; border-radius:6px; margin-top:10px;"><span>GE REAL (FATO)</span><span>{ge_real:.2f}</span></div>
                </div>""", unsafe_allow_html=True)
                
            with t_col2:
                st.markdown('<div class="box-title">📊 Prova Real — Tabela 2: Distribuição</div>', unsafe_allow_html=True)
                hist_over15 = (m_pr['over15'] + v_pr['over15']) / 2
                hist_over25 = (m_pr['over25'] + v_pr['over25']) / 2
                hist_over35 = (m_pr['over35'] + v_pr['over35']) / 2
                hist_btts = (m_pr['btts'] + v_pr['btts']) / 2
                def get_leitura(val):
                    if val >= 75: return f'<span style="color:#48BB78; font-weight:700;">GREEN ≥75%</span>'
                    if val >= 60: return f'<span style="color:#ED8936; font-weight:700;">PROTEÇÃO ≥60%</span>'
                    return f'<span style="color:#F56565; font-weight:700;">ALERTA <60%</span>'
                st.markdown(f"""<div class="details-box">
                    <div class="side-stat-row"><span>Over 0.5</span><span>{'<span style="color:#48BB78; font-weight:700;">CONFIRMADO</span>' if (100 - (m_pr['zero']+v_pr['zero'])/2) >= 85 else '<span style="color:#F56565; font-weight:700;">RISCO 0x0</span>'}</span></div>
                    <div class="side-stat-row"><span>Over 1.5</span><span>{get_leitura(hist_over15)}</span></div>
                    <div class="side-stat-row"><span>Over 2.5</span><span>{get_leitura(hist_over25)}</span></div>
                    <div class="side-stat-row"><span>Over 3.5</span><span>{get_leitura(hist_over35)}</span></div>
                    <div class="side-stat-row"><span>BTTS</span><span>{get_leitura(hist_btts)}</span></div>
                </div>""", unsafe_allow_html=True)
                
            with t_col3:
                st.markdown('<div class="box-title">🏁 Prova Real — Tabela 3: Conclusão</div>', unsafe_allow_html=True)
                p0x0_real_calc = (poisson.pmf(0, l_m) * poisson.pmf(0, l_v)) * 100
                avg_id = (m.get('dispersao', 1) + v.get('dispersao', 1)) / 2
                p0x0_stress = p0x0_real_calc * avg_id
                avg_zero_historico = (m_pr['zero'] + v_pr['zero']) / 2
                is_veto = p0x0_stress > 10 or avg_zero_historico > 8
                veto = "⚠️ ALERTA DE VETO (0x0)" if is_veto else "✅ SEM VETO POR 0x0"
                st.markdown(f"""<div class="details-box">
                    <div style="padding:15px; background:#F7FAFC; border-radius:8px; border-left:5px solid {'#F56565' if is_veto else '#48BB78'};">
                        <span style="font-weight:700; font-size:0.9rem;">{veto}</span><br/>
                        <span style="font-size:0.8rem; color:#718096;">Prob. Real: {p0x0_real_calc:.1f}% | Estresse (ID): {p0x0_stress:.1f}%</span>
                    </div>
                    <div style="margin-top:15px; padding:10px; background:#EBF8FF; border-radius:8px;">
                        <span style="font-size:0.75rem; font-weight:700; color:#2C5282;">REGRA OPERACIONAL:</span><br/>
                        <span style="font-size:0.85rem; font-weight:600;">{'🚀 ENTRADA CONFIRMADA EM OVER' if ge_real > 1.8 and not is_veto else '🛡️ RECOMENDADO CAUTELA / UNDER'}</span>
                    </div>
                </div>""", unsafe_allow_html=True)

            # --- SEGUNDA LINHA (DETALHAMENTO SUPORTE) ---
            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
            d_col1, d_col2, d_col3 = st.columns(3)
            
            with d_col1:
                st.markdown('<div class="box-title">📈 Linhas Asiáticas (Prob. Ajustada)</div>', unsafe_allow_html=True)
                probs = calculate_confronto_probs(l_total)
                rows = "".join([f"<div class='side-stat-row'><span>Linha <b>{line}</b></span><span style='font-weight:700; color:#00A3E0;'>{prob*100:.1f}%</span></div>" for line, prob in probs.items()])
                st.markdown(f"<div class='details-box'>{rows}</div>", unsafe_allow_html=True)
                
            with d_col2:
                st.markdown('<div class="box-title">🏆 Placares Mais Prováveis</div>', unsafe_allow_html=True)
                scores = get_probable_scores(l_m, l_v)
                rows = "".join([f"<div class='side-stat-row'><span>{s['placar']}</span><span style='font-weight:700;'>{s['prob']*100:.1f}%</span></div>" for s in scores])
                st.markdown(f"<div class='details-box'>{rows}</div>", unsafe_allow_html=True)
                
            with d_col3:
                st.markdown('<div class="box-title">🛡️ Prova Real — Tabela 1: Condição</div>', unsafe_allow_html=True)
                st.markdown(f"""<div class="details-box">
                    <div class="side-stat-row" style="background:#EDF2F7; font-weight:700;"><span>Métrica</span><span>Mandante | Visitante</span></div>
                    <div class="side-stat-row"><span>Jogos na condição</span><span>{m_pr['total']} | {v_pr['total']}</span></div>
                    <div class="side-stat-row"><span>Gols marcados / jogo</span><span>{m_pr['gm']:.2f} | {v_pr['gm']:.2f}</span></div>
                    <div class="side-stat-row"><span>Gols sofridos / jogo</span><span>{m_pr['gs']:.2f} | {v_pr['gs']:.2f}</span></div>
                    <div class="side-stat-row"><span>0 x 0 (Real)</span><span>{m_pr['zero']:.1f}% | {v_pr['zero']:.1f}%</span></div>
                    <div class="side-stat-row"><span>2+ Gols (Over 1.5)</span><span style="color:#00A3E0; font-weight:700;">{m_pr['over15']:.1f}% | {v_pr['over15']:.1f}%</span></div>
                    <div class="side-stat-row"><span>BTTS (Ambas Marcam)</span><span>{m_pr['btts']:.1f}% | {v_pr['btts']:.1f}%</span></div>
                </div>""", unsafe_allow_html=True)

    elif st.session_state.menu == 'Análise':
        st.markdown('''<div class="sim-header"><h3 style="margin:0; color:#2C5282;">🚀 Análise — Montagem em Bloco</h3><p style="margin:0; color:#4A5568; font-size:0.9rem;">Selecione vários confrontos e classifique os melhores para análise de gols e linhas asiáticas.</p></div>''', unsafe_allow_html=True)
        clubes_bloco_raw = sorted(df_equipes['Equipe'].dropna().astype(str).unique().tolist())
        hybrid_bloco = {get_hybrid_name(c): c for c in clubes_bloco_raw}
        hybrid_options = ["Selecione..."] + list(hybrid_bloco.keys())
        
        # Barra de Ferramentas — Apenas Ferramentas
        t_col1, t_col2, t_col3 = st.columns([1.5, 0.8, 0.8])
        with t_col1:
            new_file_analise = st.file_uploader("XLSX", type=["xlsx"], label_visibility="collapsed", key="excel_uploader_analise")
            if new_file_analise:
                st.session_state.uploaded_file = new_file_analise
                st.rerun()
        with t_col2:
            if st.button("💾 Salvar", use_container_width=True):
                with open(st.session_state.block_matches_file, 'w') as f:
                    json.dump(st.session_state.block_matches, f)
                st.session_state.block_notice = "✅ Salvo!"
                st.rerun()
        with t_col3:
            if st.button("📂 Abrir", use_container_width=True):
                if os.path.exists(st.session_state.block_matches_file):
                    with open(st.session_state.block_matches_file, 'r') as f:
                        st.session_state.block_matches = json.load(f)
                    st.session_state.block_results = []
                    st.session_state.block_notice = "✅ Carregado!"
                    st.rerun()
                else:
                    st.session_state.block_notice = "❌ Vazio"
                    st.rerun()

        if st.session_state.block_notice:
            st.toast(st.session_state.block_notice)
            st.session_state.block_notice = ''

        with st.form('form_adicionar_confronto', clear_on_submit=True):
            st.markdown('<p style="font-size:0.85rem; color:#718096; margin-bottom:10px;"><b>Dica:</b> Digite o nome da equipe (mesmo sem acento) nos campos abaixo para buscar.</p>', unsafe_allow_html=True)
            b_col1, b_col2, b_col3 = st.columns([2, 0.4, 2])
            with b_col1:
                bloco_mandante_hybrid = st.selectbox('Mandante', hybrid_options, key='bloco_mandante')
            with b_col2:
                st.markdown('<div style="font-size:1.2rem; font-weight:800; color:#CBD5E0; height:70px; display:flex; align-items:center; justify-content:center;">VS</div>', unsafe_allow_html=True)
            with b_col3:
                bloco_visitante_hybrid = st.selectbox('Visitante', hybrid_options, key='bloco_visitante')
            adicionar_bloco = st.form_submit_button('＋ Adicionar confronto ao bloco', use_container_width=True)
        
        if adicionar_bloco:
            if bloco_mandante_hybrid == 'Selecione...' or bloco_visitante_hybrid == 'Selecione...':
                st.session_state.block_notice = 'Selecione o mandante e o visitante antes de adicionar.'
                st.rerun()
            else:
                m_real = hybrid_bloco[bloco_mandante_hybrid]
                v_real = hybrid_bloco[bloco_visitante_hybrid]
                if m_real == v_real:
                    st.session_state.block_notice = 'O mandante e o visitante precisam ser equipes diferentes.'
                    st.rerun()
                elif any(x['mandante'] == m_real and x['visitante'] == v_real for x in st.session_state.block_matches):
                    st.session_state.block_notice = 'Este confronto já está no bloco.'
                    st.rerun()
                else:
                    st.session_state.block_matches.append({'mandante': m_real, 'visitante': v_real})
                    st.session_state.block_results = []
                    st.session_state.block_notice = f'{m_real} x {v_real} adicionado ao bloco.'
                    st.rerun()
        if adicionar_bloco:
            if bloco_mandante == 'Selecione...' or bloco_visitante == 'Selecione...':
                st.session_state.block_notice = 'Selecione o mandante e o visitante antes de adicionar.'
                st.rerun()
            elif bloco_mandante == bloco_visitante:
                st.session_state.block_notice = 'O mandante e o visitante precisam ser equipes diferentes.'
                st.rerun()
            elif any(x['mandante'] == bloco_mandante and x['visitante'] == bloco_visitante for x in st.session_state.block_matches):
                st.session_state.block_notice = 'Este confronto já está no bloco.'
                st.rerun()
            else:
                st.session_state.block_matches.append({'mandante': bloco_mandante, 'visitante': bloco_visitante})
                st.session_state.block_results = []
                st.session_state.block_notice = f'{bloco_mandante} x {bloco_visitante} adicionado ao bloco.'
                st.rerun()
        st.markdown('<div class="box-title">📦 Confrontos selecionados</div>', unsafe_allow_html=True)
        

        if not st.session_state.block_matches:
            st.info('Nenhum confronto adicionado. Monte o bloco usando os seletores acima.')
        else:
            for idx, confronto in enumerate(st.session_state.block_matches):
                r_col1, r_col2, r_col3 = st.columns([0.35, 3, 0.7])
                with r_col1:
                    st.markdown(f'<div style="padding-top:8px; color:#718096; font-weight:700;">{idx+1:02d}</div>', unsafe_allow_html=True)
                with r_col2:
                    st.markdown(f'<div class="details-box" style="padding:10px 14px; margin-bottom:8px;"><b>{confronto["mandante"]}</b> <span style="color:#A0AEC0;">x</span> <b>{confronto["visitante"]}</b></div>', unsafe_allow_html=True)
                with r_col3:
                    if st.button('Remover', key=f'remove_bloco_{idx}', use_container_width=True):
                        st.session_state.block_matches.pop(idx)
                        st.rerun()
            a_col1, a_col2 = st.columns([1, 1])
            with a_col1:
                if st.button('🧹 Limpar bloco', use_container_width=True):
                    st.session_state.block_matches = []
                    st.session_state.block_results = []
                    st.rerun()
            with a_col2:
                if st.button('🔎 Classificar melhores confrontos', use_container_width=True):
                    if not st.session_state.block_matches:
                        st.session_state.block_notice = 'Adicione confrontos antes de classificar.'
                        st.rerun()
                    
                    results = []
                    for conf in st.session_state.block_matches:
                        m = get_team_stats(conf['mandante'], df_dados, df_equipes)
                        v = get_team_stats(conf['visitante'], df_dados, df_equipes)
                        
                        # 1. Máquinas de gols: volume alto nas duas redes + equilíbrio GM/GS.
                        m_gm_avg = m.get('gm', 0) / max(m.get('jogos', 0), 1)
                        m_gs_avg = m.get('gs', 0) / max(m.get('jogos', 0), 1)
                        v_gm_avg = v.get('gm', 0) / max(v.get('jogos', 0), 1)
                        v_gs_avg = v.get('gs', 0) / max(v.get('jogos', 0), 1)
                        m_equilibrio = min(m_gm_avg, m_gs_avg) / max(m_gm_avg, m_gs_avg) if max(m_gm_avg, m_gs_avg) else 0
                        v_equilibrio = min(v_gm_avg, v_gs_avg) / max(v_gm_avg, v_gs_avg) if max(v_gm_avg, v_gs_avg) else 0
                        m_maquina = (m_gm_avg * m_gs_avg) * m_equilibrio
                        v_maquina = (v_gm_avg * v_gs_avg) * v_equilibrio
                        maquina_score = (m_maquina + v_maquina) / 2
                        
                        # 2. Mandante forte contra defesa visitante vulnerável.
                        fam_mandante = float(m.get('fam', 0) or 0)
                        vdv_visitante = float(v.get('vdv', 0) or 0)
                        cruzamento = fam_mandante * vdv_visitante
                        
                        # 3. Entrada confirmada: GE Real alto, sem veto e histórico mínimo disponível.
                        l_m, l_v = (m.get('fam', 0) + v.get('vdv', 0)) / 2, (v.get('fav', 0) + m.get('vdm', 0)) / 2
                        l_total = l_m + l_v
                        avg_id = (m.get('dispersao', 1) + v.get('dispersao', 1)) / 2
                        ge_real = l_total * np.sqrt(avg_id)
                        
                        # Filtro Robusto de Histórico (Strip e Case-Insensitive)
                        m_name_clean = str(conf['mandante']).strip().lower()
                        v_name_clean = str(conf['visitante']).strip().lower()
                        
                        # Filtro Robusto para Prova Real (Mandante em Casa e Visitante Fora)
                        mask_m_casa = df_dados['Mandante'].astype(str).str.strip().str.lower() == m_name_clean
                        mask_v_fora = df_dados['Visitante'].astype(str).str.strip().str.lower() == v_name_clean
                        
                        m_casa = df_dados[mask_m_casa].sort_values('Data', ascending=False).head(12)
                        v_fora = df_dados[mask_v_fora].sort_values('Data', ascending=False).head(12)
                        
                        # Cálculo de 0x0 Histórico (Fiel à Prova Real)
                        # O 0x0 na Prova Real é o percentual de jogos onde a soma de gols foi 0.
                        zero_m = (m_casa['GM_M'].astype(float) + m_casa['GM_V'].astype(float) == 0).mean() if not m_casa.empty else 1.0
                        zero_v = (v_fora['GM_M'].astype(float) + v_fora['GM_V'].astype(float) == 0).mean() if not v_fora.empty else 1.0
                        
                        p0x0_real = (poisson.pmf(0, l_m) * poisson.pmf(0, l_v)) * 100
                        p0x0_stress = p0x0_real * avg_id
                        
                        # Média de 0x0 Histórico para o Veto Sniper (Limite de 8%)
                        avg_zero_hist = (zero_m + zero_v) / 2 * 100
                        # O Veto é ativado se o Estresse (ID) > 8% OU a Média Histórica > 8%
                        is_veto = p0x0_stress > 8 or avg_zero_hist > 8
                        confirmado = bool(ge_real > 1.8 and not is_veto and not m_casa.empty and not v_fora.empty)
                        
                        # Métricas empíricas da condição específica: casa para o mandante e fora para o visitante.
                        def empirical_summary(frame):
                            if frame.empty:
                                return {'jogos': 0, 'over15': 0.0, 'over25': 0.0, 'over2plus': 0.0, 'over3plus': 0.0}
                            total_goals = frame['GM_M'].astype(float) + frame['GM_V'].astype(float)
                            return {
                                'jogos': len(frame),
                                'over15': float((total_goals >= 2).mean() * 100),
                                'over25': float((total_goals >= 3).mean() * 100),
                                'over2plus': float((total_goals >= 2).mean() * 100),
                                'over3plus': float((total_goals >= 3).mean() * 100)
                            }

                        home_emp = empirical_summary(m_casa)
                        away_emp = empirical_summary(v_fora)
                        j_casa, j_fora = home_emp['jogos'], away_emp['jogos']
                        emp_2_min = min(home_emp['over2plus'], away_emp['over2plus'])
                        emp_3_min = min(home_emp['over3plus'], away_emp['over3plus'])
                        
                        # --- CONCILIAÇÃO SOBERANA (SIMULAÇÃO INTEGRAL DAS TABELAS) ---
                        
                        # 1. Distribuição Estatística (Poisson)
                        def get_poi_metrics(ge):
                            lines = [0.5, 1.0, 1.5, 2.0, 2.5]
                            return {ln: (1 - poisson.cdf(0 if ln==0.5 else 1 if ln<=1.5 else 2, ge)) * 100 for ln in lines}
                        probs_poi = get_poi_metrics(ge_real)
                        
                        # 2. Distribuição Empírica (Prova Real)
                        def get_emp_metrics():
                            # Fiel à planilha: o empírico usa a MÉDIA das frequências das equipes na condição
                            comb_o05 = 100 - avg_zero_hist
                            comb_o15 = (home_emp['over15'] + away_emp['over15']) / 2
                            comb_o25 = (home_emp['over25'] + away_emp['over25']) / 2
                            # Para as linhas de proteção (1.0 e 2.0), usamos a linha de green imediatamente abaixo
                            return {0.5: comb_o05, 1.0: comb_o15, 1.5: comb_o15, 2.0: comb_o25, 2.5: comb_o25}
                        probs_emp = get_emp_metrics()
                        
                        # 3. Tabela de Distribuição e Proteção (Consenso)
                        # A matemática oficial do Excel para o Consenso é a média aritmética entre Poisson e Real.
                        # Para Yanbian, o Poisson é alto (devido ao GE 2.99), puxando a média para cima.
                        def get_protection_cons(ln):
                            # Proteção oficial: Probabilidade de NÃO ter RED na linha.
                            if ln == 0.5: return (probs_poi[0.5] + probs_emp[0.5]) / 2
                            if ln == 1.0: return (probs_poi[0.5] + probs_emp[0.5]) / 2
                            if ln == 1.5: return (probs_poi[1.5] + probs_emp[1.5]) / 2
                            if ln == 2.0: return (probs_poi[1.5] + probs_emp[1.5]) / 2
                            if ln == 2.5: return (probs_poi[2.5] + probs_emp[2.5]) / 2
                            return (probs_poi[ln] + probs_emp[ln]) / 2

                        def get_leitura_planilha(ln, g_cons, p_cons):
                            # Regra oficial da planilha: Green >= 75% ou Proteção >= 75%
                            if g_cons >= 75: return "GREEN ≥75%"
                            if p_cons >= 75: return "PROTEÇÃO ≥75%"
                            return "ABAIXO"
                        
                        dist_table = []
                        limite_green = "N/A"
                        inicio_prot = "N/A"
                        
                        for ln in [0.5, 1.0, 1.5, 2.0, 2.5]:
                            # Consenso Conservador: Se a Prova Real está abaixo de 75%, o consenso não pode "mascarar" o risco.
                            g_pure = (probs_poi[ln] + probs_emp[ln]) / 2
                            if probs_emp[ln] < 75:
                                # Trava: O consenso respeita o teto da Prova Real para evitar otimismo matemático excessivo
                                g_cons = min(g_pure, probs_emp[ln] + (g_pure - probs_emp[ln]) * 0.3)
                            else:
                                g_cons = g_pure
                                
                            p_cons = get_protection_cons(ln)
                            leitura_ln = get_leitura_planilha(ln, g_cons, p_cons)
                            
                            # Identificar marcos da fronteira
                            if g_cons >= 75:
                                limite_green = f"OVER {ln:.2f}".replace('.', ',')
                            elif p_cons >= 75 and inicio_prot == "N/A":
                                inicio_prot = f"OVER {ln:.2f}".replace('.', ',')
                                
                            dist_table.append({
                                'linha': f"OVER {ln:.2f}".replace('.', ','),
                                'green': g_cons,
                                'leitura': leitura_ln
                            })

                        # Veto Sniper e Regra Operacional
                        is_veto_sniper = is_veto
                        veto_text = "⚠️ ALERTA DE VETO (0x0)" if is_veto_sniper else "✅ SEM VETO POR 0x0"
                        regra_op = "🚀 ENTRADA CONFIRMADA EM OVER" if ge_real > 1.8 and not is_veto_sniper else "🛡️ RECOMENDADO CAUTELA / UNDER"
                        
                        # Detalhes do Veto e Modelo
                        modelo_est = m.get('modelo', 'Poisson')
                        p0x0_real_val = (poisson.pmf(0, l_m) * poisson.pmf(0, l_v)) * 100
                        veto_detalhe = f"Prob. Real: {p0x0_real_val:.1f}% | Estresse (ID): {p0x0_stress:.1f}% | Modelo: {modelo_est}"
                        
                        # Status do Card (VERMELHO APENAS SE REPROVADO)
                        # O Veto oficial da planilha é acionado com 8% de estresse ou média histórica.
                        if is_veto_sniper:
                            leitura, status_key, border_color, bg_color = 'REPROVADO', 0, '#E53E3E', '#FFF5F5'
                        elif ge_real > 1.8:
                            leitura, status_key, border_color, bg_color = 'FORTE', 3, '#0F5FA8', '#EBF8FF'
                        else:
                            leitura, status_key, border_color, bg_color = 'CAUTELA', 1, '#4299E1', '#F7FCFF'

                        obs = f"<b>{veto_text}</b><br><span style='font-size:10px; opacity:0.8;'>{veto_detalhe}</span><br>REGRA OPERACIONAL: {regra_op}"

                        # Média dos Últimos 5 Jogos (Fiel à Prova Real)
                        m_recent5 = df_dados[(df_dados['Mandante'] == conf['mandante']) | (df_dados['Visitante'] == conf['mandante'])].sort_values('Data', ascending=False).head(5)
                        v_recent5 = df_dados[(df_dados['Mandante'] == conf['visitante']) | (df_dados['Visitante'] == conf['visitante'])].sort_values('Data', ascending=False).head(5)
                        m_last5_avg = ((m_recent5['GM_M'].astype(float) + m_recent5['GM_V'].astype(float)).mean() if not m_recent5.empty else 0.0)
                        v_last5_avg = ((v_recent5['GM_M'].astype(float) + v_recent5['GM_V'].astype(float)).mean() if not v_recent5.empty else 0.0)
                        ultimos5 = (m_last5_avg + v_last5_avg) / 2

                        # Novas Métricas Solicitadas: Média Efetiva da Liga, GM Casa e GS Fora
                        liga_nome = m.get('liga', 'N/A')
                        media_efetiva = 0.0
                        if 'Ligas' in all_data:
                            df_ligas_full = all_data['Ligas']
                            liga_row = df_ligas_full[df_ligas_full['Liga'].astype(str).str.strip().str.lower() == str(liga_nome).strip().lower()]
                            if not liga_row.empty:
                                media_efetiva = float(liga_row['Média Efetiva da Liga'].iloc[0])
                        
                        gm_casa = float(m_casa['GM_M'].astype(float).mean()) if not m_casa.empty else 0.0
                        gs_fora = float(v_fora['GM_V'].astype(float).mean()) if not v_fora.empty else 0.0

                        # Sugestão de Linha para o .txt (Baseado no GE Real)
                        if is_veto_sniper and ge_real > 0:
                            linha_sugerida = "NÃO APOSTAR"
                        elif ge_real <= 0:
                            linha_sugerida = "ERRO: DADOS"
                        elif ge_real >= 2.4:
                            linha_sugerida = "OVER 2,00"
                        elif ge_real >= 1.85:
                            linha_sugerida = "OVER 1,50"
                        elif ge_real >= 1.5:
                            linha_sugerida = "OVER 1,00"
                        else:
                            linha_sugerida = "OVER 0,50"

                        # Identificação de Rankings de Elite para Alertas
                        # A aba Equipes V3 não possui as colunas legadas 'Liga', 'GM', 'GS' e 'Jogos'.
                        # Ela usa 'País - Liga', 'TGM', 'TGS' e 'TJT'.
                        df_elite = df_equipes.copy()
                        if 'País - Liga' in df_elite.columns:
                            df_elite = df_elite[~df_elite['País - Liga'].astype(str).str.contains('MLS-Cross', case=False, na=False)].copy()
                        elif 'Liga' in df_elite.columns:
                            df_elite = df_elite[df_elite['Liga'].astype(str).str.casefold() != 'mls-cross'].copy()

                        # Aliases robustos para manter compatibilidade com versões antigas e V3.
                        jogos_col = 'TJT' if 'TJT' in df_elite.columns else ('Jogos' if 'Jogos' in df_elite.columns else None)
                        gm_col = 'TGM' if 'TGM' in df_elite.columns else ('GM' if 'GM' in df_elite.columns else None)
                        gs_col = 'TGS' if 'TGS' in df_elite.columns else ('GS' if 'GS' in df_elite.columns else None)
                        if not all([jogos_col, gm_col, gs_col]):
                            raise KeyError('A aba Equipes precisa conter TGM/TGS/TJT (ou os aliases GM/GS/Jogos).')

                        jogos_base = pd.to_numeric(df_elite[jogos_col], errors='coerce').fillna(0).replace(0, 1)
                        gm_base = pd.to_numeric(df_elite[gm_col], errors='coerce').fillna(0)
                        gs_base = pd.to_numeric(df_elite[gs_col], errors='coerce').fillna(0)
                        df_elite['GM_Avg'] = gm_base / jogos_base
                        df_elite['GS_Avg'] = gs_base / jogos_base
                        max_avg = df_elite[['GM_Avg', 'GS_Avg']].max(axis=1).replace(0, 1)
                        df_elite['Score_Maquina'] = (df_elite['GM_Avg'] * df_elite['GS_Avg']) * (df_elite[['GM_Avg', 'GS_Avg']].min(axis=1) / max_avg)
                        df_elite['GM_Base'] = gm_base
                        df_elite['GS_Base'] = gs_base

                        top_maquinas = df_elite.sort_values('Score_Maquina', ascending=False).head(15)['Equipe'].tolist()
                        top_ataques = df_elite.sort_values('GM_Base', ascending=False).head(15)['Equipe'].tolist()
                        top_defesas = df_elite.sort_values('GS_Base', ascending=False).head(15)['Equipe'].tolist() # Maiores TGS = Piores Defesas
                        
                        alertas = []
                        if conf['mandante'] in top_maquinas: alertas.append("🔥 Máquina (M)")
                        if conf['visitante'] in top_maquinas: alertas.append("🔥 Máquina (V)")
                        if conf['mandante'] in top_ataques: alertas.append("🎯 Elite Ataque (M)")
                        if conf['visitante'] in top_ataques: alertas.append("🎯 Elite Ataque (V)")
                        if conf['mandante'] in top_defesas: alertas.append("❄️ Defesa Frágil (M)")
                        if conf['visitante'] in top_defesas: alertas.append("❄️ Defesa Frágil (V)")

                        results.append({
                            'confronto': f"{conf['mandante']} x {conf['visitante']}",
                            'mandante': conf['mandante'],
                            'visitante': conf['visitante'],
                            'maquina': maquina_score,
                            'cruzamento': cruzamento,
                            'leitura': leitura,
                            'status_key': status_key,
                            'border_color': border_color,
                            'bg_color': bg_color,
                            'linha': linha_sugerida,
                            'obs': obs,
                            'ge_real': ge_real,
                            'p0x0': p0x0_stress,
                            'lambda_total': l_total,
                            'dist_table': dist_table,
                            'j_casa': j_casa,
                            'j_fora': j_fora,
                            'emp2': emp_2_min,
                            'emp3': emp_3_min,
                            'ultimos5': ultimos5,
                            'media_efetiva': media_efetiva,
                            'gm_casa': gm_casa,
                            'gs_fora': gs_fora,
                            'pais': m.get('pais', 'N/A'),
                            'liga': m.get('liga', 'N/A'),
                            'alertas': alertas,
                            'limite_green': limite_green,
                            'inicio_prot': inicio_prot,
                            'p_green': (probs_poi[1.5] + probs_emp[1.5]) / 2 # Chave para o sumário operacional
                        })
                    
                    # Ordem: melhor leitura -> maior confirmação empírica -> maior GE Real -> maior máquina.
                    st.session_state.block_results = sorted(results, key=lambda x: (x['status_key'], x['ge_real'], x['emp2'], x['maquina'], x['cruzamento']), reverse=True)
                    st.session_state.block_notice = '✅ Classificação concluída com sucesso!'
                    st.rerun()
        
        if st.session_state.block_results:
            st.markdown('<div class="box-title">🏆 Diagnóstico Sniper — Avaliação O2.0</div>', unsafe_allow_html=True)
            
            # 1. Seleção de Bilhetes para Exportação
            st.write("Selecione os confrontos e insira as Odds:")
            selected_indices = []
            cols = st.columns(2)
            for idx, res in enumerate(st.session_state.block_results):
                with cols[idx % 2]:
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        is_selected = st.checkbox(f"#{idx+1:02d} · {res['confronto']}", key=f"sel_{idx}")
                    with c2:
                        odd_input = st.text_input("Odd", key=f"odd_{idx}", label_visibility="collapsed", placeholder="Odd", disabled=not is_selected)
                    
                    if is_selected:
                        selected_indices.append(idx)
            
            if st.button("📥 Gerar Bilhetes Simplificados (.txt)", use_container_width=True):
                if not selected_indices:
                    st.warning("Selecione ao menos um confronto.")
                else:
                    export_content = ""
                    for idx in selected_indices:
                        res = st.session_state.block_results[idx]
                        odd_val = st.session_state.get(f"odd_{idx}", "1.00")
                        export_content += f"{res['confronto']} - {odd_val}\n"
                    
                    st.download_button(
                        label="💾 Baixar Arquivo de Bilhetes",
                        data=export_content,
                        file_name=f"bilhetes_simples_{datetime.now().strftime('%d_%m_%H%M')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
            
            st.markdown("---")

            st.divider()

            # Texto de Leitura Operacional Unificada (Estilo Copilot)
            all_greens = [r['p_green'] for r in st.session_state.block_results]
            min_green = min(all_greens) if all_greens else 0
            max_green = max(all_greens) if all_greens else 0
            
            resumo_html = ""
            for idx, res in enumerate(st.session_state.block_results, start=1):
                resumo_html += f"<b>{idx}. {res['confronto']}</b>: {res['obs']}<br>"
            
            # Layout nativo do Streamlit para garantir que NADA seja cortado
            st.markdown("### 📋 Leitura Operacional")
            st.info(f"Os confrontos selecionados foram avaliados individualmente. A probabilidade média de **GREEN Consenso (Over 1.5)** varia de **{min_green:.1f}%** a **{max_green:.1f}%**.")
            
            # Usar expander ou container nativo para o resumo detalhado
            with st.container(border=True):
                st.markdown(resumo_html, unsafe_allow_html=True)
                st.caption("Regra operacional: A linha sugerida busca o equilíbrio entre probabilidade de acerto e proteção do capital. Considere a entrada se a odd de mercado for superior à odd justa calculada pelo modelo.")
            
            st.divider()

            cards = []
            for idx, res in enumerate(st.session_state.block_results, start=1):
                conv = 'SIM' if res['ge_real'] >= res['lambda_total'] else 'NÃO'
                conv_color = '#38A169' if conv == 'SIM' else '#E53E3E'
                cards.append(f"""
                    <article class='sniper-card' style='border-color:{res['border_color']}; background:{res['bg_color']};'>
                        <div class='card-top'>
                            <div class='rank' style='color:{res['border_color']};'>#{idx:02d} · {res['leitura']}</div>
                            <div class='match'>
                                <strong>{res['mandante']} x {res['visitante']}</strong>
                                <span>{res['pais']} - {res['liga']}</span>
                                <div style='margin-top:4px;'>
                                    {' '.join([f"<span style='background:#2D3748; color:white; padding:1px 5px; border-radius:3px; font-size:9px; margin-right:3px;'>{a}</span>" for a in res['alertas']])}
                                </div>
                            </div>
                            <div class='line' style='color:{res['border_color']}; text-align:right;'>
                                <span style='font-size:9px; color:#718096; display:block;'>GE REAL (FATO)</span>
                                <b style='font-size:1.4rem;'>{res['ge_real']:.2f}</b>
                            </div>
                        </div>
                        
                        <div style='display:grid; grid-template-columns: 1.2fr 2fr; gap:15px; margin:12px 0;'>
                            <div style='padding:12px; background:rgba(0,0,0,0.03); border-radius:8px; font-size:12px; line-height:1.5; border-left:4px solid {res['border_color']};'>
                                {res['obs']}
                            </div>
                            <div style='background:white; border:1px solid #E2E8F0; border-radius:8px; padding:8px;'>
                                <table style='width:100%; font-size:10px; border-collapse:collapse;'>
                                    <tr style='border-bottom:1px solid #EDF2F7; color:#718096;'>
                                        <th style='text-align:left; padding:4px;'>LINHA</th>
                                        <th style='text-align:center; padding:4px;'>GREEN CONS.</th>
                                        <th style='text-align:right; padding:4px;'>LEITURA</th>
                                    </tr>
                                    {''.join([f"<tr><td style='padding:4px; font-weight:700;'>{row['linha']}</td><td style='padding:4px; text-align:center; color:#2B6CB0; font-weight:800;'>{row['green']:.1f}%</td><td style='padding:4px; text-align:right; font-weight:600;'>{row['leitura']}</td></tr>" for row in res['dist_table']])}
                                </table>
                            </div>
                        </div>

                        <div class='metric-grid'>
                            <div><small>J CASA</small><b>{res['j_casa']}</b></div>
                            <div><small>J FORA</small><b>{res['j_fora']}</b></div>
                            <div><small>λ TOTAL</small><b>{res['lambda_total']:.2f}</b></div>
                            <div><small>RISCO 0x0</small><b class='red'>{res['p0x0']:.1f}%</b></div>
                            <div><small>2+ EMP. MÍN.</small><b>{res['emp2']:.1f}%</b></div>
                            <div><small>3+ EMP. MÍN.</small><b>{res['emp3']:.1f}%</b></div>
                            <div><small>ÚLTIMOS 5</small><b>{res['ultimos5']:.2f}</b></div>
                            <div style='background:rgba(0,0,0,0.03); border-radius:4px; padding:2px;'><small>EFETIVA LIGA</small><b>{res['media_efetiva']:.2f}</b></div>
                            <div style='background:rgba(56,161,105,0.05); border-radius:4px; padding:2px;'><small style='color:#2F855A;'>GM CASA</small><b style='color:#2F855A;'>{res['gm_casa']:.2f}</b></div>
                            <div style='background:rgba(229,62,62,0.05); border-radius:4px; padding:2px;'><small style='color:#C53030;'>GS FORA</small><b style='color:#C53030;'>{res['gs_fora']:.2f}</b></div>
                            <div style='background:rgba(56,161,105,0.1); border-radius:4px; padding:2px;'><small style='color:#2F855A;'>LIMITE GREEN</small><b style='color:#2F855A;'>{res['limite_green']}</b></div>
                            <div style='background:rgba(49,130,206,0.1); border-radius:4px; padding:2px;'><small style='color:#2B6CB0;'>INÍCIO PROT.</small><b style='color:#2B6CB0;'>{res['inicio_prot']}</b></div>
                        </div>
                    </article>
                """)
            cards_html = """
                <style>
                    * { box-sizing:border-box; }
                    body { margin:0; background:#fff; font-family:Inter,Arial,sans-serif; color:#1A202C; }
                    .sniper-card { border:2px solid; border-radius:12px; padding:14px 18px 13px; margin:0 0 11px; box-shadow:0 2px 7px rgba(15,95,168,.08); }
                    .card-top { display:grid; grid-template-columns:1.25fr 3fr 1.45fr; gap:18px; align-items:center; margin-bottom:12px; }
                    .rank { font-size:12px; font-weight:800; text-transform:uppercase; white-space:nowrap; }
                    .match { display:flex; flex-direction:column; gap:3px; font-size:15px; }
                    .match span { color:#718096; font-size:10px; }
                    .line { text-align:right; font-size:13px; font-weight:800; text-transform:uppercase; white-space:nowrap; }
                    .metric-grid { display:grid; grid-template-columns:repeat(11, minmax(62px,1fr)); gap:7px; border-top:1px solid rgba(113,128,150,.1); padding-top:10px; }
                    .metric-grid div { display:flex; flex-direction:column; gap:3px; min-width:0; }
                    .metric-grid small { color:#718096; font-size:8px; font-weight:700; white-space:nowrap; }
                    .metric-grid b { color:#2D3748; font-size:12px; font-variant-numeric:tabular-nums; }
                    .metric-grid .blue { color:#2B6CB0; }
                    .metric-grid .red { color:#E53E3E; }
                    @media (max-width: 900px) {
                        .card-top { grid-template-columns:1fr; gap:7px; }
                        .line { text-align:left; }
                        .metric-grid { grid-template-columns:repeat(4,1fr); row-gap:10px; }
                    }
                </style>
            """ + ''.join(cards)
            components.html(cards_html, height=min(1000, 145 * len(st.session_state.block_results)), scrolling=True)

    elif st.session_state.menu == 'Bilhetes':
        st.markdown('<div class="sim-header"><h3 style="margin:0; color:#2C5282;">📋 Bilhetes — Decisões Pré e Pós-Jogo</h3><p style="margin:0; color:#4A5568; font-size:0.9rem;">Acompanhamento detalhado das apostas realizadas, análises, odds recebidas e liquidações</p></div>', unsafe_allow_html=True)
        
        if 'Bilhetes' in all_data:
            df_bilh_raw = pd.read_excel(EXCEL_PATH, sheet_name='Bilhetes', header=None)
            bilhetes_list = []
            i = 3
            while i < len(df_bilh_raw):
                row_date = df_bilh_raw.iloc[i].get(0)
                match_name = df_bilh_raw.iloc[i].get(2)
                
                # Parar se encontrar o resumo da carteira ou se o nome da partida for inválido
                if pd.isna(match_name) and pd.isna(row_date):
                    i += 1
                    continue
                
                if match_name and any(x in str(match_name).upper() for x in ["RESUMO", "DESEMPENHO", "PERCENTUAL", "LEGENDA"]):
                    break
                if row_date and any(x in str(row_date).upper() for x in ["PERCENTUAL", "LEGENDA"]):
                    break
                
                try:
                    league = df_bilh_raw.iloc[i+1].get(0) if i+1 < len(df_bilh_raw) else ""
                    model_info = df_bilh_raw.iloc[i+2].get(1) if i+2 < len(df_bilh_raw) else ""
                    tecnica = df_bilh_raw.iloc[i+2].get(5) if i+2 < len(df_bilh_raw) else ""
                    orientacao = df_bilh_raw.iloc[i+2].get(7) if i+2 < len(df_bilh_raw) else ""
                    odds_info = df_bilh_raw.iloc[i+3].get(1) if i+3 < len(df_bilh_raw) else ""
                    decisao_linha = df_bilh_raw.iloc[i+4].get(1) if i+4 < len(df_bilh_raw) else ""
                    motivo = df_bilh_raw.iloc[i+4].get(4) if i+4 < len(df_bilh_raw) else ""
                    bilhete_linha = df_bilh_raw.iloc[i+5].get(1) if i+5 < len(df_bilh_raw) else ""
                    odd_val = df_bilh_raw.iloc[i+5].get(3) if i+5 < len(df_bilh_raw) else 0
                    stake_val = df_bilh_raw.iloc[i+5].get(5) if i+5 < len(df_bilh_raw) else 0
                    status_val = df_bilh_raw.iloc[i+5].get(7) if i+5 < len(df_bilh_raw) else ""
                    home_g = df_bilh_raw.iloc[i+6].get(2) if i+6 < len(df_bilh_raw) else 0
                    away_g = df_bilh_raw.iloc[i+6].get(4) if i+6 < len(df_bilh_raw) else 0
                    total_g = df_bilh_raw.iloc[i+6].get(6) if i+6 < len(df_bilh_raw) else 0
                    resultado = df_bilh_raw.iloc[i+7].get(2) if i+7 < len(df_bilh_raw) else ""
                    pl_val = df_bilh_raw.iloc[i+7].get(4) if i+7 < len(df_bilh_raw) else 0
                    obs = df_bilh_raw.iloc[i+7].get(5) if i+7 < len(df_bilh_raw) else ""
                    
                    # Formatar data se for datetime
                    date_str = row_date.strftime('%d/%m/%Y') if hasattr(row_date, 'strftime') else str(row_date)
                    
                    bilhetes_list.append({
                        'date': date_str,
                        'match': match_name,
                        'league': league,
                        'model': model_info,
                        'tecnica': tecnica,
                        'orientacao': orientacao,
                        'odds_info': odds_info,
                        'decisao_linha': decisao_linha,
                        'motivo': motivo,
                        'odd': float(odd_val) if pd.notna(odd_val) else 0.0,
                        'stake': float(stake_val) if pd.notna(stake_val) else 0.5,
                        'status': status_val,
                        'home_g': home_g,
                        'away_g': away_g,
                        'total_g': total_g,
                        'resultado': str(resultado).strip(),
                        'pl': float(pl_val) if pd.notna(pl_val) else 0.0,
                        'obs': obs
                    })
                except Exception as e:
                    pass
                i += 9

            if bilhetes_list:
                # Filtro: Contar apenas bilhetes liquidados
                liquidados = [b for b in bilhetes_list if any(x in b['resultado'].lower() for x in ['green', 'red', 'devolvida', 'push', 'reembolso', 'cashout'])]
                
                total_liq = len(liquidados)
                greens_b = sum(1 for b in liquidados if 'green' in b['resultado'].lower())
                reds_b = sum(1 for b in liquidados if 'red' in b['resultado'].lower() and 'meio' not in b['resultado'].lower())
                meio_red_b = sum(1 for b in liquidados if 'meio red' in b['resultado'].lower() or 'meio-red' in b['resultado'].lower())
                devolvidas_b = sum(1 for b in liquidados if any(x in b['resultado'].lower() for x in ['devolvida', 'push', 'reembolso']))
                cashouts_b = sum(1 for b in liquidados if 'cashout' in b['resultado'].lower())
                pnl_b = sum(b['pl'] for b in bilhetes_list) # P/L continua sendo o total geral
                
                b1, b2, b3, b4, b5, b6 = st.columns([1, 1.5, 1, 1, 1, 1.2])
                b1.metric('Liquidados', total_liq)
                
                # Acertos: Somatória de Greens + Cashouts
                acertos_total = greens_b + cashouts_b
                b2.metric('Acertos', acertos_total, help=f"Greens ({greens_b}) + Cashouts ({cashouts_b})")
                with b2:
                    st.markdown(f'<p style="font-size:0.7rem; color:#718096; margin-top:-15px;">({greens_b} G + {cashouts_b} C)</p>', unsafe_allow_html=True)
                
                b3.metric('Devolvidas', devolvidas_b)
                b4.metric('Meio-Red', meio_red_b)
                b5.metric('Red', reds_b)
                b6.metric('P/L Total', f'R$ {pnl_b:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
                st.markdown('---')

                cards_html = """
                <style>
                    .excel-bilhete { width:100%; border-collapse:collapse; font-family:Inter,Arial,sans-serif; margin-bottom:20px; border:1px solid #CBD5E0; font-size:12px; border-radius:8px; overflow:hidden; box-shadow:0 2px 5px rgba(0,0,0,0.05); }
                    .excel-header { background:#0F5FA8; color:white; font-weight:bold; text-align:center; padding:8px; font-size:14px; text-transform:uppercase; letter-spacing:0.5px; }
                    .excel-row { display:flex; border-bottom:1px solid #E2E8F0; }
                    .excel-label { background:#4299E1; color:white; width:110px; padding:6px 10px; font-weight:bold; text-transform:uppercase; flex-shrink:0; display:flex; align-items:center; font-size:10px; }
                    .excel-content { flex-grow:1; padding:6px 10px; background:white; display:flex; align-items:center; border-left:1px solid #E2E8F0; color:#2D3748; }
                    .excel-sub-label { background:#F7FAFC; color:#4A5568; padding:6px 10px; font-weight:bold; border-left:1px solid #E2E8F0; min-width:90px; font-size:10px; text-transform:uppercase; }
                    .excel-sub-content { padding:6px 10px; background:white; border-left:1px solid #E2E8F0; flex-grow:1; color:#2D3748; }
                    .placar-box { background:#EBF8FF; color:#2B6CB0; font-weight:bold; text-align:center; min-width:70px; padding:6px; border-left:1px solid #E2E8F0; font-size:14px; }
                    .green-box { background:#C6F6D5; color:#22543D; font-weight:bold; text-align:center; padding:6px; min-width:110px; border-left:1px solid #E2E8F0; text-transform:uppercase; }
                    .red-box { background:#FED7D7; color:#742A2A; font-weight:bold; text-align:center; padding:6px; min-width:110px; border-left:1px solid #E2E8F0; text-transform:uppercase; }
                </style>
                """
                for b in bilhetes_list:
                    res_lower = b['resultado'].lower()
                    if "green" in res_lower: res_class = "green-box"
                    elif "red" in res_lower or "meio red" in res_lower: res_class = "red-box"
                    elif any(x in res_lower for x in ["devolvida", "push", "reembolso"]): res_class = "excel-sub-content"
                    else: res_class = "excel-sub-content"
                    
                    cards_html += f"""
                    <div class="excel-bilhete">
                        <div class="excel-header">{b['date']} · {b['match']}</div>
                        
                        <div class="excel-row" style="background:#EDF2F7;">
                            <div style="padding:5px 12px; font-weight:bold; color:#2C5282; font-size:11px;">{b['league']}</div>
                            <div style="margin-left:auto; display:flex;">
                                <div class="excel-sub-label">Data/Hora</div>
                                <div class="excel-sub-content">{b['date']} · GMT-3</div>
                            </div>
                        </div>

                        <div class="excel-row">
                            <div class="excel-label">MODELO</div>
                            <div class="excel-content">{b['model']}</div>
                            <div class="excel-sub-label">Técnica</div>
                            <div class="excel-sub-content">{b['tecnica']}</div>
                            <div class="excel-sub-label">Orientação</div>
                            <div class="excel-sub-content">{b['orientacao']}</div>
                        </div>

                        <div class="excel-row">
                            <div class="excel-label">ODDS</div>
                            <div class="excel-content">{b['odds_info']}</div>
                        </div>

                        <div class="excel-row">
                            <div class="excel-label">DECISÃO</div>
                            <div class="excel-content">{b['decisao_linha']}</div>
                            <div class="excel-sub-label">Motivo</div>
                            <div class="excel-sub-content">{b['motivo']}</div>
                        </div>

                        <div class="excel-row">
                            <div class="excel-label">BILHETE</div>
                            <div class="excel-content" style="font-weight:bold; color:#2B6CB0;">{b['decisao_linha'].split('@')[0] if '@' in b['decisao_linha'] else b['decisao_linha']}</div>
                            <div class="excel-sub-label">Odd</div>
                            <div class="excel-sub-content">{b['odd']:.3f}</div>
                            <div class="excel-sub-label">Stake</div>
                            <div class="excel-sub-content">R$ {b['stake']:.2f}</div>
                            <div class="excel-sub-label">Status</div>
                            <div class="excel-sub-content">{b['status']}</div>
                        </div>

                        <div class="excel-row">
                            <div class="excel-label" style="background:#2B6CB0;">PLACAR</div>
                            <div class="excel-sub-label" style="background:#4299E1; color:white;">Mandante</div>
                            <div class="placar-box">{b['home_g']}</div>
                            <div class="excel-sub-label" style="background:#4299E1; color:white;">Visitante</div>
                            <div class="placar-box">{b['away_g']}</div>
                            <div class="excel-sub-label">Total</div>
                            <div class="excel-sub-content" style="text-align:center; font-weight:bold; font-size:14px;">{b['total_g']}</div>
                        </div>

                        <div class="excel-row">
                            <div class="excel-label" style="background:#2B6CB0;">LIQUIDAÇÃO</div>
                            <div class="excel-sub-content" style="font-weight:bold; color:#4A5568;">Resultado</div>
                            <div class="{res_class}">{b['resultado']}</div>
                            <div class="excel-sub-label">P/L</div>
                            <div class="excel-sub-content" style="font-weight:bold; font-size:13px; color:{'#38A169' if b['pl'] > 0 else '#E53E3E'};">R$ {b['pl']:+.2f}</div>
                            <div class="excel-sub-content" style="font-style:italic; color:#718096; font-size:11px; border-left:none;">{b['obs']}</div>
                        </div>
                    </div>
                    """
                components.html(cards_html, height=min(1200, 160 * len(bilhetes_list)), scrolling=True)
            else:
                st.info('Nenhum bilhete processado na aba Bilhetes.')
        else:
            st.info('A aba Bilhetes não foi encontrada no arquivo Excel.')

    elif st.session_state.menu == 'Track Record':
        st.markdown('<div class="sim-header"><h3 style="margin:0; color:#2C5282;">📈 Track Record — Histórico de 25 Colunas</h3><p style="margin:0; color:#4A5568; font-size:0.9rem;">Avaliação empírica completa das linhas usadas vs. melhor aproveitamento nos greens</p></div>', unsafe_allow_html=True)
        
        track_sheet = next((name for name in ('BackTest', 'Backtest') if name in all_data), None)
        if track_sheet:
            # Carregar todas as 25 colunas e remover linhas sem confronto
            track_df = pd.read_excel(EXCEL_PATH, sheet_name=track_sheet, header=1).dropna(subset=['Modelo 01'])
            
            if not track_df.empty:
                # Métricas de Resumo
                if 'P/L (R$)' in track_df.columns:
                    track_df['P/L (R$)'] = pd.to_numeric(track_df['P/L (R$)'], errors='coerce').fillna(0)
                    greens = int((track_df['P/L (R$)'] > 0).sum())
                    reds = int((track_df['P/L (R$)'] < 0).sum())
                    pnl_total = float(track_df['P/L (R$)'].sum())
                    
                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric('Total Jogos', len(track_df))
                    k2.metric('Greens', greens)
                    k3.metric('Reds', reds)
                    k4.metric('P/L Acumulado', f'R$ {pnl_total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
                    st.markdown('---')

                # Estilo para os Cards de 25 colunas
                track_cards = """
                <style>
                    .backtest-card { border:1px solid #CBD5E0; background:white; border-radius:10px; margin-bottom:15px; font-family:Arial,sans-serif; overflow:hidden; box-shadow:0 2px 4px rgba(0,0,0,0.05); }
                    .backtest-header { background:#2D3748; color:white; padding:8px 15px; display:flex; justify-content:space-between; align-items:center; }
                    .backtest-body { padding:12px; }
                    .backtest-grid { display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; margin-bottom:12px; }
                    .backtest-item { display:flex; flex-direction:column; }
                    .backtest-label { font-size:9px; color:#718096; font-weight:bold; text-transform:uppercase; }
                    .backtest-value { font-size:12px; color:#2D3748; font-weight:600; }
                    .asian-matrix { display:flex; background:#F7FAFC; border-top:1px solid #EDF2F7; padding:10px; gap:4px; overflow-x:auto; }
                    .asian-cell { display:flex; flex-direction:column; align-items:center; min-width:45px; border:1px solid #E2E8F0; border-radius:4px; padding:4px; }
                    .asian-line { font-size:9px; font-weight:bold; color:#4A5568; margin-bottom:2px; }
                    .asian-res { font-size:11px; font-weight:800; padding:2px 6px; border-radius:3px; }
                    .g-res { background:#C6F6D5; color:#22543D; }
                    .p-res { background:#FEFCBF; color:#744210; }
                    .r-res { background:#FED7D7; color:#742A2A; }
                    .hg-res { background:#C6F6D5; color:#22543D; border:1px dashed #22543D; }
                    .hr-res { background:#FED7D7; color:#742A2A; border:1px dashed #742A2A; }
                    .bet-target { border:3px solid #4299E1 !important; box-shadow:0 0 8px rgba(66,153,225,0.4); position:relative; }
                    .bet-target::after { content:'🎯'; position:absolute; top:-8px; right:-8px; font-size:12px; }
                    .best-target { border:3px solid #38A169 !important; box-shadow:0 0 8px rgba(56,161,105,0.4); position:relative; }
                    .best-target::after { content:'✅'; position:absolute; top:-8px; right:-8px; font-size:12px; }
                </style>
                """
                
                for _, row in track_df.iterrows():
                    try:
                        dt = row.get('Data', '')
                        dt_str = dt.strftime('%d/%m/%Y') if hasattr(dt, 'strftime') else str(dt)[:10]
                        conf = row.get('Modelo 01', 'N/A')
                        liga = row.get('Liga', 'N/A')
                        placar = row.get('Placar', 'N/A')
                        odd = row.get('Odd', 0)
                        pl = row.get('P/L (R$)', 0)
                        gols = row.get('Gols', 0)
                        usada = row.get('Usada', 0)
                        melhor_g = row.get('Melhor G', 0)
                        odd_mg = row.get('Odd M.G.', '-')
                        pl_mg = row.get('P/L M.G.', '-')
                        fonte = row.get('Fonte odds', '-')
                        delta = row.get('Δ linha', '-')
                        analise = row.get('Análise da Entrada', '-')
                        
                        pl_color = "#38A169" if pl > 0 else ("#E53E3E" if pl < 0 else "#718096")
                        
                        # Matriz Asiática (O0,50 a O3,00)
                        matrix_html = ""
                        asian_cols = ['O0,50', 'O0,75', 'O1,00', 'O1,25', 'O1,50', 'O1,75', 'O2,00', 'O2,25', 'O2,50', 'O2,75', 'O3,00']
                        
                        # Converter 'usada' e 'melhor_g' para string compatível com a matriz
                        def fmt_line(v):
                            try: return f"{float(v):.2f}".replace('.', ',')
                            except: return str(v).replace('.', ',')

                        usada_str = fmt_line(usada)
                        melhor_str = fmt_line(melhor_g)

                        for col in asian_cols:
                            line_val = col[1:] # ex: '0,50'
                            val = str(row.get(col, '')).strip()
                            
                            is_bet = (line_val == usada_str)
                            is_best = (line_val == melhor_str)
                            
                            res_class = ""
                            if val == 'G': res_class = "g-res"
                            elif val == '½G': res_class = "hg-res"
                            elif val == 'P': res_class = "p-res"
                            elif val == '½R': res_class = "hr-res"
                            elif val == 'R': res_class = "r-res"
                            
                            # Lógica de marcação:
                            # Se for a melhor linha e for diferente da usada, marca em verde.
                            # Se for a usada, marca em azul claro.
                            cell_style = ""
                            if is_bet: cell_style = "bet-target"
                            if is_best and line_val != usada_str: cell_style = "best-target"

                            if val and val != 'nan':
                                matrix_html += f"""
                                <div class="asian-cell {cell_style}">
                                    <div class="asian-line">{line_val}</div>
                                    <div class="asian-res {res_class}">{val}</div>
                                </div>
                                """

                        track_cards += f"""
                        <div class="backtest-card">
                            <div class="backtest-header">
                                <span style="font-size:11px; font-weight:bold;">{dt_str} · {liga}</span>
                                <span style="background:{pl_color}; padding:2px 10px; border-radius:15px; font-size:12px; font-weight:bold;">P/L: R$ {pl:+.2f}</span>
                            </div>
                            <div class="backtest-body">
                                <div style="font-size:15px; font-weight:bold; color:#1A202C; margin-bottom:10px;">{conf} <span style="color:#2B6CB0;">({placar})</span></div>
                                
                                <div class="backtest-grid">
                                    <div class="backtest-item"><div class="backtest-label">Linha Usada</div><div class="backtest-value">{usada} (Odd: {odd})</div></div>
                                    <div class="backtest-item"><div class="backtest-label">Melhor G</div><div class="backtest-value">{melhor_g}</div></div>
                                    <div class="backtest-item"><div class="backtest-label">Δ Linha</div><div class="backtest-value">{delta}</div></div>
                                    <div class="backtest-item"><div class="backtest-label">Gols Total</div><div class="backtest-value">{gols}</div></div>
                                    
                                    <div class="backtest-item"><div class="backtest-label">Odd M.G.</div><div class="backtest-value">{odd_mg}</div></div>
                                    <div class="backtest-item"><div class="backtest-label">P/L M.G.</div><div class="backtest-value">{pl_mg}</div></div>
                                    <div class="backtest-item"><div class="backtest-label">Fonte Odds</div><div class="backtest-value">{fonte}</div></div>
                                    <div class="backtest-item"><div class="backtest-label">Analise</div><div class="backtest-value">{analise if pd.notna(analise) else '-'}</div></div>
                                </div>
                            </div>
                            <div class="asian-matrix">
                                <div style="font-size:9px; font-weight:bold; color:#718096; writing-mode:vertical-lr; text-transform:uppercase; margin-right:5px;">Matriz Asiática</div>
                                {matrix_html}
                            </div>
                        </div>
                        """
                    except:
                        pass
                
                components.html(track_cards, height=min(1200, 220 * len(track_df)), scrolling=True)
            else:
                st.info('A aba Backtest está vazia.')
        else:
            st.info('A aba Backtest não foi encontrada no arquivo Excel.')

    elif st.session_state.menu == 'Ranking':
        st.markdown('<div class="sim-header"><h3 style="margin:0; color:#2C5282;">📊 Radar Over — Equipes de Alta Confiança</h3><p style="margin:0; color:#4A5568; font-size:0.9rem;">Monitoramento dinâmico de frequência de gols, produção própria e confirmação (Linhas A a K, Linhas 4 a 66)</p></div>', unsafe_allow_html=True)
        
        xls = pd.ExcelFile(uploaded_file if uploaded_file else EXCEL_PATH)
        if 'Radar Over' in xls.sheet_names:
            df_raw_radar = pd.read_excel(uploaded_file if uploaded_file else EXCEL_PATH, sheet_name='Radar Over', header=None, skiprows=3, nrows=65, usecols='A:K')
            
            # Processar seções dinamicamente
            current_sec = "Geral"
            header_found = False
            radar_rows = []
            
            for _, r in df_raw_radar.iterrows():
                vals = [x for x in r.values if pd.notna(x)]
                if not vals:
                    continue
                txt = str(vals[0]).strip().upper()
                if "OVER 3" in txt:
                    current_sec = "Over 3 (Alto Teto)"
                    header_found = False
                    continue
                elif "OVER 2" in txt:
                    current_sec = "Over 2 (Perfil Ofensivo)"
                    header_found = False
                    continue
                elif "OVER 1" in txt:
                    current_sec = "Over 1 (Segurança)"
                    header_found = False
                    continue
                
                if not header_found and ("EQUIPE" in str(vals[0]).upper() or "FAIXA" in str(vals[0]).upper()):
                    header_found = True
                    continue
                
                if header_found and current_sec != "Geral":
                    if "EXCLUSÕES" in txt or "COMO USAR" in txt:
                        current_sec = "Geral"
                        header_found = False
                        continue
                    
                    radar_rows.append({
                        'Categoria': current_sec,
                        'Equipe': r.values[0],
                        'Liga': r.values[1],
                        'Jogos': r.values[2],
                        'Media_Propria': r.values[3],
                        'Media_Partida': r.values[4],
                        'Col_F': r.values[5],
                        'Col_G': r.values[6],
                        'Col_H': r.values[7],
                        'Col_I': r.values[8],
                        'Col_J': r.values[9],
                        'Nivel': r.values[10]
                    })
            
            df_radar = pd.DataFrame(radar_rows)
            if not df_radar.empty:
                r_col1, r_col2, r_col3 = st.columns([2, 1, 1])
                with r_col1:
                    search_rank = st.text_input("Filtrar Equipe no Radar...", placeholder="🔍 Digite o nome da equipe...")
                with r_col2:
                    cat_filter = st.selectbox("Filtrar Faixa", ["Todas as Faixas"] + sorted(df_radar['Categoria'].unique().tolist()))
                with r_col3:
                    liga_rank = st.selectbox("Filtrar por Liga", ["Todas as Ligas"] + sorted(df_radar['Liga'].dropna().unique().tolist()))
                
                if search_rank:
                    norm_s = normalize_text(search_rank)
                    df_radar = df_radar[df_radar['Equipe'].apply(lambda x: norm_s in normalize_text(str(x)))]
                if cat_filter != "Todas as Faixas":
                    df_radar = df_radar[df_radar['Categoria'] == cat_filter]
                if liga_rank != "Todas as Ligas":
                    df_radar = df_radar[df_radar['Liga'] == liga_rank]

                ranking_html = """
                <style>
                    .rank-table { width:100%; border-collapse:collapse; font-family:Inter,Arial,sans-serif; background:white; border-radius:12px; overflow:hidden; box-shadow:0 4px 6px rgba(0,0,0,0.05); }
                    .rank-table th { background:#1A365D; color:white; padding:12px 8px; text-align:left; font-size:10px; text-transform:uppercase; letter-spacing:0.5px; }
                    .rank-table td { padding:10px 8px; border-bottom:1px solid #EDF2F7; font-size:12px; color:#2D3748; }
                    .rank-table tr:hover { background:#F7FAFC; }
                    .pos-badge { background:#EBF8FF; color:#2B6CB0; font-weight:800; padding:2px 8px; border-radius:6px; font-size:11px; }
                    .index-val { font-weight:700; color:#3182CE; }
                    .over-val { font-weight:600; color:#38A169; }
                    .decisao-badge { padding:2px 6px; border-radius:4px; font-size:9px; font-weight:bold; text-transform:uppercase; }
                    .dec-sel { background:#C6F6D5; color:#22543D; }
                    .dec-out { background:#EDF2F7; color:#718096; }
                </style>
                <table class="rank-table">
                    <thead>
                        <tr>
                            <th>Faixa</th>
                            <th>Equipe</th>
                            <th>Liga</th>
                            <th>Jogos</th>
                            <th>Média Própria</th>
                            <th>Média Partida</th>
                            <th>Nível</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                
                for _, row in df_radar.iterrows():
                    try:
                        eq = str(row['Equipe'])
                        lg = str(row['Liga'])
                        jg = int(row['Jogos'])
                        mp = float(row['Media_Propria'])
                        mpt = float(row['Media_Partida'])
                        cat = str(row['Categoria'])
                        nv = str(row['Nivel'])
                        flag_img = get_flag_img(lg)
                        
                        nv_color = "#38A169" if nv.upper() == 'ELITE' else "#3182CE"
                        
                        ranking_html += f"""
                            <tr>
                                <td><span class="pos-badge">{cat}</span></td>
                                <td style="font-weight:700; display:flex; align-items:center;">{flag_img}{eq}</td>
                                <td style="color:#718096; font-size:10px;">{lg}</td>
                                <td>{jg}</td>
                                <td class="index-val">{mp:.2f}</td>
                                <td class="over-val">{mpt:.2f}</td>
                                <td><span style="color:white; background:{nv_color}; padding:2px 6px; border-radius:4px; font-weight:bold; font-size:10px;">{nv}</span></td>
                            </tr>
                        """
                    except:
                        continue
                
                ranking_html += "</tbody></table>"
                components.html(ranking_html, height=min(1500, 50 * len(df_radar) + 100), scrolling=True)
            else:
                st.info('Nenhum dado encontrado na aba Radar Over.')
        else:
            st.info('A aba Radar Over não foi encontrada no arquivo Excel.')
else:
    st.error("Erro ao carregar banco de dados.")
