
import sys
import mysql.connector
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem
from PyQt5 import QtWidgets, uic
from Inicial_imc import Ui_MainWindow
from segunda_tela import Ui_MainWindow as Ui_SegundaTela
from terceira_tela import Ui_MainWindow as Ui_TerceiraTela

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
        peso = self.lineEdit_4.text()
        altura = self.lineEdit_5.text()
        alergias = self.lineEdit_6.text()
        imc = self.lineEdit_7.text()

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


                self.ui_agendamento.label_5.setText(nome_cliente)


                self.ui_agendamento.pushButton.clicked.connect(lambda: self.salvar_agendamento(nome_cliente))
                self.carregar_historico_agendamentos(nome_cliente)

                self.tela_agendamento.show()
            else:
                QMessageBox.information(self, "Cliente não encontrado", "Nenhum cliente com esses dados foi encontrado.")
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", f"Erro ao buscar cliente: {err}")

    def salvar_agendamento(self, nome_cliente):
        data = self.ui_agendamento.calendarWidget.selectedDate().toString("yyyy-MM-dd")
        hora = self.ui_agendamento.timeEdit.time().toString("HH:mm:ss")
        item = self.ui_agendamento.lineEdit.text()

        if not item:
            QMessageBox.warning(self, "Aviso", "Insira uma descrição (item) do agendamento.")
            return

        try:
            self.cursor.execute("SELECT id FROM agenda_hist WHERE dia = %s AND hora = %s AND nome_cliente = %s",
                                (data, hora, nome_cliente))
            resultado = self.cursor.fetchone()

            if resultado:
                query = "UPDATE agenda_hist SET item = %s WHERE id = %s"
                self.cursor.execute(query, (item, resultado[0]))
            else:
                query = "INSERT INTO agenda_hist (dia, hora, item, nome_cliente) VALUES (%s, %s, %s, %s)"
                self.cursor.execute(query, (data, hora, item, nome_cliente))

            self.db_connection.commit()
            QMessageBox.information(self, "Sucesso", "Agendamento salvo/modificado com sucesso!")
            self.ui_agendamento.lineEdit.clear()
            self.carregar_historico_agendamentos(nome_cliente)
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar agendamento: {err}")

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

    def closeEvent(self, event):
        self.cursor.close()
        self.db_connection.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = Main()
    janela.show()
    sys.exit(app.exec_())
