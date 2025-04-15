import requests

API_KEY = "0b422d5f18874c8996e04ab8ea01fad1"

def testar_conexao_birdeye():
    url = "https://public-api.birdeye.so/defi/v2/tokens/new_listing"
    headers = {
        "X-API-KEY": API_KEY,
        "x-chain": "solana"
    }
    response = requests.get(url, headers=headers)
    
    print("Status Code:", response.status_code)
    
    if response.status_code == 200:
        data = response.json()
        print("Tokens recebidos:", len(data.get("data", [])))
        print("Exemplo:", data.get("data", [])[0] if data.get("data") else "Nenhum token")
    else:
        print("Erro na requisição:", response.text)

testar_conexao_birdeye()
