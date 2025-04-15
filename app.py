import requests
import threading
from flask import Flask, render_template_string
from datetime import datetime

app = Flask(__name__)

# Critérios configuráveis
LIQUIDEZ_MINIMA = 1500
HOLDERS_MINIMO = 50
VOLUME_MINIMO = 5000
TAXA_MAXIMA = 0.05
MAX_SUPPLY_POR_CARTEIRA = 0.15
TWITTER_MINIMO = 500

tokens_analisados = {}
tokens_por_criterio = {}
novos_por_criterio = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Degem Sábio - Filtros</title>
    <style>
        body { font-family: Arial; background-color: #f4f4f4; padding: 20px; }
        h1 { text-align: center; }
        .tabs { overflow: hidden; background: #222; margin-top: 20px; }
        .tabs a { float: left; padding: 14px 16px; text-decoration: none; color: white; display: block; }
        .tabs a:hover { background-color: #575757; }
        .tabs a.active { background-color: #4CAF50; }
        .tabs a.novo { background-color: #ff9800 !important; }

        .content { display: none; padding: 20px; background: white; border: 1px solid #ccc; }
        .content.active { display: block; }

        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: center; font-size: 14px; }
        th { background: #444; color: white; }
        tr:nth-child(even) { background: #f9f9f9; }
    </style>
    <script>
        function showTab(id) {
            var tabs = document.getElementsByClassName('content');
            for (var i = 0; i < tabs.length; i++) {
                tabs[i].classList.remove('active');
            }
            document.getElementById(id).classList.add('active');

            var links = document.querySelectorAll('.tabs a');
            links.forEach(link => link.classList.remove('active'));
            document.getElementById("tablink_" + id).classList.add("active");
        }
        window.onload = function() { showTab('aprovados'); };
    </script>
</head>
<body>
    <h1>Degem Sábio - Filtros por Critério</h1>

    <div class="tabs">
        {% for chave in tokens_por_criterio %}
        <a href="#" id="tablink_{{ chave }}" onclick="showTab('{{ chave }}')" class="{% if chave in novos_por_criterio and novos_por_criterio[chave] > 0 %}novo{% endif %}">{{ chave.replace('_', ' ').title() }}</a>
        {% endfor %}
    </div>

    {% for chave, tokens in tokens_por_criterio.items() %}
    <div class="content" id="{{ chave }}">
        <h2>{{ chave.replace('_', ' ').title() }}</h2>
        <table>
            <tr>
                <th>Nome</th>
                <th>Preço</th>
                <th>Liquidez</th>
                <th>Volume 2h</th>
                <th>Taxa</th>
                <th>Distribuição</th>
                <th>Twitter</th>
                <th>Avaliado</th>
                <th>Contrato</th>
                <th>Social</th>
            </tr>
            {% for t in tokens %}
            <tr>
                <td>{{ t.nome }}</td>
                <td>{{ t.preco_usd }}</td>
                <td>${{ t.liquidez }}</td>
                <td>${{ t.volume_2h }}</td>
                <td>{{ t.taxa_total }}%</td>
                <td>{{ (t.maior_wallet_pct * 100)|round(2) }}%</td>
                <td>{{ t.twitter_seguidores }}</td>
                <td>{{ t.avaliado_em }}</td>
                <td><a href="https://solscan.io/token/{{ t.contrato }}" target="_blank">{{ t.contrato[:6] }}...{{ t.contrato[-4:] }}</a></td>
                <td>{% if t.social %}<a href="{{ t.social }}" target="_blank">link{% else %}-{% endif %}</a></td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endfor %}
</body>
</html>
"""

def buscar_tokens_gecko(paginas=10):
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
        "contrato": pool.get("relationships").get("base_token", {}).get("data", {}).get("id", "").split("_")[-1],
        "liquidez": float(attrs.get("reserve_in_usd", 0)),
        "volume_2h": float(attrs.get("volume_usd", {}).get("h1", 0)) * 2,
        "preco_usd": float(attrs.get("base_token_price_usd", 0.0005)),
        "social": socials[0] if socials else "",
        "holders": 60,
        "contrato_seguro": True,
        "taxa_total": 0.03,
        "maior_wallet_pct": 0.14,
        "twitter_seguidores": 800,
        "avaliado_em": datetime.utcnow().isoformat() + "Z"
    }

def escanear_periodicamente():
    global tokens_analisados, tokens_por_criterio, novos_por_criterio
    novos_por_criterio = {k: 0 for k in tokens_por_criterio.keys()}
    criterios = {
        "liquidez": lambda t: t["liquidez"] >= LIQUIDEZ_MINIMA,
        "holders": lambda t: t["holders"] >= HOLDERS_MINIMO,
        "volume_2h": lambda t: t["volume_2h"] >= VOLUME_MINIMO,
        "contrato_seguro": lambda t: t["contrato_seguro"],
        "taxa": lambda t: t["taxa_total"] <= TAXA_MAXIMA,
        "distribuicao": lambda t: t["maior_wallet_pct"] <= MAX_SUPPLY_POR_CARTEIRA,
        "twitter": lambda t: t["twitter_seguidores"] >= TWITTER_MINIMO,
        "rede_social": lambda t: t["social"] != "",
        "aprovados": lambda t: (
            t["liquidez"] >= LIQUIDEZ_MINIMA and
            t["holders"] >= HOLDERS_MINIMO and
            t["volume_2h"] >= VOLUME_MINIMO and
            t["contrato_seguro"] and
            t["taxa_total"] <= TAXA_MAXIMA and
            t["maior_wallet_pct"] <= MAX_SUPPLY_POR_CARTEIRA and
            t["twitter_seguidores"] >= TWITTER_MINIMO and
            t["social"] != ""
        )
    }

    for nome in criterios.keys():
        tokens_por_criterio.setdefault(nome, [])

    pools = buscar_tokens_gecko(paginas=10)
    for pool in pools:
        token = simular_dados_extras(pool)
        token_id = token["id"]
        tokens_analisados[token_id] = token  # atualiza sempre

        for nome, regra in criterios.items():
            grupo = tokens_por_criterio[nome]
            if regra(token):
                if all(t["id"] != token_id for t in grupo):
                    grupo.append(token)
                    novos_por_criterio[nome] = novos_por_criterio.get(nome, 0) + 1

    print(f"[{datetime.utcnow().isoformat()}] Escaneados e organizados.")
    threading.Timer(180.0, escanear_periodicamente).start()

@app.route("/")
def painel():
    return render_template_string(HTML_TEMPLATE, tokens_por_criterio=tokens_por_criterio, novos_por_criterio=novos_por_criterio)

escanear_periodicamente()
app.run(host="0.0.0.0", port=5000)
