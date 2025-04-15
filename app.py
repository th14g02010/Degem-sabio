import time
import requests
import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from threading import Thread

load_dotenv()

app = Flask(__name__)

estado_atual = {
    "status": "Bot iniciado, aguardando dados...",
    "ultimo_sinal": None
}

@app.route("/")
def home():
    return "Bot de sinais ativo com Bitget SPOT", 200

@app.route("/tokens")
def tokens():
    return jsonify(estado_atual), 200

TP_MULT = 2.0
SL_MULT = 1.0
LIMIT = 100
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ENTRADA_USDT = float(os.getenv("ENTRADA_USDT", 50))

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[ERRO] Telegram: {e}")

def get_klines(symbol="SOLUSDT", interval="1h", limit=LIMIT):
    try:
        print(f"[INFO] Buscando dados de {symbol}...")
        response = requests.get("https://api.bitget.com/api/v2/spot/market/candles",
            params={"symbol": symbol, "granularity": interval, "limit": limit})
        data = response.json()
        if "data" in data:
            return list(reversed(data["data"]))
        else:
            print(f"[WARN] Resposta inesperada: {data}")
            return []
    except Exception as e:
        print(f"[ERRO] Erro ao buscar candles: {e}")
        return []

def analisar_padrao(candles):
    if len(candles) < 2:
        return False, None

    anterior = candles[-2]
    atual = candles[-1]
    o1, c1 = float(anterior[1]), float(anterior[4])
    o2, c2 = float(atual[1]), float(atual[4])

    if c1 < o1 and c2 > o2 and c2 > o1 and o2 < c1:
        return True, c2
    return False, None

def main():
    global estado_atual
    print("[START] Bot de sinais rodando...")
    while True:
        candles = get_klines("SOLUSDT", "1h")
        if candles:
            detectado, preco = analisar_padrao(candles)
            if detectado:
                tp = preco + TP_MULT * (preco * 0.01)
                sl = preco - SL_MULT * (preco * 0.01)
                mensagem = (
                    f"*Sinal Detectado!*\n\n"
                    f"Moeda: *SOLUSDT*\n"
                    f"Padrão: *Engolfo de Alta*\n"
                    f"Preço Entrada: *{preco:.4f}*\n"
                    f"Take Profit: *{tp:.4f}*\n"
                    f"Stop Loss: *{sl:.4f}*\n"
                    f"Valor Entrada: *${ENTRADA_USDT}*"
                )
                estado_atual["status"] = "Sinal encontrado"
                estado_atual["ultimo_sinal"] = mensagem
                send_telegram(mensagem)
            else:
                estado_atual["status"] = "Nenhum sinal no momento"
                estado_atual["ultimo_sinal"] = None
        else:
            estado_atual["status"] = "Erro ao buscar dados"
            estado_atual["ultimo_sinal"] = None

        time.sleep(60)  # 1 minuto

if __name__ == "__main__":
    Thread(target=main).start()
    app.run(host="0.0.0.0", port=10000)
