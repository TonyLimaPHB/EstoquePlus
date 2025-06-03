import sys
import shutil
import os
import sqlite3
import time
from datetime import datetime
import csv
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QLineEdit, QFileDialog, QMessageBox, QListWidget, QListWidgetItem, QDialog,
    QGroupBox, QFormLayout, QMenu, QMenuBar
)
from PySide6.QtGui import QFont, QPixmap, QAction, QIcon
from PySide6.QtCore import Qt, QPoint, QSize, QSettings


# === CLASSE PARA GERENCIAR USUÁRIOS E MERCADORIAS NO BANCO DE DADOS ===
class DatabaseManager:
    def __init__(self):
        self.db_name = "stock_control.db"
        self.create_tables()

    def create_tables(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        ''')
        # Tabela de mercadorias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mercadorias (
                id TEXT PRIMARY KEY,
                nome TEXT,
                preco_compra REAL,
                preco_venda REAL,
                qtd_comprada INTEGER,
                qtd_saida INTEGER,
                descricao TEXT,
                valor_total_compra REAL,
                valor_total_venda REAL,
                imagem_path TEXT
            )
        ''')
        conn.commit()
        conn.close()


# === DIÁLOGO DE LOGIN COM LOGO DA EMPRESA ===
class LoginDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("👤🔒 Login")
        self.setFixedSize(350, 250)
        self.db_manager = db_manager
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Logo da Empresa
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)

        logo_path = os.path.join("imagens", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(200, 100, Qt.AspectRatioMode.KeepAspectRatio)
            self.logo_label.setPixmap(pixmap)
        else:
            self.logo_label.setText("🧾 Controle Stock\nVersão 1.0")
            self.logo_label.setFont(QFont("Arial", 10, QFont.Bold))
            self.logo_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.logo_label)

        # Campos de login
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Usuário")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Senha")
        self.password_input.setEchoMode(QLineEdit.Password)

        login_button = QPushButton("Entrar")
        login_button.clicked.connect(self.verify_login)

        layout.addSpacing(10)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_button)

        # Rodapé - Informações do desenvolvedor
        rodape_label = QLabel("🧾 Controle Stock - Desenvolvido por +55 86 98119-2287")
        rodape_label.setAlignment(Qt.AlignCenter)
        rodape_label.setStyleSheet("font-size: 10px; color: #666666;")
        layout.addWidget(rodape_label)

        self.setLayout(layout)
        self.center_window()  # Centraliza a janela

    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        window_rect = self.frameGeometry()
        x = int((screen.width() - window_rect.width()) / 2)
        y = int((screen.height() - window_rect.height()) / 2)
        self.move(x, y)

    def verify_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if self.check_user(username, password):
            self.accept()
        else:
            QMessageBox.warning(self, "Erro", "Credenciais inválidas!")

    def check_user(self, username, password):
        conn = sqlite3.connect(self.db_manager.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        result = cursor.fetchone()
        conn.close()
        return result is not None


# === DIÁLOGO PARA CRIAR USUÁRIO ===
class CreateUserDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Criar Usuário")
        self.setFixedSize(300, 150)
        self.db_manager = db_manager
        layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Novo usuário")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Nova senha")
        self.password_input.setEchoMode(QLineEdit.Password)

        create_button = QPushButton("Criar Usuário")
        create_button.clicked.connect(self.create_user)

        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(create_button)

        # Rodapé - Informações do desenvolvedor
        rodape_label = QLabel("🧾 Controle Stock - Desenvolvido por +55 86 98119-2287")
        rodape_label.setAlignment(Qt.AlignCenter)
        rodape_label.setStyleSheet("font-size: 10px; color: #666666;")
        layout.addWidget(rodape_label)

        self.setLayout(layout)

    def create_user(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if username and password:
            try:
                conn = sqlite3.connect(self.db_manager.db_name)
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Sucesso", "Usuário criado com sucesso!")
                self.accept()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Erro", "Usuário já existe.")
        else:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos!")


# === JANELA DE DETALHES DO PRODUTO ===
class DetalhesProdutoDialog(QDialog):
    def __init__(self, id_produto, nome, preco_compra, preco_venda, qtd_comprada, qtd_saida,
                 descricao, valor_total_compra, valor_total_venda, imagem_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Detalhes - {nome}")
        self.resize(500, 500)
        self.id_produto = id_produto
        self.preco_compra = preco_compra
        self.qtd_comprada_atual = qtd_comprada
        layout = QVBoxLayout()

        # Imagem
        imagem_label = QLabel()
        pixmap = QPixmap(imagem_path).scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
        imagem_label.setPixmap(pixmap)
        imagem_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(imagem_label)

        # Informações do produto
        lucro_por_unidade = round(preco_venda - preco_compra, 2)
        lucro_total = round(lucro_por_unidade * qtd_saida, 2)
        info = f"""
        <b>Nome:</b> {nome}<br>
        <b>ID:</b> {id_produto}<br>
        <b>Descrição:</b> {descricao}<br><br>
        <b>Preço Compra:</b> R${preco_compra:.2f}<br>
        <b>Preço Venda:</b> R${preco_venda:.2f}<br><br>
        <b>Quantidade Comprada:</b> {qtd_comprada}<br>
        <b>Quantidade Vendida:</b> {qtd_saida}<br>
        <b>Quantidade Restante:</b> {qtd_comprada - qtd_saida}<br><br>
        <b>Total Compra:</b> R${valor_total_compra:.2f}<br>
        <b>Total Venda:</b> R${valor_total_venda:.2f}<br><br>
        <b>Lucro por Unidade:</b> R${lucro_por_unidade:.2f}<br>
        <b>Lucro Estimado Total:</b> R${lucro_total:.2f}
        """
        info_label = QLabel(info)
        info_label.setTextFormat(Qt.RichText)
        info_label.setWordWrap(True)  # Habilita quebra automática de linha
        layout.addWidget(info_label)

        # Campo para adicionar mais estoque
        self.nova_qtd_input = QLineEdit()
        self.nova_qtd_input.setPlaceholderText("Digite quantidade adicional")
        layout.addWidget(self.nova_qtd_input)

        btn_adicionar = QPushButton("📦 Adicionar ao Estoque")
        btn_adicionar.clicked.connect(lambda: self.adicionar_estoque(parent))
        layout.addWidget(btn_adicionar)

        btn_excluir = QPushButton("🗑️ Excluir Produto")
        btn_excluir.clicked.connect(lambda: self.excluir_produto(parent))
        layout.addWidget(btn_excluir)

        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        # Rodapé - Informações do desenvolvedor
        rodape_label = QLabel("🧾 Controle Stock - Desenvolvido por +55 86 98119-2287")
        rodape_label.setAlignment(Qt.AlignCenter)
        rodape_label.setStyleSheet("font-size: 10px; color: #666666;")
        layout.addWidget(rodape_label)

        self.setLayout(layout)

    def adicionar_estoque(self, parent):
        try:
            nova_qtd = int(self.nova_qtd_input.text())
            if nova_qtd <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Erro", "Digite uma quantidade válida maior que zero.")
            return

        conn = sqlite3.connect("stock_control.db")
        cursor = conn.cursor()
        cursor.execute('SELECT qtd_comprada FROM mercadorias WHERE id = ?', (self.id_produto,))
        resultado = cursor.fetchone()

        if resultado:
            qc_atual = resultado[0]
            novo_qc = qc_atual + nova_qtd
            novo_vtc = self.preco_compra * novo_qc

            cursor.execute('''
                UPDATE mercadorias 
                SET qtd_comprada = ?, valor_total_compra = ?
                WHERE id = ?
            ''', (novo_qc, novo_vtc, self.id_produto))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Sucesso", f"{nova_qtd} unidades adicionadas ao estoque.")

            self.nova_qtd_input.clear()
            self.accept()
            parent.listar_mercadorias()
        else:
            QMessageBox.warning(self, "Erro", "Produto não encontrado.")

    def excluir_produto(self, parent):
        reply = QMessageBox.question(self, 'Exclusão',
                                     f"Tem certeza que deseja excluir '{self.id_produto}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = sqlite3.connect("stock_control.db")
            cursor = conn.cursor()
            cursor.execute('DELETE FROM mercadorias WHERE id = ?', (self.id_produto,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Exclusão", "Produto excluído com sucesso.")
            self.accept()
            parent.listar_mercadorias()


# === APLICAÇÃO PRINCIPAL ===
class CadastroMercadoriasApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📦💡EstoquePlus")
        self.load_window_geometry()
        self.dark_mode = False
        self.initUI()
        self.listar_mercadorias()
        print("✅ Sistema iniciado")

    def initUI(self):
        # Definindo o ícone da janela para "janela.ico"
        self.setWindowIcon(QIcon("imagens/janela.ico"))

        # Menu superior
        self.menu_bar = QMenuBar(self)
        file_menu = self.menu_bar.addMenu("Arquivo")

        backup_action = QAction("Salvar Backup", self)
        backup_action.triggered.connect(self.realizar_backup)
        file_menu.addAction(backup_action)

        exit_action = QAction("Sair", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        theme_menu = self.menu_bar.addMenu("Tema")
        self.toggle_theme_action = QAction("🌙 Modo Escuro", self)
        self.toggle_theme_action.triggered.connect(self.toggle_theme)
        theme_menu.addAction(self.toggle_theme_action)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 30, 10, 10)

        titulo = QLabel("🛒📈 Cadastro de Mercadorias 🛍️🔖🏷️💰")
        titulo.setFont(QFont("Arial", 18, QFont.Bold))
        titulo.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(titulo)

        cadastro_group = QGroupBox("Cadastro de Mercadoria")
        form = QFormLayout()

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("ID do Produto")

        self.nome_input = QLineEdit()
        self.nome_input.setPlaceholderText("Nome da Mercadoria")

        self.preco_compra_input = QLineEdit()
        self.preco_compra_input.setPlaceholderText("Ex: 10.50")

        self.preco_venda_input = QLineEdit()
        self.preco_venda_input.setPlaceholderText("Ex: 19.99")

        self.qtd_comprada_input = QLineEdit()
        self.qtd_comprada_input.setPlaceholderText("Quantidade Comprada")

        self.descricao_input = QLineEdit()
        self.descricao_input.setPlaceholderText("Descrição do Produto")

        self.imagem_label = QLabel("Nenhuma imagem selecionada")
        self.imagem_label.setAlignment(Qt.AlignCenter)
        self.imagem_button = QPushButton("Selecionar Imagem")
        self.imagem_button.clicked.connect(self.selecionar_imagem)

        form.addRow("ID Produto:", self.id_input)
        form.addRow("Nome:", self.nome_input)
        form.addRow("Preço Compra (R$):", self.preco_compra_input)
        form.addRow("Preço Venda (R$):", self.preco_venda_input)
        form.addRow("Qtd Comprada:", self.qtd_comprada_input)
        form.addRow("Descrição:", self.descricao_input)
        form.addRow("Imagem:", self.imagem_button)

        cadastro_group.setLayout(form)
        main_layout.addWidget(cadastro_group)

        cadastrar_button = QPushButton("Cadastrar / Atualizar Mercadoria")
        cadastrar_button.clicked.connect(self.cadastrar_mercadoria)
        main_layout.addWidget(cadastrar_button)

        # Campo de busca
        self.busca_input = QLineEdit()
        self.busca_input.setPlaceholderText("Buscar por Nome, ID ou Descrição...")
        self.busca_input.textChanged.connect(self.listar_mercadorias)
        main_layout.addWidget(self.busca_input)

        listar_button = QPushButton("Listar Mercadorias")
        listar_button.clicked.connect(self.listar_mercadorias)
        main_layout.addWidget(listar_button)

        self.lista_widget = QListWidget()
        self.lista_widget.itemClicked.connect(self.exibir_detalhes_produto)
        main_layout.addWidget(self.lista_widget)

        self.setLayout(main_layout)

    def load_window_geometry(self):
        settings = QSettings("MinhaEmpresa", "ControleStock")
        pos = settings.value("window_position", QPoint(300, 300))
        size = settings.value("window_size", QSize(900, 700))
        self.resize(size)
        self.move(pos)

    def save_window_geometry(self):
        settings = QSettings("MinhaEmpresa", "ControleStock")
        settings.setValue("window_position", self.pos())
        settings.setValue("window_size", self.size())

    def closeEvent(self, event):
        self.save_window_geometry()
        super().closeEvent(event)

    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        window_rect = self.frameGeometry()
        x = int((screen.width() - window_rect.width()) / 2)
        y = int((screen.height() - window_rect.height()) / 2)
        self.move(x, y)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.setStyleSheet("""
                background-color: #2e2e2e;
                color: white;
                font-family: Arial;
            """)
            self.toggle_theme_action.setText("☀️ Modo Claro")
        else:
            self.setStyleSheet("")
            self.toggle_theme_action.setText("🌙 Modo Escuro")

    def selecionar_imagem(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar Imagem",
                                                  "", "Imagens (*.png *.jpg *.jpeg)")
        if file_path:
            self.imagem_path = file_path
            pixmap = QPixmap(file_path).scaled(125, 125, Qt.AspectRatioMode.IgnoreAspectRatio)
            self.imagem_label.setPixmap(pixmap)

    def cadastrar_mercadoria(self):
        id_p = self.id_input.text().strip()
        nome = self.nome_input.text().strip()
        desc = self.descricao_input.text().strip()

        try:
            pc = float(self.preco_compra_input.text())
            pv = float(self.preco_venda_input.text())
            qc = int(self.qtd_comprada_input.text())
        except ValueError:
            QMessageBox.warning(self, "Erro", "Valores numéricos inválidos.")
            return

        if not all([id_p, nome, desc, hasattr(self, 'imagem_path'), pc > 0, pv > 0, qc >= 0]):
            QMessageBox.warning(self, "Erro", "Preencha todos os campos corretamente!")
            return

        destino_dir = "imagens"
        if not os.path.exists(destino_dir):
            os.makedirs(destino_dir)

        ext = os.path.splitext(self.imagem_path)[1]
        novo_nome = f"{id_p}_{nome}{ext}"
        destino = os.path.join(destino_dir, novo_nome)
        shutil.copy(self.imagem_path, destino)

        vtc = pc * qc
        vtv = pv * qc  # Por enquanto, sem venda registrada

        conn = sqlite3.connect("stock_control.db")
        cursor = conn.cursor()

        cursor.execute('SELECT qtd_comprada FROM mercadorias WHERE id = ?', (id_p,))
        resultado = cursor.fetchone()

        if resultado:
            qc_atual = resultado[0]
            novo_qc = qc_atual + qc
            novo_vtc = pc * novo_qc
            cursor.execute('''
                UPDATE mercadorias 
                SET nome = ?, preco_compra = ?, preco_venda = ?, qtd_comprada = ?, descricao = ?, 
                    valor_total_compra = ?, imagem_path = ?
                WHERE id = ?
            ''', (nome, pc, pv, novo_qc, desc, novo_vtc, destino, id_p))
            QMessageBox.information(self, "Atualizado", f"Estoque de '{nome}' atualizado com {qc} unidades adicionais.")
        else:
            cursor.execute('''
                INSERT INTO mercadorias VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
            ''', (id_p, nome, pc, pv, qc, desc, vtc, vtv, destino))
            QMessageBox.information(self, "Cadastrado", f"Mercadoria '{nome}' cadastrada com sucesso.")

        conn.commit()
        conn.close()
        self.limpar_campos()
        self.listar_mercadorias()

    def limpar_campos(self):
        self.id_input.clear()
        self.nome_input.clear()
        self.preco_compra_input.clear()
        self.preco_venda_input.clear()
        self.qtd_comprada_input.clear()
        self.descricao_input.clear()
        self.imagem_label.setText("Nenhuma imagem selecionada")
        if hasattr(self, 'imagem_path'):
            del self.imagem_path

    def listar_mercadorias(self):
        self.lista_widget.clear()
        conn = sqlite3.connect("stock_control.db")
        cursor = conn.cursor()
        termo_busca = self.busca_input.text().lower()

        cursor.execute('SELECT * FROM mercadorias')
        for row in cursor.fetchall():
            id_p, nome, pc, pv, qc, qs, desc, vtc, vtv, img = row

            if termo_busca and termo_busca not in id_p.lower() and termo_busca not in nome.lower() and termo_busca not in desc.lower():
                continue

            item = QListWidgetItem()
            widget = QWidget()
            layout = QHBoxLayout()

            label_img = QLabel()
            pixmap = QPixmap(img).scaled(100, 100, Qt.AspectRatioMode.IgnoreAspectRatio)
            label_img.setPixmap(pixmap)

            right_layout = QVBoxLayout()
            info = QLabel(f"<b>ID:</b> {id_p}<br><b>{nome}</b><br>{desc[:30]}...<br>"
                           f"Comprada: {qc} | Vendida: {qs}<br>"
                           f"Restante: {qc - qs}<br>"
                           f"Lucro Estimado: R${(pv - pc) * qs:.2f}")

            right_layout.addWidget(info)

            qtd_saida_input = QLineEdit()
            qtd_saida_input.setPlaceholderText("Qtd Vendida")
            qtd_saida_input.setMaximumWidth(100)

            btn_vender = QPushButton("Registrar Venda")
            btn_vender.clicked.connect(lambda _, i=id_p, q=qtd_saida_input, c=pc, p=pv: self.registrar_venda(i, q, c, p))

            right_layout.addWidget(qtd_saida_input)
            right_layout.addWidget(btn_vender)

            layout.addWidget(label_img)
            layout.addLayout(right_layout)
            widget.setLayout(layout)
            item.setSizeHint(widget.sizeHint())

            item.setData(Qt.UserRole, row)
            self.lista_widget.addItem(item)
            self.lista_widget.setItemWidget(item, widget)
        conn.close()

    def registrar_venda(self, id_p, qtd_saida_input, preco_compra, preco_venda):
        try:
            nova_saida = int(qtd_saida_input.text())
            if nova_saida <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Erro", "Digite uma quantidade válida maior que zero.")
            return

        conn = sqlite3.connect("stock_control.db")
        cursor = conn.cursor()
        cursor.execute('SELECT qtd_comprada, qtd_saida FROM mercadorias WHERE id = ?', (id_p,))
        qc_atual, qs_atual = cursor.fetchone()
        conn.close()

        if qc_atual < qs_atual + nova_saida:
            QMessageBox.warning(self, "Erro", "Quantidade vendida excede estoque disponível.")
            return

        nova_qs = qs_atual + nova_saida
        valor_total_venda = preco_venda * nova_saida

        conn = sqlite3.connect("stock_control.db")
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE mercadorias
            SET qtd_saida = ?, valor_total_venda = ?
            WHERE id = ?
        ''', (nova_qs, valor_total_venda, id_p))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Sucesso", "Venda registrada com sucesso!")
        self.listar_mercadorias()

    def exibir_detalhes_produto(self, item):
        dados = item.data(Qt.UserRole)
        if dados:
            id_p, nome, pc, pv, qc, qs, desc, vtc, vtv, img = dados
            dialog = DetalhesProdutoDialog(id_p, nome, pc, pv, qc, qs, desc, vtc, vtv, img, self)
            dialog.exec_()
            self.listar_mercadorias()

    def realizar_backup(self):
        if not os.path.exists('backups'):
            os.makedirs('backups')
        timestamp = time.strftime("%Y%m%d_%H%M")
        shutil.copy('stock_control.db', f'backups/backup_{timestamp}.db')
        print(f"💾 Backup realizado: backup_{timestamp}.db")

    def exportar_relatorio_pdf(self):
        from reportlab.pdfgen import canvas
        pdf_path = "reports/relatorio_estoque.pdf"
        c = canvas.Canvas(pdf_path)
        c.drawString(50, 800, "Relatório de Estoque - Controle Stock")
        c.drawString(50, 780, "Data: " + datetime.now().strftime("%d/%m/%Y %H:%M"))
        c.line(50, 770, 550, 770)
        y = 750
        conn = sqlite3.connect("stock_control.db")
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM mercadorias')
        for row in cursor.fetchall():
            id_p, nome, pc, pv, qc, qs, desc, vtc, vtv, img = row
            texto = f"{nome} - ID: {id_p} - Comprada: {qc}, Vendida: {qs}, Lucro: R${(pv - pc) * qs:.2f}"
            c.drawString(50, y, texto)
            y -= 20
        conn.close()
        c.save()
        QMessageBox.information(self, "PDF Exportado", "Relatório salvo como PDF")
        print("📄 Relatório exportado como PDF")

    def gerar_grafico_lucro(self):
        conn = sqlite3.connect("stock_control.db")
        cursor = conn.cursor()
        cursor.execute('SELECT nome, (preco_venda - preco_compra) * qtd_saida AS lucro FROM mercadorias')
        dados = cursor.fetchall()
        conn.close()

        nomes = [row[0] for row in dados]
        lucros = [row[1] for row in dados]

        plt.figure(figsize=(10, 5))
        plt.bar(nomes, lucros, color='skyblue')
        plt.title("Lucro por Produto")
        plt.xlabel("Produtos")
        plt.ylabel("Lucro (R$)")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig("reports/grafico_lucro.png")
        plt.close()
        QMessageBox.information(self, "Gráfico", "Gráfico de lucro salvo.")


# === EXECUÇÃO PRINCIPAL ===
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Definindo o ícone da janela para "janela.ico"
    app.setWindowIcon(QIcon("imagens/janela.ico"))

    db_manager = DatabaseManager()

    conn = sqlite3.connect(db_manager.db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users LIMIT 1")
    has_user = cursor.fetchone()
    conn.close()

    if not has_user:
        create_dialog = CreateUserDialog(db_manager)
        if create_dialog.exec() != QDialog.Accepted:
            sys.exit()

    login_dialog = LoginDialog(db_manager)
    if login_dialog.exec() != QDialog.Accepted:
        sys.exit()

    window = CadastroMercadoriasApp()
    window.show()
    sys.exit(app.exec())
