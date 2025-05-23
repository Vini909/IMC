from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_TelaFinanceiro(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.label_nome = QtWidgets.QLabel(self.centralwidget)
        self.label_nome.setGeometry(QtCore.QRect(30, 20, 400, 30))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.label_nome.setFont(font)
        self.label_nome.setStyleSheet("color: navy;")
        self.label_nome.setText("Cliente: [NOME]")

        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget.setGeometry(QtCore.QRect(30, 70, 740, 300))
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setHorizontalHeaderLabels(["Data", "Valor (R$)"])
        self.tableWidget.setObjectName("tableWidget")

        self.btn_registrar = QtWidgets.QPushButton(self.centralwidget)
        self.btn_registrar.setGeometry(QtCore.QRect(30, 400, 200, 40))
        self.btn_registrar.setText("Registrar Pagamento")

        self.btn_listar = QtWidgets.QPushButton(self.centralwidget)
        self.btn_listar.setGeometry(QtCore.QRect(290, 400, 200, 40))
        self.btn_listar.setText("Listar Pendências")

        self.btn_quitar = QtWidgets.QPushButton(self.centralwidget)
        self.btn_quitar.setGeometry(QtCore.QRect(550, 400, 200, 40))
        self.btn_quitar.setText("Quitar Pagamento")

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Financeiro - Nutricionista"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_TelaFinanceiro()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())