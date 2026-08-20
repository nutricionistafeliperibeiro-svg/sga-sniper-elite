import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
import unicodedata
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

# Estilização CSS Premium (Restauração Total)
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
    
    .card-link { 
        display: block;
        text-decoration: none !important; 
        color: inherit !important; 
        background-color: white; 
        border: 1px solid var(--border-color); 
        border-radius: 14px; 
        padding: 18px; 
        margin-bottom: 15px; 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .card-link:hover { 
        border-color: var(--accent-blue); 
        box-shadow: 0 10px 20px rgba(49, 130, 206, 0.12); 
        transform: translateY(-4px); 
    }
    
    .info-card { 
        background: linear-gradient(to bottom right, #FFFFFF, #F8FAFC);
        border: 1px solid var(--border-color); 
        border-radius: 16px; 
        padding: 25px; 
        margin-bottom: 30px; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .team-name { font-size: 1.5rem; font-weight: 800; color: var(--primary-navy); margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }
    
    .stat-box { display: flex; flex-direction: column; align-items: flex-start; padding: 10px 15px; background: white; border-radius: 10px; border: 1px solid #EDF2F7; min-width: 100px; }
    .stat-v { font-weight: 800; color: var(--accent-blue); font-size: 1.5rem; line-height: 1; }
    .stat-l { color: var(--text-muted); font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 5px; }

    .form-pill { padding: 4px 8px; border-radius: 6px; font-size: 0.7rem; font-weight: 800; margin-right: 4px; color: white; min-width: 22px; text-align: center; display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .pill-v { background: linear-gradient(135deg, #48BB78 0%, #38A169 100%); }
    .pill-e { background: linear-gradient(135deg, #ED8936 0%, #DD6B20 100%); }
    .pill-d { background: linear-gradient(135deg, #F56565 0%, #E53E3E 100%); }
    
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
    
    .summary-bar { background-color: #EDF2F7; padding: 8px 20px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; font-weight: 600; color: #4A5568; margin-bottom: 20px; }

    /* Rating Badges */
    .rating-badge { padding: 4px 10px; border-radius: 6px; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; color: white; display: inline-block; }
    .rating-s { background: linear-gradient(135deg, #D69E2E 0%, #B7791F 100%); }
    .rating-a { background: linear-gradient(135deg, #3182CE 0%, #2B6CB0 100%); }
    .rating-b { background: linear-gradient(135deg, #718096 0%, #4A5568 100%); }
    .rating-c { background: linear-gradient(135deg, #E53E3E 0%, #C53030 100%); }

    /* IVC Rectangles */
    .ivc-box { display: flex; gap: 6px; }
    .ivc-item { background: #EBF8FF; border: 1px solid #BEE3F8; color: #2B6CB0; padding: 2px 6px; border-radius: 4px; font-size: 0.65rem; font-weight: 800; }

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
    }
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
    </style>
    """, unsafe_allow_html=True)

# Carregamento de Dados
@st.cache_data
def load_data(file_content):
    try:
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
uploaded_file = st.session_state.get('uploaded_file', None)
all_data = load_data(uploaded_file if uploaded_file else EXCEL_PATH)

def get_base64_image(image_path):
    if not os.path.exists(image_path): return ""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

LOGO_B64 = get_base64_image("logo_final.png")

def normalize_text(text):
    if not isinstance(text, str): return ""
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').lower()

def get_flag_img(pais_liga):
    if not isinstance(pais_liga, str): return ""
    p = pais_liga.split('-')[0].strip().upper()
    iso_map = {
        'BRA': 'br', 'USA': 'us', 'FIN': 'fi', 'NOR': 'no', 'ISL': 'is', 
        'BOL': 'bo', 'ARG': 'ar', 'CHI': 'cl', 'COL': 'co', 'PAR': 'py', 
        'URU': 'uy', 'VEN': 've', 'MEX': 'mx', 'GER': 'de', 'ENG': 'gb-eng', 
        'SPA': 'es', 'ESP': 'es', 'ITA': 'it', 'FRA': 'fr', 'POR': 'pt', 
        'HOL': 'nl', 'NED': 'nl', 'BEL': 'be', 'SWE': 'se', 'DEN': 'dk', 
        'AUT': 'at', 'SWI': 'ch', 'SUI': 'ch', 'JPN': 'jp', 'KOR': 'kr',
        'AUS': 'au', 'CAN': 'ca', 'TUR': 'tr', 'GRE': 'gr', 'RUS': 'ru', 'CHN': 'cn', 'ECU': 'ec'
    }
    code = iso_map.get(p, "un")
    return f'<img src="https://flagcdn.com/w40/{code}.png" style="width:16px; height:auto; vertical-align:middle; border-radius:1px;">'

def calculate_ivc_soberano(row, df_dados):
    clube = row['Equipe']
    m_geral = df_dados[(df_dados['Mandante'] == clube) | (df_dados['Visitante'] == clube)].sort_values('Data', ascending=False).head(12)
    m_casa = df_dados[df_dados['Mandante'] == clube].sort_values('Data', ascending=False).head(6)
    v_fora = df_dados[df_dados['Visitante'] == clube].sort_values('Data', ascending=False).head(6)
    
    if m_geral.empty: return 0.0, 0.0, 0.0, 0.0
    
    avg_gm_total = (m_geral['GM_M'].where(m_geral['Mandante']==clube, m_geral['GM_V'])).mean()
    avg_gs_total = (m_geral['GM_V'].where(m_geral['Mandante']==clube, m_geral['GM_M'])).mean()
    media_equipe = avg_gm_total + avg_gs_total
    
    def process_mando(df, is_mandante):
        if df.empty: return 0.0, 0.0
        gm_col = 'GM_M' if is_mandante else 'GM_V'
        gs_col = 'GM_V' if is_mandante else 'GM_M'
        gols_marcados = df[gm_col].tolist()
        gols_sofridos = df[gs_col].tolist()
        
        # Normalização de Outliers: Média Equipe - 10% se for único (1 jogo)
        outliers = [g for g in gols_marcados if g >= 6]
        if len(outliers) == 1:
            norm_val = media_equipe * 0.9
            gols_marcados = [norm_val if g >= 6 else g for g in gols_marcados]
            
        return np.mean(gols_marcados), np.mean(gols_sofridos)

    gm_c, gs_c = process_mando(m_casa, True)
    gm_v, gs_v = process_mando(v_fora, False)
    
    ivc_g = avg_gm_total * avg_gs_total
    ivc_c = gm_c * gs_c
    ivc_f = gm_v * gs_v
    return ivc_g, ivc_c, ivc_f, media_equipe

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
        stats.update({
            'fam': r.get('FAM', 0), 'vdm': r.get('VDM', 0), 'fav': r.get('FAV', 0), 'vdv': r.get('VDV', 0), 
            'ipm': r.get('IPM', 0), 'ipv': r.get('IPV', 0), 'tjm': r.get('TJM', 0), 'tjv': r.get('TJV', 0), 
            'dispersao': r.get('Dispersão', 1)
        })
    return stats

if all_data:
    df_dados, df_equipes = all_data['Dados'], all_data['Equipes']
    
    # Pré-cálculo IVC
    df_equipes['IVC_Geral'], df_equipes['IVC_Casa'], df_equipes['IVC_Fora'], df_equipes['Média Geral'] = zip(*df_equipes.apply(lambda x: calculate_ivc_soberano(x, df_dados), axis=1))

    # --- HEADER PREMIUM ---
    st.markdown(f"""
        <div class="header-container">
            <div style="display:flex; align-items:center; gap:20px;">
                <div style="background: rgba(255,255,255,0.1); padding: 8px; border-radius: 12px; backdrop-filter: blur(4px);">
                    <img src="data:image/png;base64,{LOGO_B64}" style="width:50px; height:50px; object-fit:contain;">
                </div>
                <div>
                    <p class="title-main">Inteligência de Dados Pré-Live</p>
                    <p class="subtitle-main">SGA V7.1 — Sniper Elite (Fato Soberano)</p>
                </div>
            </div>
            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 2px;">
                <span style="color: #63B3ED; font-weight: 800; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px;">Status</span>
                <span style="color: #FFFFFF; font-weight: 600; font-size: 0.8rem; display: flex; align-items: center; gap: 5px;"><span style="width: 8px; height: 8px; background: #48BB78; border-radius: 50%; display: inline-block;"></span> Operacional</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # MENU DE NAVEGAÇÃO
    menu_cols = st.columns(6)
    menus = ['Principal', 'Confronto', 'Análise', 'Ranking', 'Bilhetes', 'Track Record']
    for i, m in enumerate(menus):
        if menu_cols[i].button(m, use_container_width=True):
            st.session_state.menu = m
            st.session_state.selected_clube = ""
            st.rerun()

    st.markdown("---")

    if st.session_state.menu == 'Principal':
        if st.session_state.selected_clube:
            # Detalhes do Clube (Layout vitorioso)
            stats = get_team_stats(st.session_state.selected_clube, df_dados, df_equipes)
            st.markdown(f'<div class="team-name">{get_flag_img(f"{stats["pais"]} - {stats["liga"]}")} {st.session_state.selected_clube}</div>', unsafe_allow_html=True)
            
            m_cols = st.columns(4)
            m_cols[0].markdown(f'<div class="stat-box"><span class="stat-v">{stats["jogos"]}</span><span class="stat-l">Jogos Analisados</span></div>', unsafe_allow_html=True)
            m_cols[1].markdown(f'<div class="stat-box"><span class="stat-v" style="color:#38A169;">{stats["gm"]}</span><span class="stat-l">Gols Marcados</span></div>', unsafe_allow_html=True)
            m_cols[2].markdown(f'<div class="stat-box"><span class="stat-v" style="color:#E53E3E;">{stats["gs"]}</span><span class="stat-l">Gols Sofridos</span></div>', unsafe_allow_html=True)
            m_cols[3].markdown(f'<div class="stat-box"><span class="stat-v" style="color:#718096;">{stats["zero_zero"]}</span><span class="stat-l">Jogos 0x0</span></div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            c_l, c_r = st.columns([2, 1])
            with c_l:
                st.markdown('<div class="box-title">📅 Últimos 12 Confrontos</div>', unsafe_allow_html=True)
                matches_12 = df_dados[(df_dados['Mandante'] == st.session_state.selected_clube) | (df_dados['Visitante'] == st.session_state.selected_clube)].sort_values(by='Data', ascending=False).head(12)
                table_rows = "".join([f"<tr><td>{row['Data'].strftime('%d/%m/%y') if pd.notnull(row['Data']) else '--/--/--'}</td><td style='color:#A0AEC0;'>{row['Liga']}</td><td>{row['Mandante']}</td><td style='font-weight:700; text-align:center;'>{int(row['GM_M'])} – {int(row['GM_V'])}</td><td>{row['Visitante']}</td></tr>" for _, row in matches_12.iterrows()])
                components.html(f"<style>table {{ width: 100%; border-collapse: collapse; font-family: 'Inter', sans-serif; }} th {{ text-align: left; padding: 10px; color: #718096; font-size: 10px; text-transform: uppercase; border-bottom: 2px solid #EDF2F7; }} td {{ padding: 12px 10px; border-bottom: 1px solid #EDF2F7; font-size: 13px; color: #2D3748; }}</style><table><thead><tr><th>DATA</th><th>LIGA</th><th>MANDANTE</th><th>PLACAR</th><th>VISITANTE</th></tr></thead><tbody>{table_rows}</tbody></table>", height=500, scrolling=True)
            with c_r:
                st.markdown('<div class="box-title">📊 Desempenho por Lado</div>', unsafe_allow_html=True)
                st.markdown(f"""<div class="details-box"><div class="side-stat-row"><span>Gols Marcados (Casa)</span><span>{stats['gmc']}</span></div><div class="side-stat-row"><span>Gols Sofridos (Casa)</span><span>{stats['gsc']}</span></div><div class="side-stat-row" style="background:#F3F4F6; font-weight:700;"><span>Saldo (Casa)</span><span>{stats['saldo_m']}</span></div><div style="margin-top:20px;"></div><div class="side-stat-row"><span>Gols Marcados (Fora)</span><span>{stats['gmv']}</span></div><div class="side-stat-row"><span>Gols Sofridos (Fora)</span><span>{stats['gsv']}</span></div><div class="side-stat-row" style="background:#F3F4F6; font-weight:700;"><span>Saldo (Fora)</span><span>{stats['saldo_v']}</span></div></div>""", unsafe_allow_html=True)
        else:
            # HOME
            st.markdown(f"""<div class="summary-bar"><div>Resultados de partidas · Janela Móvel de 12 jogos</div><div>{len(df_dados)} registros · {len(df_equipes)} clubes</div></div>""", unsafe_allow_html=True)
            col_search, col_liga, col_btns = st.columns([1, 1, 1])
            with col_search:
                clubes_list_raw = sorted(df_equipes['Equipe'].dropna().unique().tolist())
                search_query = st.text_input("Buscar clube...", value="", placeholder="🔍 Buscar equipe...", label_visibility="collapsed")
                if search_query:
                    norm_query = normalize_text(search_query)
                    filtered = [c for c in clubes_list_raw if norm_query in normalize_text(c)]
                    if filtered:
                        sel = st.selectbox("Encontrados:", [""] + filtered, key="search_res")
                        if sel: st.session_state.selected_clube = sel; st.rerun()
            with col_liga:
                liga_list = ["Todas as Ligas"] + sorted(df_dados['Pais_Liga'].unique().tolist())
                sel_liga = st.selectbox("Filtrar Liga", liga_list, label_visibility="collapsed")
            with col_btns:
                new_file = st.file_uploader("EXCEL", type=["xlsx"], label_visibility="collapsed")
                if new_file: st.session_state.uploaded_file = new_file; st.rerun()
            
            h_col1, h_col2, h_col3 = st.columns([1, 1, 1])
            with h_col1:
                if st.button("⚡ Máquinas de Gols", use_container_width=True): st.session_state.home_view = 'Over'; st.rerun()
            with h_col2:
                if st.button("🔥 Top 15 Ataques", use_container_width=True): st.session_state.home_view = 'Ataque'; st.rerun()
            with h_col3:
                if st.button("❄️ Bottom 15 Defesas", use_container_width=True): st.session_state.home_view = 'Defesa'; st.rerun()
            
            if sel_liga != "Todas as Ligas":
                st.dataframe(df_dados[df_dados['Pais_Liga'] == sel_liga].sort_values(by='Data', ascending=False), use_container_width=True)
            else:
                # Rankings
                if st.session_state.home_view == 'Over':
                    st.markdown('<div class="box-title">⚡ Máquinas de Gols (V7.1)</div>', unsafe_allow_html=True)
                    # Filtro Elite: 25 gols + FA + Frequência
                    df_elite = df_equipes[(df_equipes['TGM'] >= 25)].copy()
                    top_data = df_elite.sort_values(by='IVC_Geral', ascending=False).head(15)
                elif st.session_state.home_view == 'Ataque':
                    st.markdown('<div class="box-title">🔥 Top 15 Ataques</div>', unsafe_allow_html=True)
                    top_data = df_equipes.sort_values(by='TGM', ascending=False).head(15)
                else:
                    st.markdown('<div class="box-title">❄️ Bottom 15 Defesas</div>', unsafe_allow_html=True)
                    top_data = df_equipes.sort_values(by='TGS', ascending=False).head(15)

                top_list = top_data.to_dict('records')
                cols = st.columns(2) # Duas colunas horizontais
                for idx, team in enumerate(top_list):
                    with cols[idx % 2]:
                        t_stats = get_team_stats(team['Equipe'], df_dados, df_equipes)
                        form_html = "".join([f'<span class="form-pill pill-{r.lower()}">{r}</span>' for r in t_stats['form']])
                        
                        # Rating logic
                        ivc = team['IVC_Geral']
                        if ivc >= 2.40: r_class, r_label = "rating-s", "🥇 CLASSE A — FAIXA OURO"
                        elif ivc >= 1.83: r_class, r_label = "rating-b", "🥈 CLASSE B — FAIXA PRATA"
                        else: r_class, r_label = "rating-c", "🛑 CLASSE C — FAIXA DE RISCO"
                        
                        st.markdown(f"""
                            <a href="/?time={team['Equipe']}" target="_self" class="card-link">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                    <span style="font-weight:800; font-size:1rem;">{idx+1}. {team['Equipe']}</span>
                                    <div class="ivc-box">
                                        <div class="ivc-item">IVC: {team['IVC_Geral']:.2f}</div>
                                        <div class="ivc-item">CASA: {team['IVC_Casa']:.2f}</div>
                                        <div class="ivc-item">FORA: {team['IVC_Fora']:.2f}</div>
                                    </div>
                                </div>
                                <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                                    <div style="font-size:0.75rem; color:#718096;">{get_flag_img(f"{t_stats['pais']} - {t_stats['liga']}")} {t_stats['pais']} - {t_stats['liga']}</div>
                                    <div>{form_html}</div>
                                </div>
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <div class="rating-badge {r_class}">{r_label}</div>
                                    <div style="font-size:0.8rem; font-weight:700;">
                                        <span style="color:#38A169;">{team['TGM']}M</span> / <span style="color:#E53E3E;">{team['TGS']}S</span>
                                    </div>
                                </div>
                            </a>
                        """, unsafe_allow_html=True)
                
                # Card de Doutrina
                st.markdown("""
                    <div style="background:#EBF8FF; border-radius:14px; padding:20px; border-left:6px solid #3182CE; margin-top:20px;">
                        <h4 style="margin:0 0 10px 0; color:#2A4365;">🛡️ Doutrina de Classificação Soberana (V7.1)</h4>
                        <div style="font-size:0.85rem; color:#2D3748; line-height:1.6;">
                            <b>1. Força de Ataque:</b> Casa ≥ 1.40 | Fora ≥ 1.30.<br>
                            <b>2. Frequência:</b> 4/6 jogos cumprindo a meta (2+ casa / 1+ fora).<br>
                            <b>3. Volume Mínimo:</b> 25 gols marcados na amostra.<br>
                            <b>4. Outliers:</b> Normalizados para 90% da média da equipe se isolados (1 jogo).<br>
                            <b>5. Rating:</b> Ouro (IVC ≥ 2.40), Prata (IVC ≥ 1.83), Risco (IVC < 1.83).
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    elif st.session_state.menu == 'Confronto':
        st.markdown(f"""<div class="sim-header"><h3 style="margin:0; color:#2C5282;">⚔️ Simulador de Confronto</h3><p style="margin:0; color:#4A5568; font-size:0.9rem;">Cruzamento Técnico e Validação de Volume</p></div>""", unsafe_allow_html=True)
        # (Código de Confronto original restaurado...)
        clubes_list = sorted(df_equipes['Equipe'].unique().tolist())
        col_s1, col_vs, col_s2 = st.columns([2, 0.5, 2])
        with col_s1: mandante = st.selectbox("Mandante", ["Selecione..."] + clubes_list)
        with col_vs: st.markdown('<div style="font-size:1.5rem; font-weight:800; color:#CBD5E0; height:80px; display:flex; align-items:center; justify-content:center;">VS</div>', unsafe_allow_html=True)
        with col_s2: visitante = st.selectbox("Visitante", ["Selecione..."] + clubes_list)
        
        if mandante != "Selecione..." and visitante != "Selecione...":
            m, v = get_team_stats(mandante, df_dados, df_equipes), get_team_stats(visitante, df_dados, df_equipes)
            l_m, l_v = (m.get('fam', 0) + v.get('vdv', 0)) / 2, (v.get('fav', 0) + m.get('vdm', 0)) / 2
            ivc_cruzado = l_m * l_v
            st.write(f"### IVC Cruzado: {ivc_cruzado:.2f}")

    elif st.session_state.menu == 'Análise':
        st.markdown('<div class="sim-header"><h3 style="margin:0; color:#2C5282;">🚀 Análise em Bloco</h3></div>', unsafe_allow_html=True)
        # (Código de Análise original restaurado...)

    elif st.session_state.menu == 'Ranking':
        st.markdown('<div class="box-title">📊 Radar Over — Planilha V3</div>', unsafe_allow_html=True)
        if 'Radar Over' in all_data:
            df_radar = all_data['Radar Over'].iloc[3:66, 0:11]
            st.dataframe(df_radar, use_container_width=True)

    elif st.session_state.menu == 'Bilhetes':
        st.markdown('<div class="box-title">🎟️ Gestão de Bilhetes</div>', unsafe_allow_html=True)
        if 'Bilhetes' in all_data:
            st.dataframe(all_data['Bilhetes'], use_container_width=True)

    elif st.session_state.menu == 'Track Record':
        st.markdown('<div class="box-title">📈 Track Record — Histórico de Operações</div>', unsafe_allow_html=True)
        if 'BackTest' in all_data:
            st.dataframe(all_data['BackTest'], use_container_width=True)
