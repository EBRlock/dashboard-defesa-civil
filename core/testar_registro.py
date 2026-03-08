from core.database import obter_referencia
from datetime import datetime

# Simulando um registro oficial
nova_ocorr = {
    "solicitante": "SGT Eduardo",
    "bairro": "Jorge Teixeira",
    "natureza": "ALAGAMENTO",
    "risco": "Alto",
    "status": "Ativo",
    "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
}

try:
    ref = obter_referencia('ocorrencias')
    ref.push(nova_ocorr)
    print("Sucesso! Verifique o console do Firebase agora.")
except Exception as e:
    print(f"Erro ao criar nó: {e}")