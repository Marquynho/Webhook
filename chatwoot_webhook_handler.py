
import os
import json
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Variáveis de ambiente
WHATSAPP_API_TOKEN = os.environ.get("WHATSAPP_API_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

# Mapeamento de textos de botões para respostas automáticas
# Em um cenário real, isso poderia vir de um banco de dados ou arquivo de configuração
BUTTON_RESPONSES = {
    "Opção 1": "Você selecionou a Opção 1! Em breve um de nossos atendentes entrará em contato.",
    "Falar com Atendente": "Entendido! Um de nossos atendentes já foi notificado e irá te ajudar em breve.",
    "Ver Catálogo": "Aqui está o link para o nosso catálogo: [Link do Catálogo](https://seucatalogo.com)",
    "Suporte Técnico": "Para suporte técnico, por favor, visite nossa página de ajuda: [Ajuda](https://suaempresa.com/suporte)"
}

def send_whatsapp_message(to_number, message_text):
    """
    Função para enviar uma mensagem de texto de volta para o cliente via WhatsApp Cloud API.
    """
    if not WHATSAPP_API_TOKEN or not PHONE_NUMBER_ID:
        print("Erro: WHATSAPP_API_TOKEN ou PHONE_NUMBER_ID não configurados.")
        return

    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json"
    }

    clean_number = to_number.replace("+", "")
    
    json_data = {
        "messaging_product": "whatsapp",
        "to": clean_number,
        "type": "text",
        "text": {
            "body": message_text
        }
    }
    
    whatsapp_api_url = f"https://graph.facebook.com/v24.0/{PHONE_NUMBER_ID}/messages"
    
    try:
        response = requests.post(whatsapp_api_url, headers=headers, json=json_data, timeout=10 )
        print(f"Resposta da Meta API: {response.status_code} - {response.text}")

    
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar mensagem de resposta: {e}")
        if hasattr(e, "response") and e.response is not None:
            print("Detalhes do erro:", e.response.text)

@app.route("/chatwoot-webhook", methods=["POST"])
def chatwoot_webhook():
    # Retornamos 200 OK imediatamente para o Chatwoot não tentar reenviar em caso de erro
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "no_data"}), 200

        # Log para debug (ajuda a ver o que está chegando)
        print(f"Evento recebido: {data.get('event')}")

        # Lógica principal
        if data.get("event") == "message_created":
            message = data.get("message", {})
            
            # Só processamos se for mensagem de entrada (do cliente) e do tipo texto
            if message.get("message_type") == "incoming" and message.get("content_type") == "text":
                content = message.get("content", "").strip()
                
                # Tenta pegar o número de várias formas possíveis no JSON do Chatwoot
                sender = data.get("sender", {})
                phone_number = sender.get("phone_number") or message.get("sender", {}).get("phone_number")
                
                if not phone_number:
                    # Tenta pegar do objeto contact se o sender falhar
                    phone_number = data.get("contact", {}).get("phone_number")

                print(f"Processando mensagem: '{content}' de {phone_number}")

                if content in BUTTON_RESPONSES and phone_number:
                    response_text = BUTTON_RESPONSES[content]
                    print(f"Botão detectado! Respondendo para {phone_number}...")
                    send_whatsapp_message(phone_number, response_text)
                else:
                    print("Mensagem não corresponde a um botão ou número não encontrado.")

    except Exception as e:
        print(f"ERRO CRÍTICO NO PROCESSAMENTO: {e}")
        
    return jsonify({"status": "processed"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
