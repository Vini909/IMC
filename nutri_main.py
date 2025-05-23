import sys
import mysql.connector
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem
from PyQt5 import QtWidgets, uic
from Inicial_imc import Ui_MainWindow
from segunda_tela import Ui_MainWindow as Ui_SegundaTela
from terceira_tela import Ui_MainWindow as Ui_TerceiraTela
from quarta_tela import Ui_TelaFinanceiro
import matplotlib.pyplot as plt
from fpdf import FPDF

class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        uic.loadUi("Inicial_imc.ui", self)

        self.pushButton.clicked.connect(self.salvar_dados)
        self.pushButton_2.clicked.connect(self.filtrar_cliente)

        self.db_connection = mysql.connector.connect(
            host="localhost",
            database="nutri",
            user="root",
            password=""
        )
        self.cursor = self.db_connection.cursor()

    def salvar_dados(self):
        nome = self.lineEdit.text()
        idade = self.lineEdit_2.text()
        peso = self.lineEdit_5.text()
        altura = self.lineEdit_4.text()
        alergias = self.lineEdit_7.text()
        imc = self.lineEdit_6.text()

        if self.radioButton.isChecked():
            sexo = "Masculino"
        elif self.radioButton_2.isChecked():
            sexo = "Feminino"
        else:
            sexo = None

        historico_med = self.textEdit.toPlainText()

        if nome and peso and idade and altura and alergias and imc and historico_med and sexo:
            try:
                query = '''
                INSERT INTO cadastro_clientes 
                (nome, peso, idade, altura, alergias, imc, Historico_med, sexo) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                '''
                values = (nome, peso, idade, altura, alergias, imc, historico_med, sexo)
                self.cursor.execute(query, values)
                self.db_connection.commit()
                QMessageBox.information(self, "Sucesso", "Dados salvos com sucesso!")
            except mysql.connector.Error as err:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar dados: {err}")
        else:
            QMessageBox.warning(self, "Aviso", "Por favor, preencha todos os campos!")

    def filtrar_cliente(self):
        idade = self.lineEdit_3.text()
        peso = self.lineEdit_8.text()
        imc = self.lineEdit_9.text()

        if not idade or not peso or not imc:
            QMessageBox.warning(self, "Aviso", "Preencha todos os campos de login.")
            return

        try:
            query = "SELECT * FROM cadastro_clientes WHERE idade = %s AND peso = %s AND imc = %s"
            self.cursor.execute(query, (idade, peso, imc))
            resultado = self.cursor.fetchone()

            if resultado:
                nome_cliente = resultado[1]

                self.tela_agendamento = QtWidgets.QMainWindow()
                self.ui_agendamento = Ui_SegundaTela()
                self.ui_agendamento.setupUi(self.tela_agendamento)
                self.ui_agendamento.label_5.setText(f"Paciente:{nome_cliente}")
                self.ui_agendamento.pushButton.clicked.connect(lambda: self.salvar_agendamento(nome_cliente))
                self.carregar_historico_agendamentos(nome_cliente)
                self.tela_agendamento.show()

                self.tela_consulta = QtWidgets.QMainWindow()
                self.ui_terceira = Ui_TerceiraTela()
                self.ui_terceira.setupUi(self.tela_consulta)
                self.ui_terceira.label_5.setText(nome_cliente)
                self.ui_terceira.pushButton_2.clicked.connect(self.salvar_consulta)
                self.ui_terceira.pushButton_3.clicked.connect(lambda: self.gerar_grafico_evolucao_peso(resultado[0]))
                self.ui_terceira.pushButton_4.clicked.connect(self.gerar_grafico_comparativo_pesos)
                self.tela_consulta.show()

                self.tela_financeiro = QtWidgets.QMainWindow()
                self.ui_financeiro = Ui_TelaFinanceiro()
                self.ui_financeiro.setupUi(self.tela_financeiro)
                self.ui_financeiro.label_nome.setText(f"Cliente: {nome_cliente}")
                self.ui_financeiro.btn_registrar.clicked.connect(lambda: self.registrar_pagamento(nome_cliente, 150.00))
                self.ui_financeiro.btn_listar.clicked.connect(lambda: self.listar_pendencias(nome_cliente))
                self.ui_financeiro.btn_quitar.clicked.connect(lambda: self.quitar_pagamento(nome_cliente))
                self.tela_financeiro.show()
            else:
                QMessageBox.information(self, "Cliente não encontrado", "Nenhum cliente com esses dados foi encontrado.")
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", f"Erro ao buscar cliente: {err}")

    def carregar_historico_agendamentos(self, nome_cliente):
        try:
            query = "SELECT dia, item FROM agenda_hist WHERE nome_cliente = %s"
            self.cursor.execute(query, (nome_cliente,))
            agendamentos = self.cursor.fetchall()
            self.ui_agendamento.tableWidget.clearContents()
            self.ui_agendamento.tableWidget.setRowCount(31)
            self.ui_agendamento.tableWidget.setColumnCount(12)
            meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
            self.ui_agendamento.tableWidget.setHorizontalHeaderLabels(meses)
            dias = [str(i + 1) for i in range(31)]
            self.ui_agendamento.tableWidget.setVerticalHeaderLabels(dias)
            for dia, item in agendamentos:
                mes_idx = dia.month - 1
                dia_idx = dia.day - 1
                self.ui_agendamento.tableWidget.setItem(dia_idx, mes_idx, QTableWidgetItem(item))
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar histórico: {err}")

    def salvar_consulta(self):
        nome_cliente = self.ui_terceira.label_5.text()
        descricao = self.ui_terceira.plainTextEdit.toPlainText()
        dieta = self.ui_terceira.plainTextEdit_2.toPlainText()
        orientacoes = self.ui_terceira.plainTextEdit_4.toPlainText()

        if not (nome_cliente and descricao and dieta and orientacoes):
            QMessageBox.warning(self, "Aviso", "Preencha todos os campos da consulta.")
            return

        try:
            self.cursor.execute("SELECT id FROM cadastro_clientes WHERE nome = %s", (nome_cliente,))
            resultado = self.cursor.fetchone()
            if not resultado:
                QMessageBox.warning(self, "Erro", "Paciente não encontrado.")
                return

            paciente_id = resultado[0]

            query = """
            INSERT INTO consultas (paciente_id, data, descricao, dieta_prescrita, orientacoes)
            VALUES (%s, CURDATE(), %s, %s, %s)
            """
            self.cursor.execute(query, (paciente_id, descricao, dieta, orientacoes))
            self.db_connection.commit()
            QMessageBox.information(self, "Sucesso", "Consulta registrada com sucesso!")

            self.ui_terceira.plainTextEdit.clear()
            self.ui_terceira.plainTextEdit_2.clear()
            self.ui_terceira.plainTextEdit_4.clear()

        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar consulta: {err}")

    def registrar_pagamento(self, nome_cliente, valor):
        try:
            self.cursor.execute("SELECT id FROM cadastro_clientes WHERE nome = %s", (nome_cliente,))
            resultado = self.cursor.fetchone()
            if not resultado:
                QMessageBox.warning(self, "Erro", "Paciente não encontrado.")
                return
            paciente_id = resultado[0]
            self.cursor.execute("INSERT INTO financeiro (paciente_id, valor, pago) VALUES (%s, %s, %s)", (paciente_id, valor, False))
            self.db_connection.commit()
            QMessageBox.information(self, "Sucesso", "Pagamento registrado.")
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", str(err))

    def listar_pendencias(self, nome_cliente):
        try:
            self.cursor.execute("SELECT id FROM cadastro_clientes WHERE nome = %s", (nome_cliente,))
            resultado = self.cursor.fetchone()
            if not resultado:
                QMessageBox.warning(self, "Erro", "Paciente não encontrado.")
                return
            paciente_id = resultado[0]
            self.cursor.execute("SELECT data, valor FROM financeiro WHERE paciente_id = %s AND pago = FALSE", (paciente_id,))
            pendencias = self.cursor.fetchall()
            self.ui_financeiro.tableWidget.setRowCount(0)
            for row_num, (data, valor) in enumerate(pendencias):
                self.ui_financeiro.tableWidget.insertRow(row_num)
                self.ui_financeiro.tableWidget.setItem(row_num, 0, QTableWidgetItem(str(data)))
                self.ui_financeiro.tableWidget.setItem(row_num, 1, QTableWidgetItem(f"R$ {valor:.2f}"))
            if not pendencias:
                QMessageBox.information(self, "Info", "Nenhuma pendência.")
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", str(err))

    def quitar_pagamento(self, nome_cliente):
        try:
            self.cursor.execute("SELECT id FROM cadastro_clientes WHERE nome = %s", (nome_cliente,))
            resultado = self.cursor.fetchone()
            if not resultado:
                QMessageBox.warning(self, "Erro", "Paciente não encontrado.")
                return
            paciente_id = resultado[0]
            self.cursor.execute("UPDATE financeiro SET pago = TRUE WHERE paciente_id = %s AND pago = FALSE", (paciente_id,))
            self.db_connection.commit()
            QMessageBox.information(self, "Sucesso", "Pagamentos quitados!")
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", str(err))

    def gerar_grafico_evolucao_peso(self, paciente_id):
        try:
            query = "SELECT data_registro, Peso FROM dieta_evo WHERE paciente_id = %s ORDER BY data_registro"
            self.cursor.execute(query, (paciente_id,))
            resultados = self.cursor.fetchall()

            datas = [resultado[0] for resultado in resultados]
            pesos = [float(resultado[1]) for resultado in resultados]

            plt.figure(figsize=(10, 5))
            plt.plot(datas, pesos, marker='o')
            plt.title('Evolução de Peso do Paciente')
            plt.xlabel('Data')
            plt.ylabel('Peso (kg)')
            plt.grid(True)
            plt.savefig('grafico_evolucao_peso.pdf')

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Evolução de Peso do Paciente", ln=True, align='C')
            pdf.image('grafico_evolucao_peso.pdf', x=10, y=20, w=180)
            pdf.output("grafico_evolucao_peso.pdf")

            QMessageBox.information(self, "Sucesso", "Gráfico de evolução de peso gerado e salvo como PDF.")
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar gráfico: {err}")

    def gerar_grafico_comparativo_pesos(self):
        try:
            query = "SELECT nome, peso FROM cadastro_clientes"
            self.cursor.execute(query)
            resultados = self.cursor.fetchall()

            nomes = [resultado[0] for resultado in resultados]
            pesos = [float(resultado[1]) for resultado in resultados]

            plt.figure(figsize=(10, 5))
            plt.bar(nomes, pesos)
            plt.title('Comparativo de Pesos dos Pacientes')
            plt.xlabel('Nome do Paciente')
            plt.ylabel('Peso (kg)')
            plt.grid(True)
            plt.savefig('grafico_comparativo_pesos.pdf')

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Comparativo de Pesos dos Pacientes", ln=True, align='C')
            pdf.image('grafico_comparativo_pesos.pdf', x=10, y=20, w=180)
            pdf.output("grafico_comparativo_pesos.pdf")

            QMessageBox.information(self, "Sucesso", "Gráfico comparativo de pesos gerado e salvo como PDF.")
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar gráfico: {err}")

    def closeEvent(self, event):
        self.cursor.close()
        self.db_connection.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = Main()
    janela.show()
    sys.exit(app.exec_())