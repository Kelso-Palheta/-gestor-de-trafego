import streamlit as st
import pandas as pd
import datetime
from src.meta_manager import MetaAdsManager
from src.telegram_manager import TelegramNotifier

# Configuração da Página
st.set_page_config(
    page_title="Gestor de Tráfego - Palheta Brutal",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializa as classes no cache do Streamlit pra não recarregar toda hora
@st.cache_resource
def get_managers():
    try:
        man = MetaAdsManager()
        tel = TelegramNotifier()
        return man, tel, True
    except Exception as e:
        return None, None, False

manager, telegram, is_authed = get_managers()

# ==========================================
# SIDEBAR (Configurações)
# ==========================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Meta_Platforms_Inc._logo.svg/512px-Meta_Platforms_Inc._logo.svg.png", width=150)
    st.title("⚙️ Configurações")
    
    if is_authed:
        st.success(f"Conectado: {manager.ad_account_id}")
    else:
        st.error("Falha na autenticação. Verifique o .env")

    st.markdown("---")
    
    # Controles de segurança e metas
    st.header("Metas Globais")
    meta_cpa = st.number_input("Meta de CPA (R$)", min_value=1.0, value=20.0, step=1.0)
    limite_wasted = st.number_input("Limite Wasted Spend (R$)", min_value=5.0, value=30.0, step=1.0)
    dias_analise = st.slider("Dias Analisados", 1, 30, 7)
    
    st.markdown("---")
    dry_run_ui = st.toggle("Modo DRY_RUN (Segurança)", value=True, help="Se ativado, impede mudanças reais na Meta Ads.")
    
    if is_authed:
        # Atualiza a variável na classe baseada na UI
        manager.DRY_RUN = dry_run_ui

# ==========================================
# ÁREA PRINCIPAL
# ==========================================
st.title("🚀 Dashboard Autônomo - Palheta Brutal")
st.markdown("Bem-vindo ao centro de comando do seu Gestor de Tráfego. Aqui você acompanha e ajusta a inteligência artificial operando suas campanhas.")

if not is_authed:
    st.warning("⚠️ Ajuste suas credenciais no arquivo .env para começar.")
    st.stop()

# Abas de navegação
tab1, tab2, tab3 = st.tabs(["📊 Visão Geral (Métricas)", "🤖 Otimizador da IA", "🧠 IA Generativa"])

with tab1:
    st.header("Métricas das Campanhas")
    
    if st.button("🔄 Extrair Dados da Meta Agora", type="primary"):
        with st.spinner("Buscando dados na Meta Ads..."):
            df = manager.extrair_metricas_campanhas(dias=dias_analise)
            
            if not df.empty:
                st.session_state['df_metricas'] = df
                st.success("Dados atualizados com sucesso!")
            else:
                st.warning("Nenhuma campanha ativa retornou dados no período selecionado.")

    if 'df_metricas' in st.session_state and not st.session_state['df_metricas'].empty:
        df = st.session_state['df_metricas']
        
        # Métricas Globais (Cards)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Gasto", f"R$ {df['Gasto'].sum():.2f}")
        col2.metric("Conversões", f"{df['Conversões'].sum():.0f}")
        cpa_geral = df['Gasto'].sum() / df['Conversões'].sum() if df['Conversões'].sum() > 0 else 0
        col3.metric("CPA Médio Global", f"R$ {cpa_geral:.2f}")
        col4.metric("Campanhas Ativas", len(df))
        
        st.markdown("### Detalhamento por Campanha")
        st.dataframe(df.style.highlight_max(axis=0, subset=['Conversões'], color='lightgreen'))

with tab2:
    st.header("Executar Rotinas de Otimização")
    st.markdown("Acione as engrenagens de decisão manualmente para testar as regras ou auditar a inteligência artificial.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Wasted Spend Finder")
        st.info("Pausa campanhas que gastaram acima do limite sem conversão.")
        if st.button("🧹 Executar Varredura", key="btn_wasted"):
            if 'df_metricas' in st.session_state and not st.session_state['df_metricas'].empty:
                with st.spinner("Analisando gastos..."):
                    manager.wasted_spend_finder(st.session_state['df_metricas'], limite_gasto=limite_wasted)
                    st.success("Varredura concluída! Verifique o terminal para detalhes (se DRY_RUN estava ativo) ou seu Telegram.")
            else:
                st.error("Extraia os dados na aba Visão Geral primeiro.")

    with col2:
        st.subheader("Scale Up / Scale Down (CPA)")
        st.info("Sobe/desce orçamentos avaliando a Meta do CPA estipulada.")
        if st.button("📈 Executar Escala", key="btn_scale"):
             if 'df_metricas' in st.session_state and not st.session_state['df_metricas'].empty:
                with st.spinner("Otimizando orçamentos..."):
                    manager.otimizador_cpa(st.session_state['df_metricas'], meta_cpa=meta_cpa)
                    st.success("Orçamentos ajustados! Verifique seu Telegram.")
             else:
                st.error("Extraia os dados na aba Visão Geral primeiro.")

with tab3:
    st.header("Criativo AI (Anthropic Claude)")
    st.markdown("A IA só é disparada automaticamente quando uma campanha é pausada pelo gestor. Aqui você pode pedir ideias na mão.")
    
    campanha_nome = st.text_input("Nome/Tema da Oferta:")
    motivo_foco = st.selectbox("Qual o problema atual?", ["CPA muito alto (Falta persuasão)", "Sem cliques nas artes (CTR Baixo)", "Zero conversões (Despertar desejo urgente)"])
    
    if st.button("🔮 Gerar Copy Estilo Palheta Brutal"):
        if campanha_nome:
            with st.spinner("Claude 3.5 Sonnet está processando..."):
                if hasattr(manager, 'ia') and manager.ia.ativo:
                    resposta = manager.ia.gerar_copy_anuncio(nome_campanha=campanha_nome, motivo=motivo_foco)
                    st.text_area("Sugestão de Copy", value=resposta, height=300)
                else:
                    st.error("A IA não está ativada. Verifique sua chave no .env.")
        else:
            st.warning("Preencha o nome da campanha.")
