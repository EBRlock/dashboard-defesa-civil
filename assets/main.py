import sys
import os
from PyQt6.QtGui import QColor, QPixmap, QPainter, QPainterPath, QImage, QIcon
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QFrame,
                             QDialog, QMessageBox, QFileDialog, QGraphicsDropShadowEffect, QLineEdit,
                             QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap, QPainter, QPainterPath, QBitmap, QImage

# ==========================================================
# DETECÇÃO ROBUSTA DE CAMINHOS (Blindagem para logo/env/json)
# ==========================================================
# Esta mágica detecta se estamos no PyCharm ou no .exe final
if getattr(sys, 'frozen', False):
    # Se for .exe, o PyInstaller descompacta tudo numa pasta temporária (_MEIPASS)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # No .exe, ele já aponta pro _internal
else:
    # Se estivermos no PyCharm rodando assets/main.py,
    # a raiz do projeto é uma pasta acima (DEFESACIVIL)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Adiciona a raiz ao sys.path para o Python achar 'modules' e 'core'
sys.path.append(BASE_DIR)

# Nome global da imagem da logo (já corrigido de logo_defesa.png para logo_defesa.png)
FILE_LOGO = "logo_defesa.png"

from modules.datacenter.form_ocorrencia import FormOcorrenciaMapa
from modules.dashboard.painel import PainelDashboard
from core.database import obter_referencia


# ==========================================================
# PAINEL DE ADMINISTRADOR (Gestão de Abas)
# ==========================================================
class PainelAdmin(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PAINEL DO ADMINISTRADOR MESTRE")
        self.setFixedSize(650, 500)
        # Midnight Blue do Eduardo
        self.setStyleSheet("background-color: #191970; font-family: 'Segoe UI', Arial, sans-serif;")
        self.init_ui()
        self.carregar_usuarios()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Sistema de Abas
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #CCCCCC; background: #FFFFFF; border-radius: 4px; }
            QTabBar::tab { background: #E0E0E0; color: #333333; padding: 10px 20px; font-weight: bold; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #FFFFFF; color: #F57C00; border-bottom: 2px solid #F57C00; }
        """)

        # ABA 1: GESTÃO DE USUÁRIOS
        aba_usuarios = QWidget()
        aba_usuarios.setStyleSheet("background-color: #FFFFFF; color: #000000;")
        layout_users = QVBoxLayout(aba_usuarios)

        # Formulário de Cadastro
        form_layout = QHBoxLayout()
        self.txt_nome = QLineEdit();
        self.txt_nome.setPlaceholderText("Nome de Guerra (Ex: Sgt Silva)")
        self.txt_user = QLineEdit();
        self.txt_user.setPlaceholderText("Login (Ex: silva)")
        self.txt_senha = QLineEdit();
        self.txt_senha.setPlaceholderText("Senha")
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Operador", "Administrador"])

        for widget in [self.txt_nome, self.txt_user, self.txt_senha, self.combo_tipo]:
            widget.setStyleSheet(
                "padding: 5px; border: 1px solid #CCC; border-radius: 3px; font-size: 12px; background: #F9F9F9;")
            form_layout.addWidget(widget)

        btn_salvar_user = self._criar_botao("➕ SALVAR USUÁRIO", "#2E7D32", "#1B5E20")
        btn_salvar_user.clicked.connect(self.salvar_usuario)
        form_layout.addWidget(btn_salvar_user)
        layout_users.addLayout(form_layout)

        # Tabela de Usuários
        self.tabela_users = QTableWidget()
        self.tabela_users.setColumnCount(4)
        self.tabela_users.setHorizontalHeaderLabels(["NOME", "LOGIN", "SENHA", "NÍVEL DE ACESSO"])
        self.tabela_users.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabela_users.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela_users.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela_users.setStyleSheet("QTableWidget { border: 1px solid #EEE; alternate-background-color: #F5F5F5; }")
        self.tabela_users.setAlternatingRowColors(True)
        layout_users.addWidget(self.tabela_users)

        # Botão de Excluir
        btn_excluir_user = self._criar_botao("🗑️ EXCLUIR USUÁRIO SELECIONADO", "#D32F2F", "#B71C1C")
        btn_excluir_user.clicked.connect(self.excluir_usuario)
        layout_users.addWidget(btn_excluir_user)

        # ABA 2: BANCO DE DADOS
        aba_db = QWidget()
        aba_db.setStyleSheet("background-color: #FFFFFF;")
        layout_db = QVBoxLayout(aba_db)
        layout_db.addSpacing(20)

        btn_exportar = self._criar_botao("📤 EXPORTAR PARA EXCEL", "#1976D2", "#1565C0")
        layout_db.addWidget(btn_exportar)

        btn_importar = self._criar_botao("📥 IMPORTAR DE EXCEL", "#2E7D32", "#1B5E20")
        layout_db.addWidget(btn_importar)

        layout_db.addStretch()

        btn_zerar = self._criar_botao("🧨 ZERAR BANCO DE DADOS", "#D32F2F", "#B71C1C")
        layout_db.addWidget(btn_zerar)

        # Adiciona as abas ao painel
        self.tabs.addTab(aba_usuarios, "👥 GESTÃO DE EQUIPE")
        self.tabs.addTab(aba_db, "⚙️ BANCO DE DADOS")
        layout.addWidget(self.tabs)

    def _criar_botao(self, texto, cor_fundo, cor_hover):
        btn = QPushButton(texto)
        btn.setFixedHeight(35)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {cor_fundo}; color: #FFFFFF; font-size: 11px; font-weight: bold; border-radius: 4px; border: none; }} QPushButton:hover {{ background-color: {cor_hover}; }}")
        return btn

    def carregar_usuarios(self):
        self.tabela_users.setRowCount(0)
        try:
            ref = obter_referencia("usuarios")
            dados = ref.get()
            if dados:
                self.tabela_users.setRowCount(len(dados))
                for row, (uid, info) in enumerate(dados.items()):
                    self.tabela_users.setItem(row, 0, QTableWidgetItem(info.get("nome", "-")))
                    self.tabela_users.setItem(row, 1, QTableWidgetItem(info.get("usuario", "-")))
                    self.tabela_users.setItem(row, 2, QTableWidgetItem(info.get("senha", "-")))
                    self.tabela_users.setItem(row, 3, QTableWidgetItem(info.get("tipo", "Operador")))
        except Exception as e:
            print(f"Erro ao carregar usuários: {e}")

    def salvar_usuario(self):
        nome = self.txt_nome.text().strip()
        user = self.txt_user.text().strip().lower()
        senha = self.txt_senha.text().strip()
        tipo = self.combo_tipo.currentText()

        if not nome or not user or not senha:
            QMessageBox.warning(self, "Aviso", "Preencha todos os campos!")
            return

        try:
            ref = obter_referencia("usuarios")
            # Salva ou Atualiza a senha se o login já existir
            ref.child(user).set({"nome": nome, "usuario": user, "senha": senha, "tipo": tipo})
            QMessageBox.information(self, "Sucesso", "Usuário salvo/atualizado com sucesso!")
            for txt in [self.txt_nome, self.txt_user, self.txt_senha]: txt.clear()
            self.carregar_usuarios()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar:\n{e}")

    def excluir_usuario(self):
        linha = self.tabela_users.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Aviso", "Selecione um usuário na tabela para excluir.")
            return

        user = self.tabela_users.item(linha, 1).text()
        if user == "admin":
            QMessageBox.warning(self, "Aviso", "Não é possível excluir o Administrador Geral.")
            return

        resposta = QMessageBox.question(self, "Confirmar Exclusão", f"Tem certeza que deseja excluir '{user}'?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resposta == QMessageBox.StandardButton.Yes:
            try:
                obter_referencia("usuarios").child(user).delete()
                self.carregar_usuarios()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao excluir:\n{e}")


# ==========================================================
# HUB PRINCIPAL (Com Controle de Acesso e Tabela Tática)
# ==========================================================
class SigaPrincipal(QMainWindow):
    def __init__(self, usuario_logado="Operador", tipo_usuario="Operador"):
        super().__init__()
        self.usuario_logado = usuario_logado
        self.tipo_usuario = tipo_usuario
        self.setWindowTitle("SISTEMA DEFESA CIVIL - Início")
        self.setMinimumSize(1000, 600)

        # Midnight Blue do Eduardo
        self.setStyleSheet("background-color: #191970; font-family: 'Segoe UI', Arial, sans-serif;")

        self.tela_registro = None
        self.tela_dashboard = None
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Coloque logo abaixo de layout.setAlignment...
        self.setWindowIcon(QIcon(os.path.join(BASE_DIR, "assets", "logo_defesa.ico")))

        container = QFrame()
        container.setFixedSize(450, 520)  # Aumentado um pouco para acomodar os novos espaçamentos
        container.setStyleSheet("""
            QFrame { background-color: rgba(255, 255, 255, 0.12); border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.25); }
            QLabel { background-color: transparent; border: none; }
        """)

        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(25)
        sombra.setColor(QColor(0, 0, 0, 90))
        sombra.setOffset(0, 8)
        container.setGraphicsEffect(sombra)

        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(40, 30, 40, 40)  # Margem superior reduzida
        # vbox.setSpacing(15) # Removido o spacing global para controle manual

        lbl_icone = QLabel()
        path_logo = os.path.join(BASE_DIR, "assets", FILE_LOGO)

        try:
            # Carrega a imagem original
            original_pixmap = QPixmap(path_logo)
            # Redimensiona mantendo a proporção (raio maior de 100px)
            scaled_pixmap = original_pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                                   Qt.TransformationMode.SmoothTransformation)

            # --- MÁGICA: Arredondar a Logo Tática ---
            # Cria uma imagem de máscara arredondada (raio de 30px)
            mask_image = QImage(scaled_pixmap.size(), QImage.Format.Format_ARGB32)
            mask_image.fill(Qt.GlobalColor.transparent)
            painter = QPainter(mask_image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, mask_image.width(), mask_image.height(), 30, 30)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, scaled_pixmap)
            painter.end()

            # Define o resultado mascarado no QLabel
            lbl_icone.setPixmap(QPixmap.fromImage(mask_image))
        except:
            lbl_icone.setText("🛡️")
            lbl_icone.setStyleSheet("font-size: 56px; background: transparent;")

        lbl_icone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(lbl_icone)

        # --- AJUSTE: Espaçamento Coeso ---
        vbox.addSpacing(10)  # 10px entre a logo e o texto "DEFESA CIVIL"

        lbl_titulo = QLabel("DEFESA CIVIL")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF; margin-bottom: 2px;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(lbl_titulo)

        # Saudação com o Cargo!
        lbl_sub = QLabel(f"BEM-VINDO, {self.usuario_logado.upper()}\n[{self.tipo_usuario.upper()}]")
        lbl_sub.setStyleSheet("font-size: 11px; font-weight: bold; color: #F57C00; letter-spacing: 2px;")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(lbl_sub)

        vbox.addSpacing(20)  # 20px antes de começar os botões

        self.btn_reg = self._criar_botao_outline("📝 REGISTRAR OCORRÊNCIA", "#F57C00")
        self.btn_reg.clicked.connect(self.abrir_registro)

        self.btn_dash = self._criar_botao_outline("📊 PAINEL DE DADOS", "#F57C00")
        self.btn_dash.clicked.connect(self.abrir_dashboard)

        self.btn_admin = self._criar_botao_outline("⚙️ PAINEL ADMINISTRADOR", "#F57C00")
        self.btn_admin.clicked.connect(self.abrir_admin)

        if self.tipo_usuario != "Administrador":
            self.btn_admin.setVisible(False)

        self.btn_sair = QPushButton("SAIR DO SISTEMA")
        self.btn_sair.setFixedHeight(45)
        self.btn_sair.setCursor(Qt.CursorShape.PointingHandCursor)
        # Laranja do Eduardo com hover Vermelho Escuro
        self.btn_sair.setStyleSheet(
            "QPushButton { background-color: #F57C00; color: #FFFFFF; font-size: 14px; font-weight: bold; border-radius: 6px; border: none; } QPushButton:hover { background-color: #8B0000; }")
        self.btn_sair.clicked.connect(self.close)

        vbox.addWidget(self.btn_reg)
        vbox.addWidget(self.btn_dash)
        vbox.addWidget(self.btn_admin)
        vbox.addStretch()  # Empurra o botão "SAIR" para baixo
        vbox.addWidget(self.btn_sair)

        layout.addWidget(container)

    def _criar_botao_outline(self, texto, cor_hover):
        btn = QPushButton(texto)
        btn.setFixedHeight(45)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: #FFFFFF; font-size: 13px; font-weight: bold; border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.5); text-align: left; padding-left: 15px; }} QPushButton:hover {{ background-color: {cor_hover}; border: 1px solid {cor_hover}; }}")
        return btn

    def abrir_registro(self):
        self.setCursor(Qt.CursorShape.WaitCursor)
        if not self.tela_registro:
            self.tela_registro = FormOcorrenciaMapa(controlador=self, usuario=self.usuario_logado)
        self.tela_registro.showMaximized()
        self.hide()
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def abrir_dashboard(self):
        self.setCursor(Qt.CursorShape.WaitCursor)
        if not hasattr(self, 'tela_dashboard') or not self.tela_dashboard:
            self.tela_dashboard = PainelDashboard(controlador=self)
        self.tela_dashboard.carregar_dados_firebase()
        self.tela_dashboard.showMaximized()
        self.hide()
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def abrir_admin(self):
        PainelAdmin(self).exec()


# ==========================================================
# NOVA TELA DE LOGIN (Efeito Glassmorphism Tático)
# ==========================================================
class TelaLogin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ACESSO RESTRITO - DEFESA CIVIL")
        self.setMinimumSize(1000, 600)
        # Midnight Blue do Eduardo
        self.setStyleSheet("background-color: #191970; font-family: 'Segoe UI', Arial, sans-serif;")

        self.hub = None
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Coloque logo abaixo de layout.setAlignment...
        self.setWindowIcon(QIcon(os.path.join(BASE_DIR, "assets", "logo_defesa.ico")))

        container = QFrame()
        container.setFixedSize(380, 500)  # Aumentado para acomodar os novos espaçamentos
        container.setStyleSheet("""
            QFrame { background-color: rgba(255, 255, 255, 0.12); border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.25); }
            QLabel { background-color: transparent; border: none; }
        """)

        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(25)
        sombra.setColor(QColor(0, 0, 0, 90))
        sombra.setOffset(0, 8)
        container.setGraphicsEffect(sombra)

        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(40, 30, 40, 40)  # Margem superior reduzida
        # vbox.setSpacing(15) # Removido spacing global

        # --- AJUSTE: Centralização Tática do Bloco Inteiro ---
        vbox.addStretch()  # Empurra tudo para baixo, centralizando o bloco verticalmente

        lbl_icone = QLabel()
        path_logo = os.path.join(BASE_DIR, "assets", FILE_LOGO)

        try:
            original_pixmap = QPixmap(path_logo)
            scaled_pixmap = original_pixmap.scaled(90, 90, Qt.AspectRatioMode.KeepAspectRatio,
                                                   Qt.TransformationMode.SmoothTransformation)

            # --- MÁGICA: Arredondar a Logo do Login (raio de 20px) ---
            mask_image = QImage(scaled_pixmap.size(), QImage.Format.Format_ARGB32)
            mask_image.fill(Qt.GlobalColor.transparent)
            painter = QPainter(mask_image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, mask_image.width(), mask_image.height(), 20, 20)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, scaled_pixmap)
            painter.end()

            lbl_icone.setPixmap(QPixmap.fromImage(mask_image))
        except:
            lbl_icone.setText("🛡️")
            lbl_icone.setStyleSheet("font-size: 56px; color: #FFFFFF;")

        lbl_icone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(lbl_icone)

        # --- AJUSTE: Espaçamento Coeso ---
        vbox.addSpacing(30)  # 10px entre a logo e o título

        lbl_empresa = QLabel("DEFESA CIVIL")
        lbl_empresa.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        lbl_empresa.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(lbl_empresa)

        lbl_titulo = QLabel("ACESSO RESTRITO")
        lbl_titulo.setStyleSheet("font-size: 11px; font-weight: bold; color: #F57C00; letter-spacing: 1px;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(lbl_titulo)

        vbox.addSpacing(20)  # 20px antes de começar os inputs

        estilo_input = "background-color: rgba(0, 0, 0, 0.25); color: #FFFFFF; font-size: 13px; padding: 0 15px; border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 6px;"

        self.txt_usuario = QLineEdit()
        self.txt_usuario.setPlaceholderText("Usuário")
        self.txt_usuario.setFixedHeight(45)
        self.txt_usuario.setStyleSheet(estilo_input)

        self.txt_senha = QLineEdit()
        self.txt_senha.setPlaceholderText("Senha")
        self.txt_senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_senha.setFixedHeight(45)
        self.txt_senha.setStyleSheet(estilo_input)

        self.txt_senha.returnPressed.connect(self.fazer_login)

        btn_entrar = QPushButton("ENTRAR NO SISTEMA")
        btn_entrar.setFixedHeight(45)
        btn_entrar.setCursor(Qt.CursorShape.PointingHandCursor)
        # Laranja do Eduardo com hover Laranja Escuro
        btn_entrar.setStyleSheet(
            "QPushButton { background-color: #F57C00; color: #FFFFFF; font-size: 14px; font-weight: bold; border-radius: 6px; border: none; } QPushButton:hover { background-color: #E65100; }")
        btn_entrar.clicked.connect(self.fazer_login)

        vbox.addWidget(self.txt_usuario)
        vbox.addWidget(self.txt_senha)
        vbox.addSpacing(10)
        vbox.addWidget(btn_entrar)
        vbox.addStretch()  # Empurra tudo para cima, centralizando o bloco verticalmente

        layout.addWidget(container)

    def fazer_login(self):
        usuario = self.txt_usuario.text().strip()
        senha = self.txt_senha.text().strip()

        if not usuario or not senha:
            QMessageBox.warning(self, "Aviso", "Por favor, preencha o utilizador e a senha.")
            return

        self.setCursor(Qt.CursorShape.WaitCursor)

        try:
            # Consulta a tabela de usuários no Firebase
            ref = obter_referencia("usuarios")
            usuarios_db = ref.get()

            # Backdoor do Desenvolvedor
            if usuario == "admin" and senha == "1234":
                self.entrar_sucesso("Administrador Geral", "Administrador")
                return

            # Valida Firebase lendo o 'tipo'
            if usuarios_db:
                for key, val in usuarios_db.items():
                    if val.get("usuario") == usuario and val.get("senha") == senha:
                        nome_real = val.get("nome", usuario)
                        tipo_user = val.get("tipo", "Operador")
                        self.entrar_sucesso(nome_real, tipo_user)
                        return

            QMessageBox.critical(self, "Acesso Negado", "Utilizador ou senha incorretos.")

        except Exception as e:
            QMessageBox.critical(self, "Erro de Conexão", f"Falha ao comunicar com o servidor:\n{e}")
        finally:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def entrar_sucesso(self, nome_operador, tipo_user):
        self.hub = SigaPrincipal(usuario_logado=nome_operador, tipo_usuario=tipo_user)
        self.hub.showMaximized()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TelaLogin()
    window.showMaximized()
    sys.exit(app.exec())