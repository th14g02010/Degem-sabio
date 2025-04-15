import requests
from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

# Configuração
VALOR_ENTRADA_USD = 10
LIQUIDEZ_MINIMA = 1500
HOLDERS_MINIMO = 50
VOLUME_MINIMO = 5000
TAXA_MAXIMA = 0.05
MAX_SUPPLY_POR_CARTEIRA = 0.15
TWITTER_SEGUIDORES_MINIMO = 500

log_analises = []

# Função para buscar os pares da Solana via GeckoTerminal
def buscar_tokens_gecko():
    url = "https://api.geckoterminal.com/api/v2/networks/solana/pools?page=1"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("data", [])
    return []

# Simula dados complementares até termos fontes reais
def simular_dados_extras(pool):
    attrs = pool.get("attributes", {})
    return {
        "nome": attrs.get("name", "Sem nome"),
        "liquidez": float(attrs.get("reserve_in_usd", 0)),
        "holders": 60,
        "volume_2h": float(attrs.get("volume_usd", {}).get("h1", 0)) * 2,
        "contrato_seguro": True,
        "taxa_total": 0.03,
        "maior_wallet_pct": 0.14,
        "twitter_seguidores": 750,
        "tem_site": True,
        "preco": float(attrs.get("base_token_price_usd", 0.0005))
    }

# Avalia os critérios da Regra do Degem Sábio
def avaliar_token(pool):
    extras = simular_dados_extras(pool)
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
    valor_atual = (VALOR_ENTRADA_USD / extras["preco"]) * extras["preco"]

    resultado = {
        "nome": extras["nome"],
        "aprovado": aprovado,
        "falhas": falhas,
        "valor_atual": round(valor_atual, 2),
        "lucro_prejuizo": round(valor_atual - VALOR_ENTRADA_USD, 2),
        "preco_inicial": extras["preco"],
        "preco_atual": extras["preco"],
        "avaliado_em": datetime.utcnow().isoformat() + "Z"
    }

    log_analises.append(resultado)
    if len(log_analises) > 50:
        log_analises.pop(0)

    return resultado

@app.route("/tokens")
def listar_tokens():
    pools = buscar_tokens_gecko()
    resultados = [avaliar_token(p) for p in pools[:10]]
    return jsonify(resultados)

@app.route("/logs")
def mostrar_logs():
    return jsonify(log_analises)

app.run(host="0.0.0.0", port=5000)
