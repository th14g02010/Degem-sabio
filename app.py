import requests
import json
from datetime import datetime, timedelta
import time

# Função para verificar se o token atende a 7 de 8 critérios
def aprovado_criterios(criterios):
    # Contar quantos critérios o token passou
    passed_criterios = sum(criterios.values())
    return passed_criterios >= 7  # Token é aprovado se passar em pelo menos 7 de 8 critérios

# Função para buscar dados dos tokens
def buscar_tokens():
    url = 'https://api.dexscreener.com/latest/tokens'
    response = requests.get(url)
    tokens = response.json()
    return tokens['tokens']

# Função para filtrar tokens de acordo com os critérios ajustados
def filtrar_tokens(tokens):
    tokens_aprovados = []
    
    for token in tokens:
        criterios = {
            "liquidez": token["liquidez"] >= 1500,
            "holders": token["holders"] >= 50,
            "volume_2h": token["volume_2h"] >= 5000,
            "seguro": token["seguro"] == True,
            "taxa": token["taxa"] <= 5,
            "maior_carteira": token["maior_carteira"] <= 15,
            "twitter": token["twitter_seguidores"] >= 500,
            "rede_social": token["rede_social"] is not None
        }

        if aprovado_criterios(criterios):
            tokens_aprovados.append(token)
    
    return tokens_aprovados

# Função para formatar e mostrar os tokens aprovados
def mostrar_tokens_aprovados(tokens):
    html = "<html><body><h1>Tokens Aprovados</h1><table border='1'><tr><th>Nome</th><th>Liquidez</th><th>Holders</th><th>Volume 2h</th><th>Taxa</th><th>Maior Carteira</th><th>Twitter Seguidores</th><th>Rede Social</th></tr>"
    
    for token in tokens:
        html += f"<tr style='background-color: #d3ffd3;'><td>{token['nome']}</td><td>{token['liquidez']}</td><td>{token['holders']}</td><td>{token['volume_2h']}</td><td>{token['taxa']}</td><td>{token['maior_carteira']}</td><td>{token['twitter_seguidores']}</td><td>{token['rede_social']}</td></tr>"
    
    html += "</table></body></html>"
    return html

# Função principal que vai rodar o script
def run():
    while True:
        tokens = buscar_tokens()
        tokens_aprovados = filtrar_tokens(tokens)
        html_aprovado = mostrar_tokens_aprovados(tokens_aprovados)
        
        # Aqui você pode salvar o html ou enviar para uma interface para visualizar
        with open('tokens_aprovados.html', 'w') as f:
            f.write(html_aprovado)
        
        # Esperar 3 minutos para a próxima busca
        time.sleep(180)

# Executar o script
if __name__ == '__main__':
    run()
