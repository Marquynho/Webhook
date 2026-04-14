
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
    "Quero estudar esse ganho?": "Ótimo. O Tiago já vai te chamar agora com as informações.",
    "Agora não, valeu.": "Entendido! Sinta-se à vontade para entrar em contato se mudar de ideia."
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
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "no_data"}), 200

        event = data.get('event')
        print(f"Evento recebido: {event}")

        if event == "message_created":
            # No Chatwoot, os campos costumam vir na raiz do payload para este evento
            message_type = data.get("message_type")
            content_type = data.get("content_type")
            content = data.get("content", "").strip()
            
            # Logs de debug para confirmar o que está chegando
            print(f"DEBUG: type={message_type}, content_type={content_type}, content='{content}'")

            # Verifica se é mensagem de entrada e do tipo texto
            if message_type == "incoming" and content_type == "text":
                # Busca o telefone no sender ou no contact
                sender = data.get("sender", {})
                contact = data.get("contact", {})
                
                phone_number = (sender.get("phone_number") or 
                                contact.get("phone_number") or 
                                data.get("conversation", {}).get("contact_inbox", {}).get("source_id"))

                print(f"Processando mensagem de: {phone_number}")

                if content in BUTTON_RESPONSES and phone_number:
                    response_text = BUTTON_RESPONSES[content]
                    print(f"Botão detectado! Respondendo para {phone_number}...")
                    send_whatsapp_message(phone_number, response_text)
                else:
                    print("Mensagem não corresponde a um botão ou número não encontrado.")
            else:
                print(f"Mensagem ignorada: Tipo {message_type} ou Formato {content_type}")

    except Exception as e:
        print(f"ERRO CRÍTICO NO PROCESSAMENTO: {e}")
        
    return jsonify({"status": "processed"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
