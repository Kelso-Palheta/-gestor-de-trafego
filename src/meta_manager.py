"""
Gestor de Tráfego — Motor de Integração com Meta Ads
=====================================================
Classe responsável por autenticar, monitorar e (futuramente)
otimizar campanhas na Graph API da Meta de forma autônoma.

Regra de ouro: DRY_RUN = True impede qualquer escrita na API.
"""

import os
import logging
import datetime
import pandas as pd
from dotenv import load_dotenv

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.exceptions import FacebookRequestError

from src.telegram_manager import TelegramNotifier
from src.ai_manager import CriativoAI


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
        
        # Instância nativa do Telegram para envio de alertas
        self.telegram = TelegramNotifier()
        
        # Instância da IA Generativa (Anthropic)
        self.ia = CriativoAI()

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

    def extrair_metricas_campanhas(self, dias: int = 7) -> pd.DataFrame:
        """
        Extrai as métricas de performance das campanhas ativas.
        
        Args:
            dias: Número de dias para analisar (padrão: 7 últimos dias)
            
        Returns:
            DataFrame do pandas com as métricas formatadas.
        """
        logger.info(f"📊 Extraindo métricas dos últimos {dias} dias...")
        
        # Parâmetros da consulta
        params = {
            'level': 'campaign',
            'filtering': [{'field': 'campaign.effective_status', 'operator': 'IN', 'value': ['ACTIVE', 'PAUSED', 'ARCHIVED']}],
            'time_range': {
                'since': (datetime.date.today() - datetime.timedelta(days=dias)).strftime('%Y-%m-%d'),
                'until': datetime.date.today().strftime('%Y-%m-%d')
            }
        }
        
        # Campos que queremos extrair
        fields = [
            'campaign_name',
            'campaign_id',
            'spend',
            'clicks',
            'impressions',
            'cpc',
            'cpm',
            'ctr',
            'actions',
            'cost_per_action_type'
        ]
        
        try:
            # Requisita os insights da conta
            insights = self.conta.get_insights(fields=fields, params=params)
            
            # Se não houver dados, retorna um DataFrame vazio com as colunas certas
            if not insights:
                logger.warning("Nenhuma campanha ativa com gastos/impressões encontrada neste período.")
                return pd.DataFrame(columns=['Campanha', 'ID', 'Gasto', 'Impressões', 'Cliques', 'CTR', 'CPC', 'CPM', 'CPA', 'Conversões'])
                
            # Processa os dados brutos da Meta para um formato tabular amigável
            dados_processados = []
            
            for item in insights:
                # Meta retorna actions como uma lista, precisamos encontrar as conversões
                conversoes = 0
                cpa = 0.0
                
                if 'actions' in item:
                    # Adaptável conforme o seu pixer. Pode contar 'lead', 'purchase', etc.
                    for action in item['actions']:
                        if action['action_type'] in ['lead', 'offsite_conversion.fb_pixel_lead', 'omni_purchase']:
                            conversoes += float(action['value'])
                
                if conversoes > 0:
                    cpa = float(item.get('spend', 0)) / conversoes
                
                linha = {
                    'Campanha': item.get('campaign_name'),
                    'ID': item.get('campaign_id'),
                    'Gasto': float(item.get('spend', 0)),
                    'Impressões': int(item.get('impressions', 0)),
                    'Cliques': int(item.get('clicks', 0)),
                    'CTR': float(item.get('ctr', 0)) if 'ctr' in item else 0.0,
                    'CPC': float(item.get('cpc', 0)) if 'cpc' in item else 0.0,
                    'CPM': float(item.get('cpm', 0)) if 'cpm' in item else 0.0,
                    'CPA': cpa,
                    'Conversões': conversoes
                }
                dados_processados.append(linha)
                
            # Cria o DataFrame
            df = pd.DataFrame(dados_processados)
            logger.info(f"✅ Extração concluída. {len(df)} campanhas processadas.")
            return df
            
        except FacebookRequestError as e:
            logger.error(f"❌ Erro ao extrair métricas: {e.api_error_message()}")
            return pd.DataFrame()
        except Exception as e:
            logger.exception(f"❌ Erro inesperado ao extrair métricas: {e}")
            return pd.DataFrame()

    def _pausar_campanha(self, campaign_id: str, campaign_name: str) -> bool:
        """
        Pausa uma campanha na Meta Ads API (se DRY_RUN permitir).
        """
        acao = f"Pausar campanha '{campaign_name}' ({campaign_id})"
        
        # Verifica a trava de segurança antes de qualquer escrita
        if not self._verificar_dry_run(acao):
            return False
            
        try:
            campanha = Campaign(campaign_id)
            campanha.api_update(fields=[], params={'status': 'PAUSED'})
            logger.info(f"✅ Sucesso: Campanha '{campaign_name}' foi PAUSADA na Meta.")
            return True
        except FacebookRequestError as e:
            logger.error(f"❌ Falha ao pausar campanha '{campaign_name}': {e.api_error_message()}")
            return False
        except Exception as e:
            logger.exception(f"❌ Erro inesperado ao pausar '{campaign_name}': {e}")
            return False

    def wasted_spend_finder(self, df_metricas: pd.DataFrame, limite_gasto: float = 30.0) -> None:
        """
        Analisa o DataFrame de métricas em busca de campanhas que gastaram 
        mais do que o limite definido sem gerar nenhuma conversão e toma
        a decisão de pausá-las.
        """
        logger.info("-" * 60)
        logger.info(f"🕵️  Iniciando Wasted Spend Finder (Limite: R$ {limite_gasto:.2f} s/ conversão)...")
        
        if df_metricas.empty:
            logger.warning("Nenhum dado para analisar.")
            return
            
        campanhas_ineficientes = df_metricas[
            (df_metricas['Gasto'] > limite_gasto) & 
            (df_metricas['Conversões'] == 0)
        ]
        
        total_ineficientes = len(campanhas_ineficientes)
        
        if total_ineficientes == 0:
            logger.info("✅ Nenhuma campanha ineficiente encontrada. Orçamento seguro.")
            return
            
        logger.warning(f"🚨 ALERTA: {total_ineficientes} campanha(s) ineficiente(s) detectada(s)!")
        
        # Mensagem formatada pro Telegram
        texto_alerta = f"Identificamos *{total_ineficientes}* campanha(s) gastando mais do que o limite fixado (*R$ {limite_gasto:.2f}*) sem gerar conversão.\n"
        
        for _, row in campanhas_ineficientes.iterrows():
            nome = row['Campanha']
            cid = row['ID']
            gasto = row['Gasto']
            
            logger.warning(f"  -> AVALIANDO: '{nome}' (Gasto: R$ {gasto:.2f} | Conv: 0)")
            
            # Chama o método de pausar (que será barrado pelo DRY_RUN se estiver ativo)
            if self._pausar_campanha(campaign_id=cid, campaign_name=nome):
                texto_alerta += f"\n🛑 *A IA pausou a campanha:*\n- Nome: {nome}\n- Gasto desperdiçado: R$ {gasto:.2f}"
            else:
                texto_alerta += f"\n⚠️ *A IA tentou pausar (ou DRY RUN) a campanha:*\n- Nome: {nome}\n- Gasto desperdiçado: R$ {gasto:.2f}"
            
            # Pede para a Inteligência Artificial pensar num novo criativo!
            if self.ia.ativo:
                copy_sugerida = self.ia.gerar_copy_anuncio(nome_campanha=nome, motivo="Gasto alto sem conversões")
                texto_alerta += f"\n\n🤖 *Sugestão do Claude AI para reviver esta oferta:*\n{copy_sugerida}\n"
                
        # Dispara o alerta no Telegram!
        if self.telegram.ativo:
            self.telegram.enviar_alerta(texto_alerta)
            
        logger.info("🏁 Wasted Spend Finder concluído.")

    def _ajustar_orcamento_campanha(self, campaign_id: str, campaign_name: str, multiplicador: float) -> str:
        """
        Lê o orçamento diário atual da campanha e aplica um multiplicador.
        O valor do budget da Meta sempre vem em centavos (ex: 5000 = R$ 50,00).
        """
        try:
            campanha = Campaign(campaign_id)
            dados = campanha.api_get(fields=['daily_budget'])
            
            if 'daily_budget' not in dados:
                msg = f"Campanha '{campaign_name}' não utiliza orçamento diário. Pulando."
                logger.warning(msg)
                return msg
                
            orcamento_atual_centavos = int(dados['daily_budget'])
            novo_orcamento_centavos = int(orcamento_atual_centavos * multiplicador)
            
            atual_reais = orcamento_atual_centavos / 100
            novo_reais = novo_orcamento_centavos / 100
            tipo_ajuste = "AUMENTAR" if multiplicador > 1 else "REDUZIR"
            percentual = abs((multiplicador - 1) * 100)
            
            acao = f"{tipo_ajuste} orçamento de '{campaign_name}' de R$ {atual_reais:.2f} para R$ {novo_reais:.2f} ({int(percentual)}%)"
            
            # Trava de segurança
            if not self._verificar_dry_run(acao):
                return f"[DRY-RUN] Evitou: {acao}"
                
            campanha.api_update(fields=[], params={'daily_budget': str(novo_orcamento_centavos)})
            logger.info(f"✅ Sucesso: O orçamento de '{campaign_name}' foi ajustado para R$ {novo_reais:.2f}.")
            return f"✅ {acao}"
            
        except FacebookRequestError as e:
            erro = f"Falha na Meta API ao tentar ajustar '{campaign_name}': {e.api_error_message()}"
            logger.error(f"❌ {erro}")
            return erro
        except Exception as e:
            erro = f"Erro inesperado ao ajustar '{campaign_name}': {e}"
            logger.exception(f"❌ {erro}")
            return erro

    def otimizador_cpa(self, df_metricas: pd.DataFrame, meta_cpa: float = 20.0, min_conversoes: int = 2) -> None:
        """
        Fase 5: Scale Up e Scale Down baseado em CPA.
        - Se o CPA estiver 20% ABAIXO da meta e tiver conversões: Aumenta o orçamento em 15%.
        - Se o CPA estiver 20% ACIMA da meta e tiver conversões: Reduz o orçamento em 10%.
        """
        logger.info("-" * 60)
        logger.info(f"📈 Iniciando Otimizador de CPA (Meta alvo: R$ {meta_cpa:.2f})...")
        
        if df_metricas.empty:
            logger.warning("Nenhum dado para analisar.")
            return

        cpa_excelente = meta_cpa * 0.8  # 20% mais barato que a meta (bom)
        cpa_critico = meta_cpa * 1.2    # 20% mais caro que a meta (ruim)
        
        campanhas_boas = []
        campanhas_ruins = []
        texto_telegram = f"📈 *Relatório de Otimização (Meta: R$ {meta_cpa:.2f})*\n\n"
        houve_acao = False

        for _, row in df_metricas.iterrows():
            nome = row['Campanha']
            cid = row['ID']
            cpa_atual = row['CPA']
            conversoes = row['Conversões']
            
            # Só otimiza se já houve um mínimo de inteligência (conversões) na campanha
            if conversoes >= min_conversoes:
                if cpa_atual <= cpa_excelente:
                    logger.info(f"  🌟 EXCELENTE: '{nome}' (CPA R$ {cpa_atual:.2f} | Conv: {conversoes}) -> Scale Up +15%")
                    resultado = self._ajustar_orcamento_campanha(cid, nome, multiplicador=1.15)
                    campanhas_boas.append(resultado)
                    houve_acao = True
                    
                elif cpa_atual >= cpa_critico:
                    logger.warning(f"  ⚠️ CRÍTICO: '{nome}' (CPA R$ {cpa_atual:.2f} | Conv: {conversoes}) -> Scale Down -10%")
                    resultado = self._ajustar_orcamento_campanha(cid, nome, multiplicador=0.90)
                    campanhas_ruins.append(resultado)
                    houve_acao = True
                else:
                    logger.info(f"  ⚖️ ESTÁVEL: '{nome}' (CPA R$ {cpa_atual:.2f} | Conv: {conversoes}) -> Nenhuma ação.")

        # Dispara o resumo no Telegram!
        if houve_acao and self.telegram.ativo:
            if campanhas_boas:
                texto_telegram += "*🚀 Campanhas Escaladas:*\n" + "\n".join([f"- {r}" for r in campanhas_boas]) + "\n\n"
            if campanhas_ruins:
                texto_telegram += "*📉 Campanhas Reduzidas:*\n" + "\n".join([f"- {r}" for r in campanhas_ruins])
                
            self.telegram.enviar_mensagem(texto_telegram)
            
        elif not houve_acao:
            logger.info("Nenhuma campanha se qualificou para Scale Up ou Down hoje.")

        logger.info("🏁 Otimizador de CPA concluído.")


