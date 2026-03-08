from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .database import Base, engine

class Ocorrencia(Base):
    __tablename__ = 'ocorrencias'

    id = Column(Integer, primary_key=True, autoincrement=True)
    solicitante = Column(String(255), nullable=False)
    local = Column(String(255))
    municipio = Column(String(100))
    bairro = Column(String(100))
    rua = Column(String(255))
    data_hora = Column(DateTime, default=datetime.now)
    natureza = Column(String(100))
    risco = Column(String(50))
    encaminhamento = Column(String(100))
    status = Column(String(50), default="Ativo")

# Cria as tabelas automaticamente se não existirem
Base.metadata.create_all(bind=engine)