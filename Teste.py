import requests

def testar_conexao_geckoterminal():
    url = "https://api.geckoterminal.com/api/v2/networks/solana/pools?page=1"
    response = requests.get(url)

    print("Status Code:", response.status_code)
    
    if response.status_code == 200:
        data = response.json()
        pools = data.get("data", [])
        print("Total de tokens encontrados:", len(pools))
        if pools:
            print("Exemplo:", pools[0])
    else:
        print("Erro na requisição:", response.text)

testar_conexao_geckoterminal()
