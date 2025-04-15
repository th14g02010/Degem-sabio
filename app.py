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

# Armazenar histórico de avaliações
log_analises = []

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
    falhas = []

    if extras["liquidez"] < LIQUIDEZ_MINIMA:
        falhas.append("LIQUIDEZ < 1500")
    if extras["holders"] < HOLDERS_MINIMO:
        falhas.append("HOLDERS < 50")
    if extras["volume_2h"] < VOLUME_MINIMO:
        falhas.append("VOLUME < 5000")
    if not extras["contrato_seguro"]:
        falhas.append("CONTRATO INSEGURO")
    if extras["taxa_total"] > TAXA_MAXIMA:
        falhas.append("TAXA > 5%")
    if extras["maior_wallet_pct"] > MAX_SUPPLY_POR_CARTEIRA:
        falhas.append("CARTEIRA > 15%")
    if extras["twitter_seguidores"] < TWITTER_SEGUIDORES_MINIMO:
        falhas.append("TWITTER < 500")
    if not extras["tem_site"]:
        falhas.append("SEM SITE")

    aprovado = len(falhas) == 0
    entrada_valor_atual = (VALOR_ENTRADA_USD / extras["preco_inicial"]) * extras["preco_atual"]

    resultado = {
        "nome": token.get("name", "Sem nome"),
        "aprovado": aprovado,
        "falhas": falhas,
        "valor_atual": round(entrada_valor_atual, 2),
        "lucro_prejuizo": round(entrada_valor_atual - VALOR_ENTRADA_USD, 2),
        "preco_inicial": extras["preco_inicial"],
        "preco_atual": extras["preco_atual"],
        "avaliado_em": datetime.utcnow().isoformat() + "Z"
    }

    log_analises.append(resultado)
    if len(log_analises) > 50:
        log_analises.pop(0)

    return resultado

@app.route("/tokens")
def listar_tokens():
    tokens = buscar_tokens_birdeye()
    resultados = [avaliar_token(t) for t in tokens[:10]]
    return jsonify(resultados)

@app.route("/logs")
def mostrar_logs():
    return jsonify(log_analises)

app.run(host="0.0.0.0", port=5000)
