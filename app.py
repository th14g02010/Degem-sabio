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

# Simulação de tokens (em produção, isso viria da Birdeye ou outra API)
tokens_exemplo = [
    {
        "nome": "MemeCat",
        "liquidez": 2000,
        "holders": 65,
        "volume_2h": 7000,
        "contrato_seguro": True,
        "taxa_total": 0.03,
        "maior_wallet_pct": 0.12,
        "twitter_seguidores": 800,
        "tem_site": True,
        "preco_inicial": 0.0005,
        "preco_atual": 0.0008
    },
    {
        "nome": "RugDog",
        "liquidez": 800,
        "holders": 30,
        "volume_2h": 2000,
        "contrato_seguro": False,
        "taxa_total": 0.10,
        "maior_wallet_pct": 0.40,
        "twitter_seguidores": 150,
        "tem_site": False,
        "preco_inicial": 0.002,
        "preco_atual": 0.0009
    }
]

def avaliar_token(token):
    aprovado = (
        token["liquidez"] >= LIQUIDEZ_MINIMA and
        token["holders"] >= HOLDERS_MINIMO and
        token["volume_2h"] >= VOLUME_MINIMO and
        token["contrato_seguro"] and
        token["taxa_total"] <= TAXA_MAXIMA and
        token["maior_wallet_pct"] <= MAX_SUPPLY_POR_CARTEIRA and
        token["twitter_seguidores"] >= TWITTER_SEGUIDORES_MINIMO and
        token["tem_site"]
    )
    entrada_valor_atual = (VALOR_ENTRADA_USD / token["preco_inicial"]) * token["preco_atual"]
    return {
        "nome": token["nome"],
        "aprovado": aprovado,
        "valor_atual": round(entrada_valor_atual, 2),
        "lucro_prejuizo": round(entrada_valor_atual - VALOR_ENTRADA_USD, 2),
        "preco_inicial": token["preco_inicial"],
        "preco_atual": token["preco_atual"],
        "avaliado_em": datetime.utcnow().isoformat() + "Z"
    }

@app.route("/tokens")
def listar_tokens():
    resultados = [avaliar_token(t) for t in tokens_exemplo]
    return jsonify(resultados)

app.run(host="0.0.0.0", port=5000)
