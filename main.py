"""
Gestor de Tráfego — Ponto de Entrada
======================================
Script principal que inicializa o sistema, testa a conexão
com a Meta Ads API e imprime o resultado no terminal.
"""

import sys
import logging

from src.meta_manager import MetaAdsManager


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
        # 1. Instancia o gerenciador (carrega .env e autentica)
        gerenciador = MetaAdsManager()

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
