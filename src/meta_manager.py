"""
Gestor de Tráfego — Motor de Integração com Meta Ads
=====================================================
Classe responsável por autenticar, monitorar e (futuramente)
otimizar campanhas na Graph API da Meta de forma autônoma.

Regra de ouro: DRY_RUN = True impede qualquer escrita na API.
"""

import os
import logging
from dotenv import load_dotenv

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.exceptions import FacebookRequestError


# Configuração do logger
logger = logging.getLogger(__name__)


class MetaAdsManager:
    """
    Gerenciador autônomo de campanhas Meta Ads.

    Responsabilidades:
    - Autenticação segura via OAuth 2.0
    - Leitura de métricas de campanhas
    - Tomada de decisão (pausar, ativar, ajustar) com trava DRY_RUN

    Attributes:
        DRY_RUN (bool): Trava de segurança. Enquanto True, nenhum método
                        pode enviar requisições de alteração (POST/PUT).
        ad_account_id (str): ID da conta de anúncios no formato 'act_XXXX'.
        api (FacebookAdsApi): Instância inicializada da API.
    """

    # ==========================================
    # TRAVA DE SEGURANÇA — NÃO ALTERE SEM REVISÃO
    # ==========================================
    DRY_RUN = True

    def __init__(self):
        """
        Inicializa o gerenciador carregando credenciais do .env
        e autenticando na Graph API da Meta.

        Raises:
            ValueError: Se alguma credencial obrigatória estiver faltando no .env.
        """
        # Carrega variáveis do arquivo .env
        load_dotenv()

        # Lê as credenciais do ambiente
        self.app_id = os.getenv("META_APP_ID")
        self.app_secret = os.getenv("META_APP_SECRET")
        self.access_token = os.getenv("META_ACCESS_TOKEN")
        self.ad_account_id = os.getenv("META_AD_ACCOUNT_ID")

        # Validação: todas as credenciais são obrigatórias
        self._validar_credenciais()

        # Inicializa a API oficial da Meta
        self.api = FacebookAdsApi.init(
            app_id=self.app_id,
            app_secret=self.app_secret,
            access_token=self.access_token
        )

        # Referência à conta de anúncios
        self.conta = AdAccount(self.ad_account_id)

        # Log de inicialização
        logger.info("MetaAdsManager inicializado com sucesso.")
        logger.info(f"Conta de anúncios: {self.ad_account_id}")
        logger.warning(
            f"Modo DRY_RUN: {'ATIVO ✅ (somente leitura)' if self.DRY_RUN else 'DESATIVADO ⚠️ (escrita habilitada)'}"
        )

    def _validar_credenciais(self):
        """
        Verifica se todas as credenciais obrigatórias foram carregadas.

        Raises:
            ValueError: Se alguma credencial estiver vazia ou ausente.
        """
        credenciais = {
            "META_APP_ID": self.app_id,
            "META_APP_SECRET": self.app_secret,
            "META_ACCESS_TOKEN": self.access_token,
            "META_AD_ACCOUNT_ID": self.ad_account_id,
        }

        faltando = [nome for nome, valor in credenciais.items() if not valor]

        if faltando:
            msg = (
                f"Credenciais ausentes no .env: {', '.join(faltando)}. "
                f"Copie o .env.example para .env e preencha os valores."
            )
            logger.error(msg)
            raise ValueError(msg)

    def testar_conexao(self) -> dict:
        """
        Testa a autenticação fazendo uma requisição de leitura simples
        à conta de anúncios (lê o nome e o ID).

        Returns:
            dict: Dicionário com 'sucesso' (bool), 'conta_id', 'conta_nome',
                  e 'mensagem' descritiva.

        Nota:
            Este método é somente leitura (GET) e funciona mesmo com DRY_RUN ativo.
        """
        try:
            # Requisição GET simples: lê nome e ID da conta
            dados_conta = self.conta.api_get(
                fields=["name", "account_id", "account_status", "currency"]
            )

            resultado = {
                "sucesso": True,
                "conta_id": dados_conta.get("account_id"),
                "conta_nome": dados_conta.get("name"),
                "moeda": dados_conta.get("currency"),
                "status": dados_conta.get("account_status"),
                "mensagem": "Autenticação realizada com sucesso!"
            }

            logger.info(f"✅ Conexão OK — Conta: {resultado['conta_nome']} ({resultado['conta_id']})")
            logger.info(f"   Moeda: {resultado['moeda']} | Status: {resultado['status']}")

            return resultado

        except FacebookRequestError as e:
            resultado = {
                "sucesso": False,
                "conta_id": None,
                "conta_nome": None,
                "moeda": None,
                "status": None,
                "mensagem": f"Erro na API da Meta: {e.api_error_message()}"
            }

            logger.error(f"❌ Falha na autenticação — {e.api_error_message()}")
            logger.error(f"   Código: {e.api_error_code()} | Subtipo: {e.api_error_subcode()}")
            logger.error(f"   Verifique se o Access Token é válido e tem permissões suficientes.")

            return resultado

        except Exception as e:
            resultado = {
                "sucesso": False,
                "conta_id": None,
                "conta_nome": None,
                "moeda": None,
                "status": None,
                "mensagem": f"Erro inesperado: {str(e)}"
            }

            logger.exception(f"❌ Erro inesperado ao testar conexão: {e}")

            return resultado

    def _verificar_dry_run(self, acao: str) -> bool:
        """
        Verifica se uma ação de escrita pode ser executada.
        Se DRY_RUN estiver ativo, loga a intenção e bloqueia a execução.

        Args:
            acao: Descrição da ação que seria executada.

        Returns:
            True se a ação está permitida, False se bloqueada pelo DRY_RUN.
        """
        if self.DRY_RUN:
            logger.info(f"🔒 [DRY-RUN] Eu faria: {acao} — mas DRY_RUN está ativo. Nenhuma ação enviada.")
            return False

        logger.info(f"🔓 [PRODUÇÃO] Executando: {acao}")
        return True
