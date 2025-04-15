import requests
import threading
from flask import Flask, render_template_string
from datetime import datetime

app = Flask(__name__)

# Configurações da Regra do Degem Sábio
VALOR_ENTRADA_USD = 10
LIQUIDEZ_MINIMA = 1500
HOLDERS_MINIMO = 50
VOLUME_MINIMO = 5000
TAXA_MAXIMA = 0.05
MAX_SUPPLY_POR_CARTEIRA = 0.15
TWITTER_SEGUIDORES_MINIMO = 500

# Cache de dados
log_analises = []
cache_aprovados = []

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ titulo }}</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4; }
        h1 { text-align: center; }
        table { width: 100%; border-collapse: collapse; background-color: white; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 10px; text-align: center; }
        th { background-color: #222; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .aprovado { background-color: #d4edda; }
        .reprovado { background-color: #f8d7da; }
    </style>
</head>
<body>
    <h1>{{ titulo }}</h1>
    <table>
        <tr>
            <th>Nome</th>
            <th>Status</th>
            <th>Preço (USD)</th>
            <th>Valor Atual (USD)</th>
            <th>Lucro/Prejuízo</th>
            <th>Avaliado Em</th>
            <th>Falhas</th>
        </tr>
        {% for token in tokens %}
        <tr class="{{ 'aprovado' if token.status == 'APROVADO' else 'reprovado' }}">
            <td>{{ token.nome }}</td>
            <td>{{ token.status }}</td>
            <td>{{ token.preco_usd }}</td>
            <td>{{ token.valor_atual_usd }}</td>
            <td>{{ token.lucro_prejuizo_usd }}</td>
            <td>{{ token.avaliado_em }}</td>
            <td>{{ token.falhas|join(', ') }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

# Buscar tokens da GeckoTerminal
def buscar_tokens_gecko():
    url = "https://api.geckoterminal.com/api/v2/networks/solana/pools?page=1"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("data", [])
    return []

# Simular dados extras para análise (pode ser substituído por dados reais)
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

# Avaliar token com base na regra do Degem Sábio
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

    return {
        "nome": extras["nome"],
        "preco_usd": round(extras["preco"], 8),
        "valor_atual_usd": round(valor_atual, 2),
        "lucro_prejuizo_usd": round(valor_atual - VALOR_ENTRADA_USD, 2),
        "avaliado_em": datetime.utcnow().isoformat() + "Z",
        "status": "APROVADO" if aprovado else "REPROVADO",
        "falhas": falhas
    }

# Escaneamento automático a cada 3 minutos
def escanear_periodicamente():
    global cache_aprovados, log_analises
    try:
        pools = buscar_tokens_gecko()
        resultados = [avaliar_token(p) for p in pools[:10]]
        cache_aprovados = [r for r in resultados if r["status"] == "APROVADO"]
        log_analises.extend(resultados)
        log_analises = log_analises[-50:]
        print(f"[{datetime.utcnow().isoformat()}] Escaneamento feito com {len(resultados)} tokens.")
    except Exception as e:
        print("Erro ao escanear:", e)
    threading.Timer(180.0, escanear_periodicamente).start()

@app.route("/tokens")
def mostrar_aprovados():
    return render_template_string(HTML_TEMPLATE, tokens=cache_aprovados, titulo="Tokens Aprovados")

@app.route("/logs")
def mostrar_logs():
    return render_template_string(HTML_TEMPLATE, tokens=log_analises, titulo="Logs do Bot - Degem Sábio")

# Inicia escaneamento recorrente
escanear_periodicamente()
app.run(host="0.0.0.0", port=5000)
