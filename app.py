import os
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration from environment variables
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

# Base URL for WhatsApp Cloud API
WHATSAPP_API_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

def send_whatsapp_message(target_number, message_text):
    """
    Send a WhatsApp message using the Meta Cloud API
    """
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": target_number,
        "type": "text",
        "text": {
            "body": message_text
        }
    }

    response = requests.post(WHATSAPP_API_URL, headers=headers, json=data)
    return response.json(), response.status_code

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """
    Verify the webhook endpoint with Meta
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            print("VERIFICATION_FAILED")
            return jsonify({"error": "Verification failed"}), 403
    return jsonify({"error": "Missing parameters"}), 400

@app.route('/webhook', methods=['POST'])
def process_webhook():
    """
    Process incoming WhatsApp messages
    """
    data = request.get_json()
    print(f"Received data: {json.dumps(data, indent=2)}")

    try:
        # Check if this is a message notification
        if data.get('object') == 'whatsapp_business_account':
            entry = data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})

            # Check if we have messages
            if 'messages' in value:
                message = value['messages'][0]
                from_number = message.get('from')

                # Check if it's a button message
                if message.get('type') == 'interactive':
                    interactive = message.get('interactive', {})
                    if interactive.get('type') == 'button_reply':
                        button_reply = interactive.get('button_reply', {})
                        payload = button_reply.get('id')
                        button_text = button_reply.get('title')

                        print(f"Button clicked - Payload: {payload}, Text: {button_text}")

                        # Process button clicks
                        if payload == 'CLIQUE_INTERESSE':
                            response_text = (
                                "Ótimo escolha! Este empreendimento oferece um ROI de 0,8% ao mês "
                                "com localização privilegiada em frente ao Parque do Sabiá. "
                                "Você pode conferir o catálogo completo aqui: [LINK_DO_CATALOGO]"
                            )
                        elif payload == 'CLIQUE_NEGATIVO':
                            response_text = (
                                "Tudo bem! Se mudar de ideia, estamos aqui para ajudar. "
                                "Tenha um ótimo dia!"
                            )
                        else:
                            response_text = "Opção não reconhecida. Por favor, tente novamente."

                        # Send response
                        if from_number:
                            send_whatsapp_message(from_number, response_text)
                            print(f"Sent response to {from_number}: {response_text}")

                    else:
                        print("Not a button reply interactive message")
                else:
                    print("Not an interactive message")
            else:
                print("No messages in value")
        else:
            print("Not a WhatsApp business account object")

    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({"error": "Internal server error"}), 500

    # Always return 200 OK to Meta
    return jsonify({"status": "ok"}), 200

@app.route('/')
def index():
    return "WhatsApp Webhook Server is running. Use /webhook endpoint for Meta integration."


if __name__ == '__main__':
    # Validate required environment variables
    required_vars = ['VERIFY_TOKEN', 'PHONE_NUMBER_ID', 'ACCESS_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"Error: Missing environment variables: {missing_vars}")
        print("Please set these variables in your .env file")
        exit(1)

    print("Starting WhatsApp Webhook Server...")
    print(f"Verify Token: {VERIFY_TOKEN[:5]}..." if VERIFY_TOKEN else "Verify Token: Not set")
    print(f"Phone Number ID: {PHONE_NUMBER_ID}")
    app.run(host='0.0.0.0', port=5000, debug=True)