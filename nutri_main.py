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

def sugerir_dieta(peso, alergias):
    alimentos = {
        "leve": ["Salada de folhas", "Frutas", "Peito de frango", "Peixe grelhado", "Legumes cozidos"],
        "proteina": ["Ovos", "Iogurte grego", "Queijo cottage", "Carne magra", "Tofu"],
        "sem_lactose": ["Leite de amêndoas", "Queijo vegano", "Iogurte de coco"],
        "sem_gluten": ["Arroz integral", "Quinoa", "Batata doce", "Milho"],
        "geral": ["Aveia", "Nozes", "Sementes", "Smoothies", "Sopas"]
    }

    if peso > 90:
        sugestoes = alimentos["leve"] + alimentos["proteina"]
    else:
        sugestoes = alimentos["geral"]

    if "lactose" in alergias:
        sugestoes = [a for a in sugestoes if a not in alimentos["sem_lactose"]]

    if "gluten" in alergias:
        sugestoes = [a for a in sugestoes if a not in alimentos["sem_gluten"]]

    plano = []
    for i in range(6):
        linha = []
        for j in range(7):
            item = sugestoes[(i * 7 + j) % len(sugestoes)]
            linha.append(item)
        plano.append(linha)
    return plano

def preencher_tabela(tableWidget, plano_alimentar):
    for i in range(6):
        for j in range(7):
            item = QTableWidgetItem(plano_alimentar[i][j])
            tableWidget.setItem(i, j, item)

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

    def salvar_consulta(self):
        nome_cliente = self.ui_terceira.label_5.text()
        paciente_id = self.buscar_id_paciente(nome_cliente)
        descricao = self.ui_terceira.plainTextEdit.toPlainText()
        dieta = self.ui_terceira.plainTextEdit_2.toPlainText()
        orientacoes = self.ui_terceira.plainTextEdit_3.toPlainText()

        if not paciente_id:
            QMessageBox.warning(self, "Erro", "Paciente não encontrado.")
            return

        try:
            query = """
            INSERT INTO consultas (paciente_id, data, descricao, dieta_prescrita, orientacoes)
            VALUES (%s, CURDATE(), %s, %s, %s)
            """
            self.cursor.execute(query, (paciente_id, descricao, dieta, orientacoes))
            self.db_connection.commit()
            QMessageBox.information(self, "Sucesso", "Consulta registrada com sucesso!")
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar consulta: {err}")

    def carregar_plano_alimentar(self, nome_cliente):
        paciente_id = self.buscar_id_paciente(nome_cliente)
        if not paciente_id:
            QMessageBox.warning(self, "Erro", "Paciente não encontrado.")
            return

        try:
            self.cursor.execute("SELECT dia, cafe, almoco, tarde, noite, lache, extra FROM plano WHERE paciente_id = %s", (paciente_id,))
            resultados = self.cursor.fetchall()

            tabela = self.ui_terceira.tableWidget
            tabela.clearContents()

            for linha in resultados:
                dia = linha[0] - 1  # dias são de 1 a 7, colunas de 0 a 6
                for i in range(6):  # 6 refeições
                    item = QtWidgets.QTableWidgetItem(linha[i + 1])
                    tabela.setItem(i, dia, item)

        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar plano alimentar: {err}")

    def gerar_grafico_evolucao_peso(self, paciente_id):
        try:
            self.cursor.execute("SELECT data_registro, peso FROM dieta_evo WHERE paciente_id = %s ORDER BY data_registro", (paciente_id,))
            resultados = self.cursor.fetchall()

            if not resultados:
                QMessageBox.information(self, "Aviso", "Nenhum dado de evolução de peso encontrado.")
                return

            datas = [r[0].strftime("%d/%m") for r in resultados]
            pesos = [float(r[1]) for r in resultados]

            import matplotlib.pyplot as plt

            plt.figure(figsize=(10, 6))
            plt.plot(datas, pesos, marker='o', linestyle='-', color='green')
            plt.xlabel("Data")
            plt.ylabel("Peso (kg)")
            plt.title("Evolução do Peso do Paciente")
            plt.grid(True)
            plt.tight_layout()
            plt.show()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar gráfico de evolução: {e}")

    def salvar_agendamento(self, nome_cliente):
        data = self.ui_agendamento.calendarWidget.selectedDate().toString("yyyy-MM-dd")
        hora = self.ui_agendamento.timeEdit.time().toString("HH:mm:ss")
        item = self.ui_agendamento.lineEdit.text()

        if not data or not hora:
            QMessageBox.warning(self, "Aviso", "Selecione uma data e horário.")
            return

        try:
            query = """
            INSERT INTO agendamento (dia, hora, item, nome_cliente)
            VALUES (%s, %s, %s, %s)
            """
            self.cursor.execute(query, (data, hora, item, nome_cliente))
            self.db_connection.commit()
            QMessageBox.information(self, "Sucesso", "Agendamento salvo com sucesso!")
            self.carregar_historico_agendamentos(nome_cliente)
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar agendamento: {err}")

    def carregar_historico_agendamentos(self, nome_cliente):
        try:
            self.cursor.execute(
                "SELECT dia, hora FROM agendamento WHERE nome_cliente = %s ORDER BY dia DESC",
                (nome_cliente,)
            )
            resultados = self.cursor.fetchall()
            tabela = self.ui_agendamento.tableWidget
            tabela.setRowCount(len(resultados))
            tabela.setColumnCount(2)
            tabela.setHorizontalHeaderLabels(["Data", "Horário"])
            for i, (dia, hora) in enumerate(resultados):
                tabela.setItem(i, 0, QtWidgets.QTableWidgetItem(str(dia)))
                tabela.setItem(i, 1, QtWidgets.QTableWidgetItem(str(hora)))
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar histórico: {err}")
        




    def salvar_dados(self):
        nome = self.lineEdit.text()
        idade = self.lineEdit_2.text()
        peso = self.lineEdit_5.text()
        altura = self.lineEdit_4.text()
        alergias = self.lineEdit_7.text()
        imc = self.lineEdit_6.text()
        sexo = "Masculino" if self.radioButton.isChecked() else "Feminino" if self.radioButton_2.isChecked() else None
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
                self.abrir_agendamento(nome_cliente)
            else:
                QMessageBox.information(self, "Cliente não encontrado", "Nenhum cliente com esses dados foi encontrado.")
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", f"Erro ao buscar cliente: {err}")

    def abrir_agendamento(self, nome_cliente):
        self.fechar_todas_janelas()
        self.tela_agendamento = QtWidgets.QMainWindow()
        self.ui_agendamento = Ui_SegundaTela()
        self.ui_agendamento.setupUi(self.tela_agendamento)
        self.ui_agendamento.label_5.setText(f"Paciente:{nome_cliente}")
        self.ui_agendamento.pushButton.clicked.connect(lambda: self.salvar_agendamento(nome_cliente))
        self.ui_agendamento.pushButton_4.clicked.connect(lambda: self.abrir_consulta(nome_cliente))
        self.ui_agendamento.pushButton_6.clicked.connect(lambda: self.abrir_financeiro(nome_cliente))
        self.carregar_agendamento(nome_cliente)
        self.tela_agendamento.show()

    def abrir_consulta(self, nome_cliente):
        self.fechar_todas_janelas()
        self.tela_consulta = QtWidgets.QMainWindow()
        self.ui_terceira = Ui_TerceiraTela()
        self.ui_terceira.setupUi(self.tela_consulta)
        self.ui_terceira.label_5.setText(nome_cliente)
        self.ui_terceira.pushButton.clicked.connect(self.salvar_plano_alimentar)
        self.ui_terceira.pushButton_2.clicked.connect(self.salvar_consulta)
        self.ui_terceira.pushButton_3.clicked.connect(lambda: self.gerar_grafico_evolucao_peso(self.buscar_id_paciente(nome_cliente)))
        self.ui_terceira.pushButton_4.clicked.connect(self.gerar_grafico_comparativo_pesos)
        self.ui_terceira.pushButton_5.clicked.connect(self.gerar_sugestao_dieta)
        self.ui_terceira.pushButton_8.clicked.connect(lambda: self.abrir_agendamento(nome_cliente))
        self.ui_terceira.pushButton_10.clicked.connect(lambda: self.abrir_financeiro(nome_cliente))
        self.carregar_plano_alimentar(nome_cliente)
        self.tela_consulta.show()
    
    def abrir_financeiro(self, nome_cliente):
        self.fechar_todas_janelas()
        self.tela_financeiro = QtWidgets.QMainWindow()
        self.ui_financeiro = Ui_TelaFinanceiro()
        self.ui_financeiro.setupUi(self.tela_financeiro)
        self.ui_financeiro.label_nome.setText(f"Cliente: {nome_cliente}")
        self.tela_financeiro.show()


    def salvar_plano_alimentar(self):
        nome_cliente = self.ui_terceira.label_5.text()
        paciente_id = self.buscar_id_paciente(nome_cliente)
    

        if not paciente_id:
            QMessageBox.warning(self, "Erro", "Paciente não encontrado.")
            return

        tabela = self.ui_terceira.tableWidget
        try:
            self.cursor.execute("DELETE FROM plano WHERE paciente_id = %s", (paciente_id,))
            for coluna in range(tabela.columnCount()):
                dados = [tabela.item(linha, coluna).text() if tabela.item(linha, coluna) else None for linha in range(6)]
                query = """
                INSERT INTO plano (paciente_id, dia, cafe, almoco, tarde, noite, lache, extra)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                self.cursor.execute(query, (paciente_id, coluna + 1, *dados))
            self.db_connection.commit()
            QMessageBox.information(self, "Sucesso", "Plano alimentar salvo com sucesso!")
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar plano: {err}")


    def gerar_sugestao_dieta(self):
        nome_cliente = self.ui_terceira.label_5.text()
        paciente_id = self.buscar_id_paciente(nome_cliente)
        if not paciente_id:
            QMessageBox.warning(self, "Erro", "Paciente não encontrado.")
            return
        try:
            self.cursor.execute("SELECT peso, alergias FROM cadastro_clientes WHERE id = %s", (paciente_id,))
            resultado = self.cursor.fetchone()
            if resultado:
                peso, alergias = resultado
                alergias = alergias.lower().replace(" ", "").split(",")
                plano = sugerir_dieta(float(peso), alergias)
                preencher_tabela(self.ui_terceira.tableWidget, plano)
                QMessageBox.information(self, "Sucesso", "Plano alimentar sugerido com sucesso!")
            else:
                QMessageBox.warning(self, "Erro", "Dados do paciente não encontrados.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar sugestão: {e}")

    def buscar_id_paciente(self, nome_cliente):
        self.cursor.execute("SELECT id FROM cadastro_clientes WHERE nome = %s", (nome_cliente,))
        resultado = self.cursor.fetchone()
        return resultado[0] if resultado else None

    def carregar_agendamento(self, nome_cliente):
        try:
            self.cursor.execute(
                "SELECT dia, hora FROM agendamento WHERE nome_cliente = %s ORDER BY dia DESC",
                (nome_cliente,)
            )
            resultados = self.cursor.fetchall()
            tabela = self.ui_agendamento.tableWidget
            tabela.setRowCount(len(resultados))
            tabela.setColumnCount(2)
            tabela.setHorizontalHeaderLabels(["Data", "Horário"])
            for i, (dia, hora) in enumerate(resultados):
                tabela.setItem(i, 0, QTableWidgetItem(str(dia)))
                tabela.setItem(i, 1, QTableWidgetItem(str(hora)))
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar histórico: {err}")

    def fechar_todas_janelas(self):
        for janela in ['tela_agendamento', 'tela_consulta', 'tela_financeiro']:
            if hasattr(self, janela):
                getattr(self, janela).close()
    
    def gerar_grafico_comparativo_pesos(self):
        try:
            self.cursor.execute("SELECT nome, peso FROM cadastro_clientes")
            resultados = self.cursor.fetchall()

            if not resultados:
                QMessageBox.information(self, "Aviso", "Nenhum dado de paciente encontrado.")
                return

            nomes = [r[0] for r in resultados]
            pesos = [float(r[1]) for r in resultados]

            import matplotlib.pyplot as plt

            plt.figure(figsize=(10, 6))
            plt.bar(nomes, pesos, color='skyblue')
            plt.xlabel("Pacientes")
            plt.ylabel("Peso (kg)")
            plt.title("Comparativo de Pesos dos Pacientes")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar gráfico: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = Main()
    janela.show()
    sys.exit(app.exec_())
