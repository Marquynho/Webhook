
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
    
    json_data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": message_text
        }
    }
    
    whatsapp_api_url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    
    try:
        response = requests.post(whatsapp_api_url, headers=headers, json=json_data, timeout=5)
        response.raise_for_status() # Levanta um erro para códigos de status HTTP ruins (4xx ou 5xx)
        print("Mensagem de resposta enviada com sucesso!")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar mensagem de resposta: {e}")
        if hasattr(e, "response") and e.response is not None:
            print("Detalhes do erro:", e.response.text)

@app.route("/chatwoot-webhook", methods=["POST"])
def chatwoot_webhook():
    data = request.get_json()
    print("Webhook do Chatwoot recebido:", json.dumps(data, indent=2))

    # Retorna 200 OK imediatamente para o Chatwoot
    # O processamento da lógica é rápido o suficiente para ser síncrono aqui.

    try:
        # Verifica se o evento é de uma mensagem criada e se é uma mensagem de entrada (do cliente)
        if data.get("event") == "message_created" and \
           data.get("message", {}).get("message_type") == "incoming" and \
           data.get("message", {}).get("content_type") == "text":
            
            message_content = data["message"]["content"]
            sender_phone_number = data["message"]["sender"]["phone_number"]

            print(f"Mensagem recebida do Chatwoot: '{message_content}' de {sender_phone_number}")

            # Verifica se o conteúdo da mensagem corresponde a um botão interativo esperado
            if message_content in BUTTON_RESPONSES:
                response_text = BUTTON_RESPONSES[message_content]
                print(f"Identificado clique no botão: '{message_content}'. Enviando resposta automática.")
                send_whatsapp_message(sender_phone_number, response_text)
            else:
                print(f"Mensagem '{message_content}' não corresponde a um botão interativo configurado. Nenhuma ação automática.")
        else:
            print("Evento não é uma mensagem de entrada de texto ou não é 'message_created'. Ignorando.")

    except Exception as e:
        print(f"Erro ao processar webhook do Chatwoot: {e}")
        # Em caso de erro, ainda retornamos 200 OK para o Chatwoot
        
    return jsonify({"status": "OK", "message": "Webhook processed"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
