from core.database import obter_referencia


def resetar_banco():
    print("Iniciando limpeza do banco de dados SIGA...")

    # Remove o nó de teste
    ref_teste = obter_referencia('teste_conexao')
    ref_teste.delete()

    # Garante que o nó 'ocorrencias' exista (mesmo que vazio)
    ref_ocorr = obter_referencia('ocorrencias')

    print("Banco de dados pronto para uso oficial!")


if __name__ == "__main__":
    confirmacao = input("Isso apagará os dados de teste. Continuar? (s/n): ")
    if confirmacao.lower() == 's':
        resetar_banco()