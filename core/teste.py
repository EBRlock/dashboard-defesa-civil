from core.database import obter_referencia

try:
    print("Testando conexão com o Firebase...")
    ref = obter_referencia('teste_conexao')
    ref.set({"status": "Online", "mensagem": "SIGA conectado com sucesso!"})
    print("Dados gravados na nuvem! Verifique o console do Firebase.")
except Exception as e:
    print(f"Erro na configuração: {e}")