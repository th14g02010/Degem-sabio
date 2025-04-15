import requests
import threading
from flask import Flask, render_template_string
from datetime import datetime

app = Flask(__name__)

LIQUIDEZ_MINIMA = 1500
VOLUME_MINIMO = 5000

log_analises = []
cache_aprovados = []
tokens_analisados_ids = set()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ titulo }}</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4; }
        h1 { text-align: center; }
        table { width: 100%; border-collapse: collapse; background-color: white; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 10px; text-align: center; font-size: 14px; }
        th { background-color: #222; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .aprovado { background-color: #d4edda; }
    </style>
</head>
<body>
    <h1>{{ titulo }}</h1>
    <table>
        <tr>
            <th>Nome</th>
            <th>Status</th>
            <th>Preço (USD)</th>
            <th>Liquidez</th>
            <th>Volume 2h</th>
            <th>Avaliado Em</th>
            <th>Contrato</th>
            <th>Social</th>
        </tr>
        {% for token in tokens %}
        <tr class="aprovado">
            <td>{{ token.nome }}</td>
            <td>{{ token.status }}</td>
            <td>{{ token.preco_usd }}</td>
            <td>${{ token.liquidez }}</td>
            <td>${{ token.volume_2h }}</td>
            <td>{{ token.avaliado_em }}</td>
            <td><a href="https://solscan.io/token/{{ token.contrato }}" target="_blank">{{ token.contrato[:6] }}...{{ token.contrato[-4:] }}</a></td>
            <td>{% if token.social %}<a href="{{ token.social }}" target="_blank">link{% else %}-{% endif %}</a></td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

def buscar_tokens_gecko(paginas=5):
    tokens = []
    for page in range(1, paginas + 1):
        url = f"https://api.geckoterminal.com/api/v2/networks/solana/pools?page={page}"
        response = requests.get(url)
        if response.status_code == 200:
            tokens += response.json().get("data", [])
    return tokens

def simular_dados_extras(pool):
    attrs = pool.get("attributes", {})
    socials = attrs.get("websites", []) + attrs.get("twitter", [])
    return {
        "nome": attrs.get("name", "Sem nome"),
        "id": pool.get("id"),
        "contrato": pool.get("relationships", {}).get("base_token", {}).get("data", {}).get("id", "").split("_")[-1],
        "liquidez": float(attrs.get("reserve_in_usd", 0)),
        "volume_2h": float(attrs.get("volume_usd", {}).get("h1", 0)) * 2,
        "preco": float(attrs.get("base_token_price_usd", 0.0005)),
        "social": socials[0] if socials else ""
    }

def avaliar_token(pool):
    extras = simular_dados_extras(pool)
    if extras["id"] in tokens_analisados_ids:
        return None

    tokens_analisados_ids.add(extras["id"])

    if (
        extras["liquidez"] >= LIQUIDEZ_MINIMA and
        extras["volume_2h"] >= VOLUME_MINIMO
    ):
        return {
            "nome": extras["nome"],
            "preco_usd": round(extras["preco"], 8),
            "liquidez": round(extras["liquidez"], 2),
            "volume_2h": round(extras["volume_2h"], 2),
            "avaliado_em": datetime.utcnow().isoformat() + "Z",
            "status": "APROVADO",
            "contrato": extras["contrato"],
            "social": extras["social"]
        }
    return None

def escanear_periodicamente():
    global cache_aprovados
    try:
        pools = buscar_tokens_gecko(paginas=5)
        novos = []
        for pool in pools:
            resultado = avaliar_token(pool)
            if resultado:
                novos.append(resultado)
        if novos:
            cache_aprovados.extend(novos)
            cache_aprovados = cache_aprovados[-100:]
            print(f"[{datetime.utcnow().isoformat()}] Escaneados: {len(novos)} novos tokens")
    except Exception as e:
        print("Erro ao escanear:", e)
    threading.Timer(180.0, escanear_periodicamente).start()

@app.route("/tokens")
def mostrar_aprovados():
    return render_template_string(HTML_TEMPLATE, tokens=cache_aprovados, titulo="Tokens Aprovados")

@app.route("/logs")
def mostrar_logs():
    return render_template_string(HTML_TEMPLATE, tokens=cache_aprovados, titulo="Tokens Aprovados (Log Ativo)")

escanear_periodicamente()
app.run(host="0.0.0.0", port=5000)
