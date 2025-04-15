import requests

def testar_dexscreener_geral():
    url = "https://api.dexscreener.com/latest/dex/pairs"
    response = requests.get(url)

    print("Status Code:", response.status_code)
    if response.status_code == 200:
        data = response.json()
        solana_tokens = [pair for pair in data.get("pairs", []) if pair.get("chainId") == "solana"]
        print("Tokens da Solana encontrados:", len(solana_tokens))
        if solana_tokens:
            print("Exemplo:", solana_tokens[0])
    else:
        print("Erro na requisição:", response.text)

testar_dexscreener_geral()
