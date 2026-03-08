import sys
import os

# Mágica para o script conseguir ler as pastas do projeto e achar o .env
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import obter_referencia

def cadastrar_operador():
    print("\n=============================================")
    print("  🛡️ CADASTRAR NOVO OPERADOR - DEFESA CIVIL  ")
    print("=============================================")

    # Coleta os dados digitados por si no terminal
    nome_real = input("Nome de Guerra / Posto (Ex: Sgt Eduardo): ").strip()
    usuario = input("Nome de Login (Ex: eduardo): ").strip().lower()
    senha = input("Senha de Acesso: ").strip()

    if not nome_real or not usuario or not senha:
        print("❌ ERRO: Todos os campos devem ser preenchidos!")
        return

    try:
        print("A conectar à nuvem segura...")
        # Acede à "pasta" de utilizadores no Firebase
        ref = obter_referencia("usuarios")

        # Guarda os dados na nuvem usando o login como chave para não haver repetidos
        ref.child(usuario).set({
            "nome": nome_real,
            "usuario": usuario,
            "senha": senha
        })

        print(f"✅ SUCESSO! O operador '{nome_real}' já pode fazer login no sistema.")

    except Exception as e:
        print(f"❌ ERRO ao salvar no Firebase: {e}")

if __name__ == "__main__":
    while True:
        cadastrar_operador()
        continuar = input("\nDeseja cadastrar mais alguém? (S/N): ").strip().upper()
        if continuar != 'S':
            print("A encerrar o módulo de cadastro.")
            break