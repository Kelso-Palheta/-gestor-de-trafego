"""
Gestor de Tráfego — Ponto de Entrada
======================================
Script principal que inicializa o sistema, testa a conexão
com a Meta Ads API e imprime o resultado no terminal.
"""

import sys
import logging
import pandas as pd

from src.meta_manager import MetaAdsManager
from src.telegram_manager import TelegramNotifier


# ============================================
# Configuração de Logging
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Saída no terminal
    ]
)

logger = logging.getLogger("GestorDeTrafego")


def main():
    """
    Fluxo principal:
    1. Instancia o MetaAdsManager (carrega credenciais + inicializa API)
    2. Executa o teste de conexão
    3. Imprime o resultado formatado no terminal
    """
    logger.info("=" * 60)
    logger.info("🚀 GESTOR DE TRÁFEGO — Inicializando Sistema")
    logger.info("=" * 60)

    try:
        # 1. Instancia o gerenciador e o bot (carrega .env e autentica)
        gerenciador = MetaAdsManager()
        telegram = TelegramNotifier()
        
        # Envia mensagem inicial se configurado
        if telegram.ativo:
            telegram.enviar_mensagem("🟢 *Gestor de Tráfego* ativado com sucesso. Iniciando rotina de testes...")

        # 2. Testa a conexão com a Meta Ads API
        logger.info("-" * 60)
        logger.info("📡 Testando conexão com a Meta Ads API...")
        logger.info("-" * 60)

        resultado = gerenciador.testar_conexao()

        # 3. Imprime resultado final
        logger.info("=" * 60)
        if resultado["sucesso"]:
            logger.info("✅ RESULTADO: Autenticação bem-sucedida!")
            logger.info(f"   Conta: {resultado['conta_nome']}")
            logger.info(f"   ID:    {resultado['conta_id']}")
            logger.info(f"   Moeda: {resultado['moeda']}")
            
            # 4. Extração de Métricas (Fase 3)
            logger.info("-" * 60)
            logger.info("📥 Iniciando extração de métricas de campanhas (ativas, pausadas e arquivadas)...")
            
            df_metricas = gerenciador.extrair_metricas_campanhas(dias=30)
            
            if not df_metricas.empty:
                logger.info("\n" + df_metricas.to_string())
                
                # 5. Otimização de Orçamento (Fase 4: Wasted Spend Finder)
                gerenciador.wasted_spend_finder(df_metricas=df_metricas, limite_gasto=30.0)
                
                # 6. Otimização de CPA (Fase 5: Scale Up / Scale Down)
                gerenciador.otimizador_cpa(df_metricas=df_metricas, meta_cpa=20.0, min_conversoes=2)
                
            else:
                logger.warning("Nenhum dado retornado para exibir ou otimizar no momento.")
                
        else:
            logger.error(f"❌ RESULTADO: Falha na autenticação")
            logger.error(f"   Motivo: {resultado['mensagem']}")
        logger.info("=" * 60)

    except ValueError as e:
        # Credenciais ausentes no .env
        logger.error("=" * 60)
        logger.error(f"⛔ ERRO DE CONFIGURAÇÃO: {e}")
        logger.error("   Copie .env.example para .env e preencha suas credenciais.")
        logger.error("=" * 60)
        sys.exit(1)

    except Exception as e:
        # Erro inesperado
        logger.exception("=" * 60)
        logger.exception(f"💥 ERRO INESPERADO: {e}")
        logger.exception("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
