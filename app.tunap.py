import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from supabase import create_client, Client

# Configuração da página
st.set_page_config(
    page_title="TUNAP | Campanha Mercosul",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Configuração de Conexão com o Supabase
# -----------------------------------------------------------------------------
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_supabase()

# -----------------------------------------------------------------------------
# Estilização CSS Customizada (Light Mode Estrito, Hover e Larguras Fixas)
# -----------------------------------------------------------------------------
st.markdown("""
    <style>
    :root {
        color-scheme: light !important;
    }
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF !important;
        color: #1F2937 !important;
    }

    [data-testid="stSidebar"] [data-testid="stImage"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
    }
    
    [data-testid="stSidebar"] img {
        max-width: 80px !important;
        height: auto !important;
        margin: 0 auto !important;
        display: block !important;
        object-fit: contain !important;
    }
    
    div[data-baseweb="select"] > div {
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 8px !important;
        background-color: #F8FAFC !important;
    }
    
    .table-responsive {
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        margin-bottom: 1.5rem;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
    }
    table.custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        color: #1F2937;
    }
    table.custom-table th {
        background-color: #F1F5F9;
        font-weight: 700;
        border: 1px solid #CBD5E1;
        padding: 10px 12px;
        text-align: center;
    }
    table.custom-table td {
        border: 1px solid #E2E8F0;
        padding: 8px 12px;
        text-align: center;
        transition: background-color 0.2s ease;
    }
    table.custom-table tr:hover td {
        background-color: #E0F2FE !important;
        font-weight: 600;
    }
    
    .wpp-box {
        background-color: #F8FAFC;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 12px;
        font-family: monospace;
        font-size: 13px;
        white-space: pre-wrap !important;
        word-break: break-word !important;
        overflow-x: hidden !important;
        color: #0F172A;
    }

    .header-subtitle {
        background-color: #EFF6FF;
        border-left: 4px solid #2563EB;
        padding: 10px 15px;
        border-radius: 4px;
        font-size: 16px;
        font-weight: 600;
        color: #1E40AF;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Funções de Banco de Dados com Paginação Otimizada
# -----------------------------------------------------------------------------
def clear_database():
    try:
        supabase.table("vendas").delete().neq("id", 0).execute()
        supabase.table("passagens").delete().neq("id", 0).execute()
        supabase.table("uploads_log").delete().neq("id", 0).execute()
        return True
    except Exception as e:
        st.error(f"Erro ao limpar banco: {e}")
        return False

def load_data_from_db():
    """Carrega todas as vendas e passagens do Supabase usando paginação em lotes de 1000."""
    try:
        # Paginação para a tabela de Vendas
        all_vendas = []
        batch_size = 1000
        offset = 0
        while True:
            res_v = supabase.table("vendas").select("*").range(offset, offset + batch_size - 1).execute()
            data_v = res_v.data if res_v.data else []
            all_vendas.extend(data_v)
            if len(data_v) < batch_size:
                break
            offset += batch_size

        df_vendas = pd.DataFrame(all_vendas) if all_vendas else pd.DataFrame(columns=['id', 'empresa', 'consultor', 'nf_numero', 'nf_item_cod', 'prod_ref', 'sku', 'descricao', 'qtde', 'data_venda'])

        # Paginação para a tabela de Passagens
        all_pass = []
        offset = 0
        while True:
            res_p = supabase.table("passagens").select("*").range(offset, offset + batch_size - 1).execute()
            data_p = res_p.data if res_p.data else []
            all_pass.extend(data_p)
            if len(data_p) < batch_size:
                break
            offset += batch_size

        df_pass = pd.DataFrame(all_pass) if all_pass else pd.DataFrame(columns=['id', 'empresa', 'consultor', 'os_codigo', 'os_numero', 'data_passagem'])

        return df_vendas, df_pass
    except Exception as e:
        st.error(f"Erro ao carregar dados do Supabase: {e}")
        return pd.DataFrame(), pd.DataFrame()

def get_db_status():
    try:
        df_v, df_p = load_data_from_db()
        min_v, max_v = "N/A", "N/A"
        if not df_v.empty and 'data_venda' in df_v.columns:
            valid_v = pd.to_datetime(df_v['data_venda'], format='%d/%m/%Y', errors='coerce').dropna()
            if not valid_v.empty:
                min_v = valid_v.min().strftime('%d/%m/%Y')
                max_v = valid_v.max().strftime('%d/%m/%Y')

        min_p, max_p = "N/A", "N/A"
        if not df_p.empty and 'data_passagem' in df_p.columns:
            valid_p = pd.to_datetime(df_p['data_passagem'], format='%d/%m/%Y', errors='coerce').dropna()
            if not valid_p.empty:
                min_p = valid_p.min().strftime('%d/%m/%Y')
                max_p = valid_p.max().strftime('%d/%m/%Y')

        res_log = supabase.table("uploads_log").select("data_upload").order("id", desc=True).limit(1).execute()
        ultimo_upload = "Nenhum upload"
        if res_log.data:
            ultimo_upload = res_log.data[0]['data_upload']

        return min_v, max_v, min_p, max_p, ultimo_upload
    except Exception:
        return "N/A", "N/A", "N/A", "N/A", "Nenhum upload"

# -----------------------------------------------------------------------------
# Dicionários e Mapeamentos
# -----------------------------------------------------------------------------
PRODUCT_MAP = {
    'CARE0 40001': {'desc': 'Espuma Limpeza', 'sku': '109'},
    'TU109': {'desc': 'Espuma Limpeza', 'sku': '109'},
    'CARE0 40102': {'desc': 'Lubrificante Teflon', 'sku': '104'},
    'TU104': {'desc': 'Lubrificante Teflon', 'sku': '104'},
    'CARE0 40201': {'desc': 'Desengraxante Universal', 'sku': '115'},
    'TU115': {'desc': 'Desengraxante Universal', 'sku': '115'},
    'CARE0 40501': {'desc': 'Limpeza Preventiva DPF', 'sku': '126'},
    'TU126': {'desc': 'Limpeza Preventiva DPF', 'sku': '126'},
    'CARE0 40701': {'desc': 'Evaporador', 'sku': '994'},
    'CARE0 40702': {'desc': 'Sanitizador AC', 'sku': '996'},
    'TU996': {'desc': 'Sanitizador AC', 'sku': '996'},
    'CARE0 40703': {'desc': 'Odorizante', 'sku': '599'},
    'TU599': {'desc': 'Odorizante', 'sku': '599'},
    'CARE0 42501': {'desc': 'Tratamento FLEX', 'sku': '939'},
    'CARE0 42502': {'desc': 'Tratamento DIESEL', 'sku': '984'},
    'CARE0 43501': {'desc': 'Limp. Interna Motor', 'sku': '957'},
    'CARE0 44902': {'desc': 'Lubrificação Feixe de Molas', 'sku': '299'},
    'TU299': {'desc': 'Lubrificação Feixe de Molas', 'sku': '299'},
    'CARE0 44904': {'desc': 'Kit Lubrificação', 'sku': '2000'},
    'CARE0 44905': {'desc': 'Veda Pneu', 'sku': '711'},
    'TU047658': {'desc': 'Veda Pneu', 'sku': '711'},
    '047658': {'desc': 'Veda Pneu', 'sku': '711'},
    'CARE044907': {'desc': 'Limpa Para-brisa', 'sku': '724'},
    'TU127': {'desc': 'Limpeza Injetores DIESEL', 'sku': '127'},
    'TU137': {'desc': 'Limpeza Injetores FLEX', 'sku': '137'},
    'TU987': {'desc': 'Agente do Sistema SCR ARLA32', 'sku': '987'},
    'TUN987': {'desc': 'Agente do Sistema SCR ARLA32', 'sku': '987'},
    'TU931': {'desc': 'Limpeza Corretiva DPF 931', 'sku': '931'},
    'TU932': {'desc': 'Limpeza Corretiva DPF 932', 'sku': '932'}
}

PRODUCT_CATALOG = [
    ('CARE0 40001', 'Espuma Limpeza'),
    ('CARE0 40102', 'Lubrificante Teflon'),
    ('CARE0 40201', 'Desengraxante Universal'),
    ('CARE0 40501', 'Limpeza Preventiva DPF'),
    ('CARE0 40701', 'Evaporador'),
    ('CARE0 40702', 'Sanitizador AC'),
    ('CARE0 40703', 'Odorizante'),
    ('CARE0 42501', 'Tratamento FLEX'),
    ('CARE0 42502', 'Tratamento DIESEL'),
    ('CARE0 43501', 'Limp. Interna Motor'),
    ('CARE0 44902', 'Lubrificação Feixe de Molas'),
    ('CARE0 44904', 'Kit Lubrificação'),
    ('CARE0 44905', 'Veda Pneu'),
    ('CARE044907', 'Limpa Para-brisa'),
    ('TU127', 'Limpeza Injetores DIESEL'),
    ('TU137', 'Limpeza Injetores FLEX'),
    ('TU931', 'Limpeza Corretiva DPF 931'),
    ('TU932', 'Limpeza Corretiva DPF 932'),
    ('TU987', 'Agente do Sistema SCR ARLA32')
]

METAS_STAFF = {
    'ARARANGUÁ': {'994': 10, '127': 2, '137': 1, '931': 2, '932': 2},
    'CRICIÚMA': {'994': 6, '127': 3, '137': 2, '931': 2, '932': 2},
    'LAGES': {'994': 8, '127': 4, '137': 1, '931': 3, '932': 3},
    'TUBARÃO': {'994': 10, '127': 4, '137': 2, '931': 3, '932': 3},
    'VIDEIRA': {'994': 6, '127': 3, '137': 1, '931': 2, '932': 2},
}

STAFF_SKUS_INFO = [
    ('994', 'Evaporador / Higienização Ar'),
    ('127', 'Limpeza Injetores DIESEL'),
    ('137', 'Limpeza Injetores FLEX'),
    ('931', 'Limpeza Corretiva DPF 931'),
    ('932', 'Limpeza Corretiva DPF 932'),
]

LOJAS_PADRAO_ORDEM = ['Araranguá', 'Criciúma', 'Lages', 'Tubarão', 'Videira']

def format_short_name(name):
    parts = str(name).strip().split()
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0].upper()
    return f"{parts[0]} {parts[-1]}".upper()

def format_loja_name(loja_str):
    nome = str(loja_str).replace('MERCOSUL VEICULOS LTDA', '').replace('MERCOSUL VEÍCULOS LTDA', '').strip()
    return nome.replace('(', '').replace(')', '').strip()

def parse_dms_date(series):
    parsed = pd.to_datetime(series, errors='coerce', dayfirst=True)
    if parsed.isna().all() and not series.empty:
        numeric_series = pd.to_numeric(series, errors='coerce')
        if not numeric_series.isna().all():
            parsed = pd.to_datetime(numeric_series, unit='D', origin='1899-12-30', errors='coerce')
    return parsed.dt.strftime('%d/%m/%Y').fillna('N/A')

def map_info(ref):
    info = PRODUCT_MAP.get(ref, {})
    return info.get('sku', None), info.get('desc', 'Outros')

def save_to_database(file_pass, file_vend):
    raw_p = pd.read_excel(file_pass)
    df_p = raw_p.copy()
    df_p['TipoOS'] = df_p['TipoOS_Sigla'].astype(str).str.strip()
    df_csp = df_p[df_p['TipoOS'] == 'CSP'].drop_duplicates(subset=['OS_Codigo', 'OS_Numero']).copy()
    df_csp['Consultor'] = df_csp['Consultor_Nome'].astype(str).str.strip().str.upper()
    df_csp['Empresa'] = df_csp['Empresa_Nome'].astype(str).str.strip()
    df_csp['DataPassagem'] = parse_dms_date(df_csp['NotaFiscal_DataEmissao'])
    
    passagens_list = []
    for _, row in df_csp.iterrows():
        passagens_list.append({
            'empresa': row['Empresa'],
            'consultor': row['Consultor'],
            'os_codigo': str(row['OS_Codigo']),
            'os_numero': str(row['OS_Numero']),
            'data_passagem': row['DataPassagem']
        })
    
    if passagens_list:
        try:
            supabase.table("passagens").upsert(passagens_list, on_conflict="os_codigo,os_numero").execute()
        except Exception:
            pass

    raw_v = pd.read_excel(file_vend)
    df_v = raw_v.copy()
    df_v['NF_Numero'] = pd.to_numeric(df_v['NF_Numero'], errors='coerce').fillna(0).astype(int)
    df_v['NFItem_Cod'] = pd.to_numeric(df_v['NFItem_Cod'], errors='coerce').fillna(0).astype(int)
    df_v = df_v.drop_duplicates(subset=['NF_Numero', 'NFItem_Cod']).copy()

    df_v['Consultor'] = df_v['NF_UsuNomVendedor'].astype(str).str.strip().str.upper()
    df_v['Empresa'] = df_v['Empresa_Nome'].astype(str).str.strip()
    df_v['ProdRef'] = df_v['NFItem_ProdutoRef'].astype(str).str.strip()
    df_v['Qtde'] = pd.to_numeric(df_v['NFItem_Qtde'], errors='coerce').fillna(0)
    df_v['DataVenda'] = parse_dms_date(df_v['NF_Dataemis'])

    vendas_list = []
    for _, row in df_v.iterrows():
        sku, desc = map_info(row['ProdRef'])
        if sku:
            vendas_list.append({
                'empresa': row['Empresa'],
                'consultor': row['Consultor'],
                'nf_numero': int(row['NF_Numero']),
                'nf_item_cod': int(row['NFItem_Cod']),
                'prod_ref': row['ProdRef'],
                'sku': sku,
                'descricao': desc,
                'qtde': float(row['Qtde']),
                'data_venda': row['DataVenda']
            })

    if vendas_list:
        try:
            supabase.table("vendas").upsert(vendas_list, on_conflict="nf_numero,nf_item_cod,prod_ref").execute()
        except Exception:
            pass

    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    supabase.table("uploads_log").insert({"arquivo_tipo": "Vendas & Passagens", "data_upload": agora}).execute()

# Pop-up / Modal de Análise do Consultor
@st.dialog("Análise do Consultor")
def abrir_modal_consultor(short_n, mes_sel, loja_formatada, tot_latas_c, tot_os_c, conv_c, produtos_nao_vendidos_lista):
    st.markdown(f"### 👤 {short_n}")
    
    col_c1, col_c2, col_c3 = st.columns(3)
    col_c1.metric("Total Latas", tot_latas_c)
    col_c2.metric("Passagens CSP", tot_os_c)
    col_c3.metric("Conversão", f"{conv_c:.2f}")

    saudacao = f"Fala, *{short_n}*! Tudo joia? 🚀 Passando para dar aquela conferida rápida no nosso ritmo da campanha TUNAP em *{mes_sel}* por *{loja_formatada}*."
    
    if conv_c >= 2.40:
        desempenho_msg = f"📈 Seu ritmo está excelente! Você já soma {tot_latas_c} latas em {tot_os_c} passagens CSP, alcançando uma conversão fantástica de *{conv_c:.2f}* (acima da nossa meta de 2.40). Parabéns pelo foco e dedicação!"
    else:
        falta_conv = round(2.40 - conv_c, 2)
        desempenho_msg = f"📊 Até o momento, registramos {tot_latas_c} latas em {tot_os_c} passagens CSP, gerando uma conversão de *{conv_c:.2f}*. Estamos muito perto da meta de 2.40 (faltam apenas {falta_conv} pontos na média), e tenho certeza que com alguns ajustes nos próximos atendimentos vamos buscar esse objetivo!"

    if produtos_nao_vendidos_lista:
        oportunidades_msg = f"💡 *Oportunidades de Ouro (Produtos que ainda não saíram nas suas OS):*\n" + "\n".join([f"• ⚠️ {item}" for item in produtos_nao_vendidos_lista[:6]]) + f"\n*(E mais alguns itens do catálogo)*\n\n🎯 Focar nesses itens nos balcões vai turbinar o seu mix e maximizar seus ganhos!"
    else:
        oportunidades_msg = f"🎉 Espetacular! Você já pontuou com absolutamente todos os produtos do mix! Trabalho impecável!"

    fechamento = f"Vamos pra cima nas próximas passagens! Qualquer dúvida ou apoio que precisar, estou à disposição. Bom trabalho e excelentes vendas! 👊🔥"

    texto_wpp_consultor = f"{saudacao}\n\n{desempenho_msg}\n\n{oportunidades_msg}\n\n{fechamento}"

    st.markdown("**Mensagem pronta para envio:**")
    st.markdown(f'<div class="wpp-box">{texto_wpp_consultor}</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Barra Lateral
# -----------------------------------------------------------------------------
LOGOTIPO_URL = "https://lh3.googleusercontent.com/d/1ONAL_dfLAPxpQKxaynprv24hf2vx2Yde=s400"
st.sidebar.image(
    LOGOTIPO_URL, 
    use_container_width=False
)
st.sidebar.markdown("---")

df_vendas, df_pass = load_data_from_db()

if not df_vendas.empty and 'empresa' in df_vendas.columns:
    lojas_brutas = sorted(df_vendas['empresa'].unique().tolist())
    lojas_map = {format_loja_name(l): l for l in lojas_brutas}
    lojas_display = sorted(list(lojas_map.keys()))
    
    default_loja_index = 0
    if "loja_sel_display" in st.session_state and st.session_state.loja_sel_display in lojas_display:
        default_loja_index = lojas_display.index(st.session_state.loja_sel_display)

    loja_display_sel = st.sidebar.selectbox("Concessionária:", lojas_display, index=default_loja_index, key="loja_sel_display")
    loja_sel = lojas_map[loja_display_sel]
    
    meses_dict = {
        "Setembro": "09", 
        "Outubro": "10", 
        "Novembro": "11", 
        "Dezembro": "12"
    }
    
    mes_atual_num = datetime.now().strftime('%m')
    default_mes_key = "Outubro"
    for nome_mes, num_str in meses_dict.items():
        if num_str == mes_atual_num:
            default_mes_key = nome_mes
            break

    meses_keys = list(meses_dict.keys())
    default_mes_index = meses_keys.index(default_mes_key) if default_mes_key in meses_keys else 1

    mes_sel = st.sidebar.selectbox("Mês de Apuração:", meses_keys, index=default_mes_index)
    num_mes = meses_dict[mes_sel]
else:
    loja_sel = None
    loja_display_sel = "Criciúma"
    num_mes = datetime.now().strftime('%m')
    mes_sel = "Outubro"
    st.sidebar.info("Banco no Supabase vazio. Faça o upload abaixo.")

st.sidebar.markdown("---")

st.sidebar.subheader("📥 Atualizar Histórico (Upload)")
file_pass = st.sidebar.file_uploader("Relatório de Passagens (OS)", type=["xlsx", "xls"])
file_vend = st.sidebar.file_uploader("Relatório de Vendas (NF)", type=["xlsx", "xls"])

if file_pass and file_vend:
    if st.sidebar.button("🔄 Atualizar dados", use_container_width=True):
        with st.spinner("Processando e atualizando na nuvem..."):
            save_to_database(file_pass, file_vend)
            st.sidebar.success("🟢 Dados atualizados no Supabase!")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Status dos Dados na Nuvem")

min_v, max_v, min_p, max_p, ultimo_upload = get_db_status()

st.sidebar.markdown(f"🕒 **Último Upload:** `{ultimo_upload}`")
st.sidebar.markdown(f"🛒 **Vendas:** `{min_v}` até `{max_v}`")
st.sidebar.markdown(f"🛠️ **Passagens:** `{min_p}` até `{max_p}`")

st.sidebar.markdown("---")

st.sidebar.subheader("🗑️ Gerenciamento")
if "confirm_clear" not in st.session_state:
    st.session_state.confirm_clear = False

if not st.session_state.confirm_clear:
    if st.sidebar.button("🧹 Limpar Banco do Supabase", use_container_width=True):
        st.session_state.confirm_clear = True
        st.rerun()
else:
    st.sidebar.warning("Tem certeza? Todos os dados na nuvem serão apagados!")
    col_bt1, col_bt2 = st.sidebar.columns(2)
    with col_bt1:
        if st.button("Sim, apagar", use_container_width=True):
            clear_database()
            st.session_state.confirm_clear = False
            st.sidebar.success("Banco limpo!")
            st.rerun()
    with col_bt2:
        if st.button("Cancelar", use_container_width=True):
            st.session_state.confirm_clear = False
            st.rerun()

# -----------------------------------------------------------------------------
# Corpo Principal
# -----------------------------------------------------------------------------
st.title("🚗 TUNAP | Campanha Mercosul")

st.markdown(f"""
    <div class="header-subtitle">
        📍 Concessionária: <b>{loja_display_sel}</b> &nbsp;|&nbsp; 📅 Período: <b>{mes_sel}/2026</b>
    </div>
""", unsafe_allow_html=True)

if df_vendas.empty:
    st.warning("⚠️ O banco de dados no Supabase não possui registros. Faça o upload dos relatórios na barra lateral.")
else:
    # Filtra dados garantindo correspondência insensível a maiúsculas
    v_filtered = df_vendas[(df_vendas['empresa'].astype(str).str.upper() == str(loja_sel).upper()) & (df_vendas['data_venda'].str[3:5] == num_mes)] if not df_vendas.empty else pd.DataFrame()
    p_filtered = df_pass[(df_pass['empresa'].astype(str).str.upper() == str(loja_sel).upper()) & (df_pass['data_passagem'].str[3:5] == num_mes)] if not df_pass.empty else pd.DataFrame()

    tab1, tab2, tab3, tab4 = st.tabs(["👤 Consultores", "🛠️ Técnico", "📊 Gerencial", "📈 Analytics Global"])

    # --- ABA 1: CONSULTORES ---
    with tab1:
        st.subheader("Vendas por Consultor")
        
        all_consultants = sorted(list(set(p_filtered['consultor'].dropna().tolist() + v_filtered['consultor'].dropna().tolist()))) if not v_filtered.empty or not p_filtered.empty else []
        filtered_consultants = []
        consultant_display_map = {}

        for c in all_consultants:
            short_name = format_short_name(c)
            filtered_consultants.append(c)
            consultant_display_map[c] = short_name

        if not filtered_consultants:
            st.info("Nenhum consultor registrado para esta concessionária no período selecionado.")
        else:
            st.write("📊 **Clique no botão do consultor para abrir a análise:**")
            cols_consultores_btns = st.columns(min(len(filtered_consultants), 6))
            for idx, c in enumerate(filtered_consultants):
                short_n = consultant_display_map[c]
                col_idx = idx % len(cols_consultores_btns)
                with cols_consultores_btns[col_idx]:
                    if st.button(f"📊 {short_n}", key=f"btn_pop_{c}", use_container_width=True):
                        c_vendas = v_filtered[v_filtered['consultor'] == c]
                        c_pass = p_filtered[p_filtered['consultor'] == c]
                        tot_latas_c = int(c_vendas['qtde'].sum())
                        tot_os_c = int(c_pass['os_numero'].nunique())
                        conv_c = round(tot_latas_c / tot_os_c, 2) if tot_os_c > 0 else 0.0
                        
                        prod_nao_vendidos = []
                        for prod_ref, desc in PRODUCT_CATALOG:
                            sku_alvo = PRODUCT_MAP.get(prod_ref, {}).get('sku')
                            qtd_item = c_vendas[(c_vendas['prod_ref'] == prod_ref) | (c_vendas['sku'] == sku_alvo)]['qtde'].sum()
                            if qtd_item == 0:
                                prod_nao_vendidos.append(f"{desc} (SKU {sku_alvo})")
                        
                        abrir_modal_consultor(short_n, mes_sel, loja_display_sel, tot_latas_c, tot_os_c, conv_c, prod_nao_vendidos)

            st.markdown("<br>", unsafe_allow_html=True)

            matrix_data = []
            totais_colunas = {c: 0 for c in filtered_consultants}
            mix_colunas = {c: set() for c in filtered_consultants}

            for prod_cod, desc in PRODUCT_CATALOG:
                row_dict = {'Código SKU': prod_cod, 'Descrição do Produto': desc}
                sku_alvo = PRODUCT_MAP.get(prod_cod, {}).get('sku')
                for c in filtered_consultants:
                    short_n = consultant_display_map[c]
                    qtd = v_filtered[(v_filtered['consultor'] == c) & ((v_filtered['prod_ref'] == prod_cod) | (v_filtered['sku'] == sku_alvo))]['qtde'].sum()
                    qtd = int(qtd) if not np.isnan(qtd) else 0
                    row_dict[short_n] = str(qtd) if qtd > 0 else ""
                    if qtd > 0:
                        totais_colunas[c] += qtd
                        mix_colunas[c].add(sku_alvo if sku_alvo else prod_cod)
                matrix_data.append(row_dict)

            tot_row = {'Código SKU': 'TOTAL DE LATAS', 'Descrição do Produto': 'Soma Volume'}
            mix_row = {'Código SKU': 'CONTAGEM MIX', 'Descrição do Produto': 'SKUs Distintos'}
            pass_row = {'Código SKU': 'PASSAGENS CSP', 'Descrição do Produto': 'OS CSP'}
            conv_row = {'Código SKU': 'TAXA CONVERSÃO', 'Descrição do Produto': 'Latas / OS'}
            status_mix = {'Código SKU': 'STATUS MIX', 'Descrição do Produto': 'Meta 17 SKUs'}
            status_conv = {'Código SKU': 'STATUS CONV.', 'Descrição do Produto': 'Meta 2.40'}

            passagens_dict = {c: int(p_filtered[p_filtered['consultor'] == c]['os_numero'].nunique()) for c in filtered_consultants}

            for c in filtered_consultants:
                short_n = consultant_display_map[c]
                tot_v_c = totais_colunas[c]
                mix_c = len(mix_colunas[c])
                pass_c = passagens_dict[c]
                conv_c = round(tot_v_c / pass_c, 2) if pass_c > 0 else 0.0

                tot_row[short_n] = str(tot_v_c)
                mix_row[short_n] = str(mix_c)
                pass_row[short_n] = str(pass_c)
                conv_row[short_n] = f"{conv_c:.2f}"
                status_mix[short_n] = "🟢 OK" if mix_c >= 17 else f"🔴 Falta {17 - mix_c}"
                status_conv[short_n] = "🟢 OK" if conv_c >= 2.40 else f"🔴 Falta {round(2.40 - conv_c, 2):.2f}"

            matrix_data.extend([tot_row, mix_row, pass_row, conv_row, status_mix, status_conv])
            df_matrix = pd.DataFrame(matrix_data)
            
            st.markdown('<div class="table-responsive">', unsafe_allow_html=True)
            st.markdown(df_matrix.to_html(index=False, classes="custom-table"), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- ABA 2: EQUIPE TÉCNICA ---
    with tab2:
        st.subheader("Acompanhamento da Equipe Técnica")
        metas_loja = METAS_STAFF.get(loja_display_sel, {})
        
        tot_v = int(v_filtered['qtde'].sum()) if not v_filtered.empty else 0
        tot_p = int(p_filtered['os_numero'].nunique()) if not p_filtered.empty else 0
        taxa_conv = round(tot_v / tot_p, 2) if tot_p > 0 else 0.0

        staff_rows = []
        todos_skus = True
        for sku, desc in STAFF_SKUS_INFO:
            meta = metas_loja.get(sku, 0)
            realizado = int(v_filtered[v_filtered['sku'] == sku]['qtde'].sum()) if not v_filtered.empty else 0
            gap = realizado - meta
            pct = round((realizado / meta) * 100, 1) if meta > 0 else 0.0
            status = "🟢 Atingida" if realizado >= meta else f"🔴 Falta {abs(gap)}"
            if realizado < meta:
                todos_skus = False
            staff_rows.append({
                'SKU': str(sku), 
                'Descrição do Produto': str(desc), 
                'Meta': str(meta), 
                'Realizado': str(realizado), 
                'Atingimento %': f"{pct}%", 
                'GAP / Over': str(gap), 
                'Status': str(status)
            })

        meta_conv = 2.40
        pct_conv = round((taxa_conv / meta_conv) * 100, 1)
        gap_conv = round(taxa_conv - meta_conv, 2)
        status_conv = "🟢 Meta Atingida" if taxa_conv >= meta_conv else f"🔴 Falta {abs(gap_conv):.2f}"
        
        staff_rows.append({
            'SKU': '-', 
            'Descrição do Produto': 'Taxa de Conversão Loja', 
            'Meta': f"{meta_conv:.2f}", 
            'Realizado': f"{taxa_conv:.2f}", 
            'Atingimento %': f"{pct_conv}%", 
            'GAP / Over': f"{gap_conv:+.2f}", 
            'Status': str(status_conv)
        })

        df_staff = pd.DataFrame(staff_rows)
        st.markdown('<div class="table-responsive">', unsafe_allow_html=True)
        st.markdown(df_staff.to_html(index=False, classes="custom-table"), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        premio = "🏆 ELEGÍVEL À PREMIAÇÃO" if (todos_skus and taxa_conv >= meta_conv) else "❌ NÃO ELEGÍVEL"
        st.markdown(f"### Resultado Staff: **{premio}**")

    # --- ABA 3: PAINEL GERENCIAL ---
    with tab3:
        st.subheader(f"Visão Gerencial Consolidada - {mes_sel}/2026")
        st.write("Panorama geral consolidado de **todas as concessionárias** cadastradas no período selecionado:")

        v_gerencial_global = df_vendas[df_vendas['data_venda'].str[3:5] == num_mes] if not df_vendas.empty else pd.DataFrame()
        p_gerencial_global = df_pass[df_pass['data_passagem'].str[3:5] == num_mes] if not df_pass.empty else pd.DataFrame()

        if v_gerencial_global.empty:
            st.info("Nenhum dado registrado para o período gerencial selecionado.")
        else:
            lojas_disponiveis = sorted(v_gerencial_global['empresa'].unique().tolist())
            gerencial_rows = []

            tot_geral_v = 0
            tot_geral_p = 0

            for loja in lojas_disponiveis:
                v_loja = v_gerencial_global[v_gerencial_global['empresa'] == loja]
                p_loja = p_gerencial_global[p_gerencial_global['empresa'] == loja]

                v_tot = int(v_loja['qtde'].sum())
                p_tot = int(p_loja['os_numero'].nunique())
                conv_loja = round(v_tot / p_tot, 2) if p_tot > 0 else 0.0

                tot_geral_v += v_tot
                tot_geral_p += p_tot

                if conv_loja >= 2.80:
                    status_loja = "🏆 Nível Máximo (Meta 3)"
                elif conv_loja >= 2.60:
                    status_loja = "⭐ Intermediário (Meta 2)"
                elif conv_loja >= 2.40:
                    status_loja = "✔️ Nível Base (Meta 1)"
                else:
                    status_loja = "❌ Abaixo da Meta"

                gerencial_rows.append({
                    'Concessionária': str(format_loja_name(loja)),
                    'Total Vendas (Latas)': str(v_tot),
                    'Passagens (CSP)': str(p_tot),
                    'Conversão': f"{conv_loja:.2f}",
                    'Status Executivo': str(status_loja)
                })

            conv_geral_rede = round(tot_geral_v / tot_geral_p, 2) if tot_geral_p > 0 else 0.0
            gerencial_rows.append({
                'Concessionária': 'TOTAL / MÉDIA REDE',
                'Total Vendas (Latas)': str(tot_geral_v),
                'Passagens (CSP)': str(tot_geral_p),
                'Conversão': f"{conv_geral_rede:.2f}",
                'Status Executivo': '🌐 Consolidado Mercosul'
            })

            df_gerencial_global = pd.DataFrame(gerencial_rows)
            st.markdown('<div class="table-responsive">', unsafe_allow_html=True)
            st.markdown(df_gerencial_global.to_html(index=False, classes="custom-table"), unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- ABA 4: ANALYTICS GLOBAL ---
    with tab4:
        st.subheader("📈 Analytics & Desempenho Global da Campanha")
        
        if df_vendas.empty or df_pass.empty:
            st.info("Sem dados cadastrados no banco para exibir análises globais.")
        else:
            df_v_glob = df_vendas.copy()
            df_p_glob = df_pass.copy()

            df_v_glob['mes_num'] = df_v_glob['data_venda'].str[3:5]
            df_p_glob['mes_num'] = df_p_glob['data_passagem'].str[3:5]

            meses_map_analytics = {"09": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro"}
            df_v_glob['Mes'] = df_v_glob['mes_num'].map(meses_map_analytics)
            df_p_glob['Mes'] = df_p_glob['mes_num'].map(meses_map_analytics)

            df_v_glob['Concessionaria'] = df_v_glob['empresa'].apply(format_loja_name)
            df_p_glob['Concessionaria'] = df_p_glob['empresa'].apply(format_loja_name)

            col_a1, col_a2 = st.columns(2)

            with col_a1:
                st.markdown("#### 📦 Volume de Latas por Concessionária")
                v_pivot = df_v_glob.groupby(['Mes', 'Concessionaria'])['qtde'].sum().unstack().fillna(0)
                st.line_chart(v_pivot, use_container_width=True)

            with col_a2:
                st.markdown("#### 🎯 Taxa de Conversão por Concessionária")
                v_grp = df_v_glob.groupby(['Mes', 'Concessionaria'])['qtde'].sum().reset_index()
                p_grp = df_p_glob.groupby(['Mes', 'Concessionaria'])['os_numero'].nunique().reset_index()
                
                df_conv_glob = pd.merge(v_grp, p_grp, on=['Mes', 'Concessionaria'], how='inner')
                df_conv_glob['Conversao'] = (df_conv_glob['qtde'] / df_conv_glob['os_numero']).round(2)
                
                conv_pivot = df_conv_glob.pivot(index='Mes', columns='Concessionaria', values='Conversao').fillna(0)
                st.line_chart(conv_pivot, use_container_width=True)

            st.markdown("---")
            st.subheader("📊 Tabela Geral por Produto e Concessionária")

            col_filtro, col_vazia = st.columns([1, 2])
            with col_filtro:
                opcoes_meses = ["Todos os Meses"] + [m for m in ["Setembro", "Outubro", "Novembro", "Dezembro"] if m in df_v_glob['Mes'].unique()]
                mes_analytics_sel = st.selectbox("Filtrar Período do Relatório:", opcoes_meses, index=0)

            if mes_analytics_sel == "Todos os Meses":
                df_v_mes_sel = df_v_glob.copy()
                df_p_mes_sel = df_p_glob.copy()
            else:
                df_v_mes_sel = df_v_glob[df_v_glob['Mes'] == mes_analytics_sel]
                df_p_mes_sel = df_p_glob[df_p_glob['Mes'] == mes_analytics_sel]

            if df_v_mes_sel.empty:
                st.info("Nenhum registro encontrado para a seleção.")
            else:
                analytics_table_rows = []
                
                for prod_cod, desc in PRODUCT_CATALOG:
                    sku_alvo = PRODUCT_MAP.get(prod_cod, {}).get('sku')
                    row_dict = {'Código': prod_cod, 'Descrição': desc}
                    
                    soma_linha = 0
                    for loja in LOJAS_PADRAO_ORDEM:
                        qtd = df_v_mes_sel[(df_v_mes_sel['Concessionaria'].str.upper() == loja.upper()) & ((df_v_mes_sel['prod_ref'] == prod_cod) | (df_v_mes_sel['sku'] == sku_alvo))]['qtde'].sum()
                        qtd = int(qtd) if not np.isnan(qtd) else 0
                        row_dict[loja] = str(qtd) if qtd > 0 else ""
                        soma_linha += qtd
                    
                    row_dict['Total'] = str(soma_linha)
                    analytics_table_rows.append(row_dict)

                tot_vol_row = {'Código': 'SOMA VOLUME', 'Descrição': 'Total de Latas'}
                pass_row = {'Código': 'PASSAGENS CSP', 'Descrição': 'Atendimentos OS'}
                conv_row = {'Código': 'TAXA CONVERSÃO', 'Descrição': 'Latas / OS'}

                soma_geral_vol = 0
                soma_geral_pass = 0

                for loja in LOJAS_PADRAO_ORDEM:
                    tot_v_loja = int(df_v_mes_sel[df_v_mes_sel['Concessionaria'].str.upper() == loja.upper()]['qtde'].sum())
                    tot_p_loja = int(df_p_mes_sel[df_p_mes_sel['Concessionaria'].str.upper() == loja.upper()]['os_numero'].nunique())
                    conv_loja = round(tot_v_loja / tot_p_loja, 2) if tot_p_loja > 0 else 0.0

                    soma_geral_vol += tot_v_loja
                    soma_geral_pass += tot_p_loja

                    tot_vol_row[loja] = str(tot_v_loja)
                    pass_row[loja] = str(tot_p_loja)
                    conv_row[loja] = f"{conv_loja:.2f}"

                conv_geral_rede = round(soma_geral_vol / soma_geral_pass, 2) if soma_geral_pass > 0 else 0.0

                tot_vol_row['Total'] = str(soma_geral_vol)
                pass_row['Total'] = str(soma_geral_pass)
                conv_row['Total'] = f"{conv_geral_rede:.2f}"

                analytics_table_rows.extend([tot_vol_row, pass_row, conv_row])
                df_analytics_final = pd.DataFrame(analytics_table_rows)

                st.markdown('<div class="table-responsive">', unsafe_allow_html=True)
                st.markdown(df_analytics_final.to_html(index=False, classes="custom-table"), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
