import os
import logging
import anthropic

logger = logging.getLogger(__name__)

class CriativoAI:
    """
    Gerenciador de Inteligência Artificial Generativa usando Claude (Anthropic).
    Criado para gerar copies de anúncios otimizadas.
    """
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY não encontrada no .env. A IA generativa não poderá criar anúncios.")
            self.ativo = False
        else:
            self.cliente = anthropic.Anthropic(api_key=self.api_key)
            self.ativo = True

    def gerar_copy_anuncio(self, nome_campanha: str, motivo: str = "Baixa conversão") -> str:
        """
        Pede para o Claude criar uma nova sugestão de copy baseada na campanha atual.
        """
        if not self.ativo:
            return "⚠️ IA Generativa desativada (Falta API Key na configuração)."

        prompt = f"""
        Você é um Copywriter de elite focado em tráfego pago (Meta Ads).
        A campanha '{nome_campanha}' foi pausada recentemente devido a: {motivo}.
        
        Sua missão:
        Me dê 2 ideias de textos (copies) altamente persuasivos para revivermos essa campanha.
        Não use hashtags exageradas. Seja focado em conversão e escassez.
        Retorne de forma enxuta.
        """

        try:
            logger.info(f"🧠 Acionando Claude AI para gerar ideias para '{nome_campanha}'...")
            
            mensagem = self.cliente.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=600,
                temperature=0.7,
                system="Você é um copywriter persuasivo e direto ao ponto.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            resposta_texto = mensagem.content[0].text
            logger.info("✅ Nova copy gerada com sucesso pela IA!")
            return resposta_texto
            
        except anthropic.NotFoundError:
            logger.error("❌ Conta da Anthropic (Claude) sem permissão para o modelo informado (possivelmente conta Tier 0 sem créditos).")
            return "❌ IA Indisponível: Sua conta da Anthropic não possui fundos (créditos comprados) para acessar o modelo Claude 3. É necessário adicionar saldo em console.anthropic.com."
        except Exception as e:
            logger.error(f"❌ Falha ao gerar texto com a IA: {e}")
            return f"❌ Erro ao gerar copy: {e}"
