import requests

def testar_conexao_dexscreener():
    url = "https://api.dexscreener.com/latest/pairs/solana"  # <- endpoint correto
    response = requests.get(url)
    
    print("Status Code:", response.status_code)
    
    if response.status_code == 200:
        data = response.json()
        print("Total de tokens recebidos:", len(data.get("pairs", [])))
        exemplo = data.get("pairs", [])[0] if data.get("pairs") else None
        print("Exemplo:", exemplo)
    else:
        print("Erro na requisição:", response.text)

testar_conexao_dexscreener()
