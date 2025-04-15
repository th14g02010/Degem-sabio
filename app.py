import requests
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

# Configuração
API_KEY = "0b422d5f18874c8996e04ab8ea01fad1"
VALOR_ENTRADA_USD = 10
LIQUIDEZ_MINIMA = 1500
HOLDERS_MINIMO = 50
VOLUME_MINIMO = 5000
TAXA_MAXIMA = 0.05
MAX_SUPPLY_POR_CARTEIRA = 0.15
TWITTER_SEGUIDORES_MINIMO = 500

# Função para buscar tokens novos na Solana via Birdeye
def buscar_tokens_birdeye():
    url = "https://public-api.birdeye.so/defi/v2/tokens/new_listing"
    headers = {
        "X-API-KEY": API_KEY,
        "x-chain": "solana"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("data", [])
    return []

# Simulação de dados extras (esses serão reais depois)
def simular_dados_extras(token):
    return {
        "liquidez": 2000,
        "holders": 60,
        "volume_2h": 6000,
        "contrato_seguro": True,
        "taxa_total": 0.03,
        "maior_wallet_pct": 0.14,
        "twitter_seguidores": 750,
        "tem_site": True,
        "preco_inicial": float(token.get("price", 0.0005)),
        "preco_atual": float(token.get("price", 0.0005))
    }

# Avaliar token com base na Regra do Degem Sábio
def avaliar_token(token):
    extras = simular_dados_extras(token)
    aprovado = (
        extras["liquidez"] >= LIQUIDEZ_MINIMA and
        extras["holders"] >= HOLDERS_MINIMO and
        extras["volume_2h"] >= VOLUME_MINIMO and
        extras["contrato_seguro"] and
        extras["taxa_total"] <= TAXA_MAXIMA and
        extras["maior_wallet_pct"] <= MAX_SUPPLY_POR_CARTEIRA and
        extras["twitter_seguidores"] >= TWITTER_SEGUIDORES_MINIMO and
        extras["tem_site"]
    )
    entrada_valor_atual = (VALOR_ENTRADA_USD / extras["preco_inicial"]) * extras["preco_atual"]
    return {
        "nome": token.get("name", "Sem nome"),
        "aprovado": aprovado,
        "valor_atual": round(entrada_valor_atual, 2),
        "lucro_prejuizo": round(entrada_valor_atual - VALOR_ENTRADA_USD, 2),
        "preco_inicial": extras["preco_inicial"],
        "preco_atual": extras["preco_atual"],
        "avaliado_em": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/tokens")
def listar_tokens():
    tokens_birdeye = buscar_tokens_birdeye()
    print("TOKENS RECEBIDOS:", tokens_birdeye)
    resultados = [avaliar_token(t) for t in tokens_birdeye[:10]]
    print("RESULTADOS AVALIADOS:", resultados)
    return jsonify(resultados)

app.run(host="0.0.0.0", port=5000)
