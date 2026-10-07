import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="TUNAP | Painel Executivo Mercosul",
    page_icon="🚗",
    layout="wide"
)

# -----------------------------------------------------------------------------
# Configuração do Banco de Dados SQLite (base.db)
# -----------------------------------------------------------------------------
DB_NAME = "base.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT,
            consultor TEXT,
            nf_numero INTEGER,
            nf_item_cod INTEGER,
            prod_ref TEXT,
            sku TEXT,
            descricao TEXT,
            qtde REAL,
            data_venda TEXT,
            UNIQUE(nf_numero, nf_item_cod, prod_ref)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT,
            consultor TEXT,
            os_codigo TEXT,
            os_numero TEXT,
            data_passagem TEXT,
            UNIQUE(os_codigo, os_numero)
        )
    ''')
    
    # Tabela para controle de metadados / histórico de uploads
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploads_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arquivo_tipo TEXT,
            data_upload TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def clear_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vendas")
    cursor.execute("DELETE FROM passagens")
    cursor.execute("DELETE FROM uploads_log")
    conn.commit()
    conn.close()

def get_db_status():
    conn = sqlite3.connect(DB_NAME)
    
    # Maior e menor data de vendas
    df_v = pd.read_sql("SELECT data_venda FROM vendas", conn)
    min_v, max_v = "N/A", "N/A"
    if not df_v.empty:
        valid_v = pd.to_datetime(df_v['data_venda'], format='%d/%m/%Y', errors='coerce').dropna()
        if not valid_v.empty:
            min_v = valid_v.min().strftime('%d/%m/%Y')
            max_v = valid_v.max().strftime('%d/%m/%Y')

    # Maior e menor data de passagens
    df_p = pd.read_sql("SELECT data_passagem FROM passagens", conn)
    min_p, max_p = "N/A", "N/A"
    if not df_p.empty:
        valid_p = pd.to_datetime(df_p['data_passagem'], format='%d/%m/%Y', errors='coerce').dropna()
        if not valid_p.empty:
            min_p = valid_p.min().strftime('%d/%m/%Y')
            max_p = valid_p.max().strftime('%d/%m/%Y')

    # Último upload registrado
    df_log = pd.read_sql("SELECT data_upload FROM uploads_log ORDER BY id DESC LIMIT 1", conn)
    ultimo_upload = "Nenhum upload"
    if not df_log.empty:
        ultimo_upload = df_log['data_upload'].iloc[0]

    conn.close()
    return min_v, max_v, min_p, max_p, ultimo_upload

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
    'MERCOSUL VEICULOS LTDA (ARARANGUÁ)': {'994': 10, '127': 2, '137': 1, '931': 2, '932': 2},
    'MERCOSUL VEICULOS LTDA (CRICIÚMA)': {'994': 6, '127': 3, '137': 2, '931': 2, '932': 2},
    'MERCOSUL VEÍCULOS LTDA (LAGES)': {'994': 8, '127': 4, '137': 1, '931': 3, '932': 3},
    'MERCOSUL VEICULOS LTDA (TUBARÃO)': {'994': 10, '127': 4, '137': 2, '931': 3, '932': 3},
    'MERCOSUL VEICULOS LTDA (VIDEIRA)': {'994': 6, '127': 3, '137': 1, '931': 2, '932': 2},
}

STAFF_SKUS_INFO = [
    ('994', 'Evaporador / Higienização Ar'),
    ('127', 'Limpeza Injetores DIESEL'),
    ('137', 'Limpeza Injetores FLEX'),
    ('931', 'Limpeza Corretiva DPF 931'),
    ('932', 'Limpeza Corretiva DPF 932'),
]

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
    conn = sqlite3.connect(DB_NAME)
    
    raw_p = pd.read_excel(file_pass)
    df_p = raw_p.copy()
    df_p['TipoOS'] = df_p['TipoOS_Sigla'].astype(str).str.strip()
    df_csp = df_p[df_p['TipoOS'] == 'CSP'].drop_duplicates(subset=['OS_Codigo', 'OS_Numero']).copy()
    df_csp['Consultor'] = df_csp['Consultor_Nome'].astype(str).str.strip().str.upper()
    df_csp['Empresa'] = df_csp['Empresa_Nome'].astype(str).str.strip()
    df_csp['DataPassagem'] = parse_dms_date(df_csp['NotaFiscal_DataEmissao'])
    
    for _, row in df_csp.iterrows():
        try:
            conn.execute('''
                INSERT OR IGNORE INTO passagens (empresa, consultor, os_codigo, os_numero, data_passagem)
                VALUES (?, ?, ?, ?, ?)
            ''', (row['Empresa'], row['Consultor'], str(row['OS_Codigo']), str(row['OS_Numero']), row['DataPassagem']))
        except:
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

    for _, row in df_v.iterrows():
        sku, desc = map_info(row['ProdRef'])
        if sku:
            try:
                conn.execute('''
                    INSERT OR REPLACE INTO vendas (empresa, consultor, nf_numero, nf_item_cod, prod_ref, sku, descricao, qtde, data_venda)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (row['Empresa'], row['Consultor'], row['NF_Numero'], row['NFItem_Cod'], row['ProdRef'], sku, desc, row['Qtde'], row['DataVenda']))
            except:
                pass

    # Registra o histórico do upload atual com data/hora
    agora = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    conn.execute("INSERT INTO uploads_log (arquivo_tipo, data_upload) VALUES (?, ?)", ("Vendas & Passagens", agora))

    conn.commit()
    conn.close()

def load_data_from_db():
    conn = sqlite3.connect(DB_NAME)
    df_vendas = pd.read_sql("SELECT * FROM vendas", conn)
    df_pass = pd.read_sql("SELECT * FROM passagens", conn)
    conn.close()
    return df_vendas, df_pass

# -----------------------------------------------------------------------------
# Barra Lateral (Sidebar)
# -----------------------------------------------------------------------------
st.sidebar.title("⚙️ Painel de Controle")
st.sidebar.markdown("---")

# 1. PRIMEIRO: Seleção de Concessionária e Período (Setembro a Dezembro)
df_vendas_init, df_pass_init = load_data_from_db()

if not df_vendas_init.empty:
    lojas = sorted(df_vendas_init['empresa'].unique().tolist())
    loja_sel = st.sidebar.selectbox("Concessionária:", lojas)
    
    meses_dict = {
        "Setembro": "09", 
        "Outubro": "10", 
        "Novembro": "11", 
        "Dezembro": "12"
    }
    mes_sel = st.sidebar.selectbox("Mês de Apuração:", list(meses_dict.keys()))
    num_mes = meses_dict[mes_sel]
else:
    loja_sel = None
    num_mes = "10"
    mes_sel = "Outubro"
    st.sidebar.info("Banco vazio. Faça o upload abaixo.")

st.sidebar.markdown("---")

# 2. SEGUNDO: Operação de Atualização (Upload)
st.sidebar.subheader("📥 Atualizar Histórico (Upload)")
file_pass = st.sidebar.file_uploader("Relatório de Passagens (OS)", type=["xlsx", "xls"])
file_vend = st.sidebar.file_uploader("Relatório de Vendas (NF)", type=["xlsx", "xls"])

if file_pass and file_vend:
    if st.sidebar.button("💾 Salvar Novos Dados no Banco"):
        with st.spinner("Processando e salvando no base.db..."):
            save_to_database(file_pass, file_vend)
            st.sidebar.success("🟢 Dados acumulados com sucesso no banco!")
            st.rerun()

# -----------------------------------------------------------------------------
# PAINEL DE CONTROLE DE UPLOADS E REGISTROS DO BANCO
# -----------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Status dos Dados Carregados")

min_v, max_v, min_p, max_p, ultimo_upload = get_db_status()

st.sidebar.markdown(f"🕒 **Último Upload:**\n`{ultimo_upload}`")
st.sidebar.markdown(f"🛒 **Vendas (Notas Fiscais):**\nDe `{min_v}` até `{max_v}`")
st.sidebar.markdown(f"🛠️ **Passagens (OS CSP):**\nDe `{min_p}` até `{max_p}`")

st.sidebar.markdown("---")

# 3. TERCEIRO: Botão de Limpeza do Banco de Dados com confirmação
st.sidebar.subheader("🗑️ Gerenciamento de Dados")
if "confirm_clear" not in st.session_state:
    st.session_state.confirm_clear = False

if not st.session_state.confirm_clear:
    if st.sidebar.button("🧹 Limpar Banco de Dados"):
        st.session_state.confirm_clear = True
        st.rerun()
else:
    st.sidebar.warning("Tem certeza? Todos os dados salvos serão apagados!")
    col_bt1, col_bt2 = st.sidebar.columns(2)
    with col_bt1:
        if st.button("Sim, apagar"):
            clear_database()
            st.session_state.confirm_clear = False
            st.sidebar.success("Banco de dados limpo com sucesso!")
            st.rerun()
    with col_bt2:
        if st.button("Cancelar"):
            st.session_state.confirm_clear = False
            st.rerun()

# -----------------------------------------------------------------------------
# Corpo Principal
# -----------------------------------------------------------------------------
st.title("🚗 TUNAP | Painel Executivo Mercosul")

df_vendas, df_pass = load_data_from_db()

if df_vendas.empty:
    st.warning("⚠️ O banco de dados (`base.db`) não possui registros. Faça o upload dos relatórios na barra lateral.")
else:
    v_filtered = df_vendas[(df_vendas['empresa'] == loja_sel) & (df_vendas['data_venda'].str[3:5] == num_mes)]
    p_filtered = df_pass[(df_pass['empresa'] == loja_sel) & (df_pass['data_passagem'].str[3:5] == num_mes)]

    tab1, tab2, tab3 = st.tabs(["👤 Consultores", "🛠️ Equipe Técnica", "📊 Painel Gerentes"])

    # --- ABA 1: CONSULTORES ---
    with tab1:
        st.subheader("Matriz de Vendas por Consultor (SKUs)")
        
        all_consultants = sorted(list(set(p_filtered['consultor'].tolist() + v_filtered['consultor'].tolist())))
        filtered_consultants = []
        consultant_display_map = {}

        for c in all_consultants:
            tot_v = v_filtered[v_filtered['consultor'] == c]['qtde'].sum()
            tot_p = p_filtered[p_filtered['consultor'] == c]['os_numero'].nunique()
            if tot_v >= 10 and tot_p > 0:
                short_name = format_short_name(c)
                filtered_consultants.append(c)
                consultant_display_map[c] = short_name

        if not filtered_consultants:
            st.info("Nenhum consultor atingiu o volume mínimo de 10 latas no período selecionado.")
        else:
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
            
            # Tabela fixa (sem ordenação)
            st.markdown("### Matriz Consolidada da Equipe")
            st.markdown(df_matrix.to_html(index=False, classes="table table-striped"), unsafe_allow_html=True)

            # --- SEÇÃO DE ATALHOS / POP-UP INDIVIDUAL POR CONSULTOR ---
            st.markdown("---")
            st.subheader("📋 Atalhos Rápidos e Resumos Individuais (WhatsApp)")
            st.write("Abra o painel abaixo de cada consultor para copiar o resumo de desempenho e oportunidades:")

            for c in filtered_consultants:
                short_n = consultant_display_map[c]
                with st.expander(f"👤 Consultor: {short_n} (Resumo & Oportunidades WA)"):
                    c_vendas = v_filtered[v_filtered['consultor'] == c]
                    c_pass = p_filtered[p_filtered['consultor'] == c]
                    
                    tot_latas_c = int(c_vendas['qtde'].sum())
                    tot_os_c = int(c_pass['os_numero'].nunique())
                    conv_c = round(tot_latas_c / tot_os_c, 2) if tot_os_c > 0 else 0.0
                    
                    produtos_nao_vendidos_lista = []
                    for prod_ref, desc in PRODUCT_CATALOG:
                        sku_alvo = PRODUCT_MAP.get(prod_ref, {}).get('sku')
                        qtd_item = c_vendas[(c_vendas['prod_ref'] == prod_ref) | (c_vendas['sku'] == sku_alvo)]['qtde'].sum()
                        if qtd_item == 0:
                            produtos_nao_vendidos_lista.append(f"• ⚠️ {desc} (SKU {sku_alvo})")

                    col_c1, col_c2, col_c3 = st.columns(3)
                    col_c1.metric("Total Latas", tot_latas_c)
                    col_c2.metric("Passagens CSP", tot_os_c)
                    col_c3.metric("Conversão", f"{conv_c:.2f}")

                    texto_wpp_consultor = f"👤 *RELATÓRIO INDIVIDUAL - TUNAP*\n" \
                                          f"📌 Consultor: *{short_n}*\n" \
                                          f"📅 Período: {mes_sel}/2026\n\n" \
                                          f"📊 *Resultados Atuais:*\n" \
                                          f"• Total de Latas: {tot_latas_c}\n" \
                                          f"• Atendimentos CSP: {tot_os_c}\n" \
                                          f"• Taxa de Conversão: {conv_c:.2f}\n\n" \
                                          f"🚀 *Oportunidades (Produtos não vendidos):*\n" + \
                                          ("\n".join(produtos_nao_vendidos_lista) if produtos_nao_vendidos_lista else "• Nenhum! Fechou o mix completo! 🎉") + \
                                          f"\n\n_Foco no mix para alavancar os resultados!_"

                    st.markdown("**Mensagem pronta para o WhatsApp:**")
                    st.code(texto_wpp_consultor, language="markdown")

    # --- ABA 2: EQUIPE TÉCNICA ---
    with tab2:
        st.subheader("Acompanhamento da Equipe Técnica")
        metas_loja = METAS_STAFF.get(loja_sel, {})
        
        tot_v = int(v_filtered['qtde'].sum())
        tot_p = int(p_filtered['os_numero'].nunique())
        taxa_conv = round(tot_v / tot_p, 2) if tot_p > 0 else 0.0

        staff_rows = []
        todos_skus = True
        for sku, desc in STAFF_SKUS_INFO:
            meta = metas_loja.get(sku, 0)
            realizado = int(v_filtered[v_filtered['sku'] == sku]['qtde'].sum())
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
        st.markdown(df_staff.to_html(index=False, classes="table table-striped"), unsafe_allow_html=True)
        
        premio = "🏆 ELEGÍVEL À PREMIAÇÃO" if (todos_skus and taxa_conv >= meta_conv) else "❌ NÃO ELEGÍVEL"
        st.markdown(f"### Resultado Final Staff: **{premio}**")

    # --- ABA 3: PAINEL GERENTES ---
    with tab3:
        st.subheader("Visão Executiva Gerencial")
        
        m1, m2, m3 = 2.40, 2.60, 2.80
        s1 = "🟢 Atingida" if taxa_conv >= m1 else f"🔴 Falta {round(m1 - taxa_conv, 2)}"
        s2 = "🟢 Atingida" if taxa_conv >= m2 else f"🔴 Falta {round(m2 - taxa_conv, 2)}"
        s3 = "🟢 Atingida" if taxa_conv >= m3 else f"🔴 Falta {round(m3 - taxa_conv, 2)}"

        if taxa_conv >= m3:
            exec_status = "🏆 NÍVEL MÁXIMO (Meta 3)"
        elif taxa_conv >= m2:
            exec_status = "⭐ INTERMEDIÁRIO (Meta 2)"
        elif taxa_conv >= m1:
            exec_status = "✔️ NÍVEL BASE (Meta 1)"
        else:
            exec_status = "❌ ABAIXO DA META 1"

        gerente_data = [{
            'Concessionária': str(format_loja_name(loja_sel)),
            'Total Vendas (Latas)': str(tot_v),
            'Total Passagens (CSP)': str(tot_p),
            'Taxa Conversão': f"{taxa_conv:.2f}",
            'Meta 1 (2.4)': str(s1),
            'Meta 2 (2.6)': str(s2),
            'Meta 3 (2.8)': str(s3),
            'Status Executivo': str(exec_status)
        }]

        df_gerente = pd.DataFrame(gerente_data)
        st.markdown(df_gerente.to_html(index=False, classes="table table-striped"), unsafe_allow_html=True)

        st.markdown("---")
        if st.button("📝 Gerar Resumo Rápido para o WhatsApp"):
            texto_wpp = f"📊 *RESUMO EXECUTIVO TUNAP - {format_loja_name(loja_sel)}*\n" \
                        f"📅 Período: {mes_sel}/2026\n\n" \
                        f"• Vendas Totais: {tot_v} latas\n" \
                        f"• Passagens CSP: {tot_p} OS\n" \
                        f"• Taxa de Conversão: {taxa_conv:.2f} (Meta: 2.40)\n" \
                        f"• Status: {exec_status}\n\n" \
                        f"_Painel Gerencial Mercosul_"
            st.code(texto_wpp, language="markdown")
            st.info("Basta copiar o texto acima e enviar para a equipe junto com o print da tela!")