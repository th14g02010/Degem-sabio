import time
import requests
import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot de sinais ativo com Bitget SPOT", 200

# Configurações
TP_MULT = 2.0
SL_MULT = 1.0
LIMIT = 100
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
ENTRADA_USDT = float(os.getenv("ENTRADA_USDT", 50))  # valor padrão da entrada simulada

erro_reportado = False

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
        print(f"[ERRO] Falha ao enviar mensagem no Telegram: {e}")

def get_klines(symbol="BTCUSDT", interval="1h", limit=LIMIT):
    try:
        print(f"[INFO] Buscando dados de {symbol}...")
        response = requests.get(f"https://api.bitget.com/api/v2/spot/market/candles",
            params={"symbol": symbol, "granularity": interval, "limit": limit}
        )
        data = response.json()
        if "data" in data:
            print(f"[INFO] Dados recebidos com sucesso para {symbol}.")
            return list(reversed(data["data"]))
        else:
            print(f"[WARN] Resposta inesperada da API: {data}")
            return []
    except Exception as e:
        print(f"[ERRO] Erro ao buscar candles: {e}")
        return []

def analisar_padrao(candles):
    try:
        if len(candles) < 2:
            print("[WARN] Não há candles suficientes para análise.")
            return False, None

        anterior = candles[-2]
        atual = candles[-1]

        o1, c1 = float(anterior[1]), float(anterior[4])
        o2, c2 = float(atual[1]), float(atual[4])

        if c1 < o1 and c2 > o2 and c2 > o1 and o2 < c1:
            print("[INFO] Padrão de engolfo de alta detectado.")
            return True, c2
        else:
            print("[INFO] Nenhum padrão encontrado nesse ciclo.")
            return False, None
    except Exception as e:
        print(f"[ERRO] Erro na análise de padrão: {e}")
        return False, None

def main():
    print("[START] Iniciando bot de sinais Bitget...")
    while True:
        candles = get_klines("SOLUSDT", "1h")
        if candles:
            padrao_detectado, preco_entrada = analisar_padrao(candles)
            if padrao_detectado:
                tp = preco_entrada + (TP_MULT * (preco_entrada * 0.01))
                sl = preco_entrada - (SL_MULT * (preco_entrada * 0.01))
                mensagem = (
                    f"*Sinal Detectado!*\n\n"
                    f"Moeda: *SOLUSDT*\n"
                    f"Padrão: *Engolfo de Alta*\n"
                    f"Preço de Entrada: *{preco_entrada:.4f}*\n"
                    f"Take Profit: *{tp:.4f}*\n"
                    f"Stop Loss: *{sl:.4f}*\n"
                    f"Valor Entrada: *${ENTRADA_USDT}*\n"
                    f"Tendência: *Alta*\n"
                )
                send_telegram(mensagem)
        else:
            print("[WARN] Nenhum dado retornado pela API para SOLUSDT.")

        time.sleep(300)  # Espera 5 minutos antes de rodar novamente

if __name__ == "__main__":
    from threading import Thread
    Thread(target=main).start()
    app.run(host="0.0.0.0", port=10000)
