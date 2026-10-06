import logging
import os
import sys

import httpx
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("whatsapp_alert")

def send_whatsapp_alert(message: str) -> bool:
    load_dotenv()

    api_url = os.getenv("WHATSAPP_API_URL")
    token = os.getenv("WHATSAPP_TOKEN")
    to_number = os.getenv("WHATSAPP_TO")

    if not api_url or not token or not to_number:
        logger.warning("Credenciais do WhatsApp não configuradas no .env. Alerta não enviado.")
        logger.info(f"Mensagem de alerta pendente: {message}")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": f"🚨 *MarketPulse Alert*\n\n{message}"},
    }

    try:
        with httpx.Client() as client:
            response = client.post(api_url, headers=headers, json=payload, timeout=15.0)
            response.raise_for_status()
            logger.info("Alerta enviado com sucesso via WhatsApp!")
            return True
    except (httpx.HTTPError, ValueError, KeyError) as e:
        logger.error(f"Erro ao enviar alerta via WhatsApp: {e}")
        return False

if __name__ == "__main__":
    send_whatsapp_alert("Teste de alerta do pipeline MarketPulse.")
