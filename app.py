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

# Estilização CSS Premium (Restauração Milimétrica)
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
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        text-decoration: none !important; 
        color: inherit !important; 
        background-color: white; 
        border: 1px solid var(--border-color); 
        border-radius: 14px; 
        padding: 15px; 
        margin-bottom: 15px; 
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        height: 165px; /* Formato original retangular/quadrado */
    }
    .card-link:hover { 
        border-color: var(--accent-blue); 
        box-shadow: 0 10px 20px rgba(49, 130, 206, 0.12); 
        transform: translateY(-4px); 
    }
    
    .team-name { font-size: 1.5rem; font-weight: 800; color: var(--primary-navy); margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }
    .stat-box { display: flex; flex-direction: column; align-items: flex-start; padding: 10px 15px; background: white; border-radius: 10px; border: 1px solid #EDF2F7; min-width: 100px; }
    .stat-v { font-weight: 800; color: var(--accent-blue); font-size: 1.5rem; line-height: 1; }
    .stat-l { color: var(--text-muted); font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 5px; }
    .form-pill { padding: 4px 8px; border-radius: 6px; font-size: 0.7rem; font-weight: 800; margin-right: 4px; color: white; min-width: 22px; text-align: center; display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .pill-v { background: linear-gradient(135deg, #48BB78 0%, #38A169 100%); }
    .pill-e { background: linear-gradient(135deg, #ED8936 0%, #DD6B20 100%); }
    .pill-d { background: linear-gradient(135deg, #F56565 0%, #E53E3E 100%); }
    
    .box-title { font-size: 0.9rem; font-weight: 800; color: var(--primary-navy); margin-bottom: 20px; text-transform: uppercase; display: flex; align-items: center; gap: 10px; }
    .box-title::before { content: ""; display: block; width: 4px; height: 18px; background: var(--accent-blue); border-radius: 2px; }
    .details-box { background-color: white; border: 1px solid var(--border-color); border-radius: 14px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .side-stat-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #F1F5F9; font-size: 0.9rem; font-weight: 500; }
    
    .summary-bar { background-color: #EDF2F7; padding: 8px 20px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; font-size: 0.75rem; font-weight: 600; color: #4A5568; margin-bottom: 20px; }

    /* Rating Badges Suaves */
    .rating-badge { padding: 2px 6px; border-radius: 4px; font-size: 0.55rem; font-weight: 800; text-transform: uppercase; color: white; display: inline-block; }
    .rating-s { background: #D69E2E; } 
    .rating-a { background: #3182CE; }
    .rating-b { background: #A0AEC0; }
    .rating-c { background: #E53E3E; }

    /* IVC Rectangles */
    .ivc-box { display: flex; gap: 4px; }
    .ivc-item { background: #EBF8FF; border: 1px solid #BEE3F8; color: #2B6CB0; padding: 1px 4px; border-radius: 3px; font-size: 0.6rem; font-weight: 800; }
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
    return f'<img src="https://flagcdn.com/w40/{code}.png" style="width:14px; height:auto; vertical-align:middle;">'

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
        outliers = [g for g in gols_marcados if g >= 6]
        if len(outliers) == 1:
            norm_val = media_equipe * 0.9
            gols_marcados = [norm_val if g >= 6 else g for g in gols_marcados]
        return np.mean(gols_marcados), df[gs_col].mean()
    gm_c, gs_c = process_mando(m_casa, True)
    gm_v, gs_v = process_mando(v_fora, False)
    return avg_gm_total * avg_gs_total, gm_c * gs_c, gm_v * gs_v, media_equipe

def get_team_stats(team_name, df_dados, df_equipes):
    all_matches = df_dados[(df_dados['Mandante'] == team_name) | (df_dados['Visitante'] == team_name)].sort_values(by='Data', ascending=False)
    team_row = df_equipes[df_equipes['Equipe'] == team_name]
    gmc, gsc, gmv, gsv = 0, 0, 0, 0
    form = []
    for _, row in all_matches.iterrows():
        m, v = int(row['GM_M']), int(row['GM_V'])
        is_mandante = row['Mandante'] == team_name
        if is_mandante:
            gmc += m; gsc += v
            res = 'V' if m > v else ('E' if m == v else 'D')
            if len(form) < 5: form.append(res)
        else:
            gmv += v; gsv += m
            res = 'V' if v > m else ('E' if v == m else 'D')
            if len(form) < 5: form.append(res)
    stats = {'jogos': len(all_matches), 'gm': gmc + gmv, 'gs': gsc + gsv, 'gmc': gmc, 'gsc': gsc, 'gmv': gmv, 'gsv': gsv, 'saldo_m': gmc - gsc, 'saldo_v': gmv - gsv, 'form': form, 'liga': all_matches.iloc[0]['Liga'] if not all_matches.empty else "N/A", 'pais': all_matches.iloc[0]['País'] if not all_matches.empty else "N/A"}
    if not team_row.empty:
        r = team_row.iloc[0].fillna(0)
        stats.update({'fam': r.get('FAM', 0), 'vdm': r.get('VDM', 0), 'fav': r.get('FAV', 0), 'vdv': r.get('VDV', 0), 'tjm': r.get('TJM', 0), 'tjv': r.get('TJV', 0)})
    return stats

if all_data:
    df_dados, df_equipes = all_data['Dados'], all_data['Equipes']
    df_equipes['IVC_Geral'], df_equipes['IVC_Casa'], df_equipes['IVC_Fora'], df_equipes['Média Geral'] = zip(*df_equipes.apply(lambda x: calculate_ivc_soberano(x, df_dados), axis=1))

    st.markdown(f"""<div class="header-container"><div style="display:flex; align-items:center; gap:20px;"><div style="background: rgba(255,255,255,0.1); padding: 8px; border-radius: 12px; backdrop-filter: blur(4px);"><img src="data:image/png;base64,{LOGO_B64}" style="width:50px; height:50px; object-fit:contain;"></div><div><p class="title-main">Inteligência de Dados Pré-Live</p><p class="subtitle-main">SGA V7.1 — Sniper Elite (Fato Soberano)</p></div></div><div style="display: flex; flex-direction: column; align-items: flex-end; gap: 2px;"><span style="color: #63B3ED; font-weight: 800; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px;">Status</span><span style="color: #FFFFFF; font-weight: 600; font-size: 0.8rem; display: flex; align-items: center; gap: 5px;"><span style="width: 8px; height: 8px; background: #48BB78; border-radius: 50%; display: inline-block;"></span> Operacional</span></div></div>""", unsafe_allow_html=True)

    menu_cols = st.columns(6)
    menus = ['Principal', 'Confronto', 'Análise', 'Ranking', 'Bilhetes', 'Track Record']
    for i, m in enumerate(menus):
        if menu_cols[i].button(m, use_container_width=True):
            st.session_state.menu = m; st.session_state.selected_clube = ""; st.rerun()

    st.markdown("---")

    if st.session_state.menu == 'Principal':
        if st.session_state.selected_clube:
            stats = get_team_stats(st.session_state.selected_clube, df_dados, df_equipes)
            st.markdown(f'<div class="team-name">{get_flag_img(f"{stats["pais"]} - {stats["liga"]}")} {st.session_state.selected_clube}</div>', unsafe_allow_html=True)
            m_cols = st.columns(4)
            m_cols[0].markdown(f'<div class="stat-box"><span class="stat-v">{stats["jogos"]}</span><span class="stat-l">Jogos Analisados</span></div>', unsafe_allow_html=True)
            m_cols[1].markdown(f'<div class="stat-box"><span class="stat-v" style="color:#38A169;">{stats["gm"]}</span><span class="stat-l">Gols Marcados</span></div>', unsafe_allow_html=True)
            m_cols[2].markdown(f'<div class="stat-box"><span class="stat-v" style="color:#E53E3E;">{stats["gs"]}</span><span class="stat-l">Gols Sofridos</span></div>', unsafe_allow_html=True)
            m_cols[3].markdown(f'<div class="stat-box"><span class="stat-v" style="color:#718096;">{stats["gmc"]-stats["gsc"]}</span><span class="stat-l">Saldo</span></div>', unsafe_allow_html=True)
        else:
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
                if st.session_state.home_view == 'Over':
                    st.markdown('<div class="box-title">⚡ Máquinas de Gols (V7.1)</div>', unsafe_allow_html=True)
                    top_data = df_equipes[(df_equipes['TGM'] >= 25)].sort_values(by='IVC_Geral', ascending=False).head(15)
                elif st.session_state.home_view == 'Ataque':
                    st.markdown('<div class="box-title">🔥 Top 15 Ataques</div>', unsafe_allow_html=True)
                    top_data = df_equipes.sort_values(by='TGM', ascending=False).head(15)
                else:
                    st.markdown('<div class="box-title">❄️ Bottom 15 Defesas</div>', unsafe_allow_html=True)
                    top_data = df_equipes.sort_values(by='TGS', ascending=False).head(15)

                top_list = top_data.to_dict('records')
                cols = st.columns(3) # Restaurando 3 colunas (Formato Quadrado)
                for idx, team in enumerate(top_list):
                    with cols[idx % 3]:
                        t_stats = get_team_stats(team['Equipe'], df_dados, df_equipes)
                        form_html = "".join([f'<span class="form-pill pill-{r.lower()}">{r}</span>' for r in t_stats['form']])
                        ivc = team['IVC_Geral']
                        if ivc >= 2.40: r_class, r_label = "rating-s", "🥇 OURO"
                        elif ivc >= 1.83: r_class, r_label = "rating-b", "🥈 PRATA"
                        else: r_class, r_label = "rating-c", "🛑 RISCO"
                        
                        st.markdown(f"""
                            <a href="/?time={team['Equipe']}" target="_self" class="card-link">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <span style="font-weight:800; font-size:0.85rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:140px;">{idx+1}. {team['Equipe']}</span>
                                    <div class="rating-badge {r_class}">{r_label}</div>
                                </div>
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <div style="font-size:0.65rem; color:#718096;">{get_flag_img(f"{t_stats['pais']} - {t_stats['liga']}")} {t_stats['pais']}</div>
                                    <div>{form_html}</div>
                                </div>
                                <div class="ivc-box">
                                    <div class="ivc-item">IVC: {team['IVC_Geral']:.2f}</div>
                                    <div class="ivc-item">C: {team['IVC_Casa']:.2f}</div>
                                    <div class="ivc-item">F: {team['IVC_Fora']:.2f}</div>
                                </div>
                                <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.75rem; font-weight:700; border-top:1px solid #EDF2F7; padding-top:8px;">
                                    <span style="color:#38A169;">{int(team['TGM'])}M</span>
                                    <span style="color:#E53E3E;">{int(team['TGS'])}S</span>
                                </div>
                            </a>
                        """, unsafe_allow_html=True)
                
                st.markdown("""<div style="background:#EBF8FF; border-radius:14px; padding:20px; border-left:6px solid #3182CE; margin-top:20px;"><h4 style="margin:0 0 10px 0; color:#2A4365;">🛡️ Doutrina de Classificação Soberana (V7.1)</h4><div style="font-size:0.85rem; color:#2D3748; line-height:1.6;"><b>1. Força de Ataque:</b> Casa ≥ 1.40 | Fora ≥ 1.30.<br><b>2. Frequência:</b> 4/6 jogos cumprindo a meta (2+ casa / 1+ fora).<br><b>3. Volume Mínimo:</b> 25 gols marcados na amostra.<br><b>4. Outliers:</b> Normalizados para 90% da média da equipe se isolados (1 jogo).<br><b>5. Rating:</b> Ouro (IVC ≥ 2.40), Prata (IVC ≥ 1.83), Risco (IVC < 1.83).</div></div>""", unsafe_allow_html=True)

    elif st.session_state.menu == 'Confronto':
        st.markdown(f"""<div class="sim-header"><h3 style="margin:0; color:#2C5282;">⚔️ Simulador de Confronto</h3></div>""", unsafe_allow_html=True)
        # Código simplificado para evitar KeyErrors
        st.info("Selecione as equipes para simular o confronto técnico.")

    elif st.session_state.menu == 'Ranking':
        if 'Radar Over' in all_data: st.dataframe(all_data['Radar Over'].iloc[3:66, 0:11], use_container_width=True)

    elif st.session_state.menu == 'Bilhetes':
        if 'Bilhetes' in all_data: st.dataframe(all_data['Bilhetes'], use_container_width=True)

    elif st.session_state.menu == 'Track Record':
        if 'BackTest' in all_data: st.dataframe(all_data['BackTest'], use_container_width=True)
