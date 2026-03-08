import os
import requests
import logging

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """
    Gerenciador de envios de mensagens para o Telegram.
    Usado para enviar alertas, relatórios e notificações em tempo real.
    """
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Credenciais do Telegram ausentes. As notificações não serão enviadas.")
            self.ativo = False
        else:
            self.ativo = True
            
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def enviar_mensagem(self, texto: str):
        """
        Envia uma mensagem de texto para o chat configurado.
        """
        if not self.ativo:
            return False
            
        payload = {
            "chat_id": self.chat_id,
            "text": texto,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(self.base_url, json=payload)
            response.raise_for_status()
            logger.info("📱 Mensagem enviada para o Telegram com sucesso.")
            return True
        except Exception as e:
            logger.error(f"❌ Falha ao enviar mensagem para o Telegram: {e}")
            return False
            
    def enviar_alerta(self, mensagem: str):
        """
        Envia um alerta crítico com emojis para chamar atenção.
        """
        texto_formatado = f"🚨 *ALERTA DO GESTOR DE TRÁFEGO* 🚨\n\n{mensagem}"
        return self.enviar_mensagem(texto_formatado)
