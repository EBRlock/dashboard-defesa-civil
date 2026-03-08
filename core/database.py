import firebase_admin
from firebase_admin import credentials, db
import os
from dotenv import load_dotenv

# 1. Descobre onde o database.py está (pasta 'core')
PASTA_CORE = os.path.dirname(os.path.abspath(__file__))

# 2. Descobre a pasta raiz (uma pasta acima da 'core', ou seja, 'DEFESACIVIL')
PASTA_RAIZ = os.path.dirname(PASTA_CORE)

# 3. Força o Python a ler o .env que está exatamente dentro de 'assets'
caminho_env = os.path.join(PASTA_RAIZ, 'assets', '.env')
load_dotenv(caminho_env)


def conectar_defesa_civil():
    # Só conecta se ainda não houver conexão ativa
    if not firebase_admin._apps:

        # Puxa os dados que estão dentro do .env
        nome_arquivo_json = os.getenv("FIREBASE_CREDENTIALS")
        url_banco = os.getenv("FIREBASE_URL")

        # Trava de Segurança 1: Verifica se as variáveis foram carregadas
        if not nome_arquivo_json or not url_banco:
            raise ValueError(f"ERRO: O arquivo .env não foi encontrado em {caminho_env} ou está vazio.")

        # 4. Monta o caminho procurando o arquivo JSON dentro da pasta 'core'
        path_to_json = os.path.join(PASTA_CORE, nome_arquivo_json)

        # Trava de Segurança 2: Verifica se o arquivo JSON existe fisicamente ali
        if not os.path.exists(path_to_json):
            raise FileNotFoundError(
                f"ERRO: O arquivo JSON ({nome_arquivo_json}) não foi encontrado na pasta {PASTA_CORE}!")

        try:
            cred = credentials.Certificate(path_to_json)
            firebase_admin.initialize_app(cred, {
                'databaseURL': url_banco
            })
            print("✅ Conexão DEFESA CIVIL-DATABASE estabelecida com sucesso!")
        except Exception as e:
            raise Exception(f"ERRO ao conectar com o Firebase: {e}")


def obter_referencia(caminho):
    conectar_defesa_civil()
    return db.reference(caminho)


def puxar_dados_brutos(caminho="ocorrencias"):
    """Retorna todos os registros para análise no Dashboard"""
    try:
        ref = obter_referencia(caminho)
        dados = ref.get()
        return dados if dados else {}
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return {}