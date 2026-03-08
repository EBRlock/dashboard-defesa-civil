import hashlib
from core.database import obter_referencia


def criar_admin():
    login = "dudu"
    senha = "1234"  # Troque por uma senha segura
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()

    ref = obter_referencia(f'usuarios/{login}')
    ref.set({
        "nome": "Eduardo Lindoso",
        "senha": senha_hash,
        "nivel": "admin"
    })
    print(f"Admin '{login}' criado com sucesso no Firebase!")


if __name__ == "__main__":
    criar_admin()