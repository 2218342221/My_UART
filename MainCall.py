import re
import sys
import binascii
from PyQt5.QtWidgets import QMainWindow, QApplication, QFontDialog, QMessageBox
from PyQt5.QtGui import QFont
from PyQt5 import QtGui
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from MyUartMainWindow import Ui_MyUART


class MyWin(QMainWindow, Ui_MyUART):
    def __init__(self, ):
        super().__init__()
        self.setupUi(self)
        self.addMyToolTip()
        self.CreateItems()
        self.addSlot()

    def addMyToolTip(self):
        self.pushButton_clear.setToolTip("clear")
        self.pushButton_readOrWrite.setToolTip("reading")
        self.pushButton_send.setToolTip("send")
        self.pushButton_startOrStop.setToolTip("stoped")
        self.checkBox_16.setToolTip("hex send")
        self.comboBox_baud.setToolTip("baud rate")
        self.comboBox_Com.setToolTip("select com")
        self.page_write.setStatusTip("write mode")
        self.page_read.setStatusTip("read mode")
        self.pushButton_search.setToolTip("search com")

        self.pushButton_readOrWrite.setProperty("status", "read")
        self.pushButton_readOrWrite.setProperty("readHex", False)
        self.pushButton_readOrWrite.setProperty("writeHex", False)
        self.pushButton_startOrStop.setProperty("status", "stop")
        self.comboBox_baud.setCurrentText("115200")

    def CreateItems(self):
        # Qt 串口类
        self.com = QSerialPort()

    def addSlot(self):
        # 读写转换按钮
        self.pushButton_readOrWrite.clicked.connect(self.setWindowReadOrWrite)
        # 字体
        self.actionPreferences.triggered.connect(self.setTextWindowFont)
        # 开关按钮
        self.pushButton_startOrStop.clicked.connect(self.startOrStop)
        # 发送按钮
        self.pushButton_send.clicked.connect(self.sendData)
        # 16进制按钮
        self.checkBox_16.stateChanged.connect(self.hexSendingOrWriting)
        # 搜索按钮
        self.pushButton_search.clicked.connect(self.searchComPort)
        # 清除按钮
        self.pushButton_clear.clicked.connect(self.clearData)
        # com选择
        # 波特率选择

        self.com.readyRead.connect(self.comReceiveData)  # 接收数据



    def setTextWindowFont(self):
        font, ok = QFontDialog.getFont()
        if ok:
            self.textEdit_write.setFont(font)
            self.textEdit_read.setFont(font)

    def setWindowReadOrWrite(self):
        if self.pushButton_readOrWrite.property("status") == "read":
            self.stackedWidget.setCurrentWidget(self.page_write)
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/Tool Button/resources/write.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.pushButton_readOrWrite.setIcon(icon)
            self.pushButton_readOrWrite.setToolTip("writing")
            self.pushButton_readOrWrite.setProperty("status", "write")
            if self.pushButton_readOrWrite.property("writeHex"):
                self.checkBox_16.setChecked(True)
            else:
                self.checkBox_16.setChecked(False)

        elif self.pushButton_readOrWrite.property("status") == "write":
            self.stackedWidget.setCurrentWidget(self.page_read)
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/Tool Button/resources/read.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.pushButton_readOrWrite.setIcon(icon)
            self.pushButton_readOrWrite.setToolTip("reading")
            self.pushButton_readOrWrite.setProperty("status", "read")

            if self.pushButton_readOrWrite.property("readHex"):
                self.checkBox_16.setChecked(True)
            else:
                self.checkBox_16.setChecked(False)

    def startOrStop(self):
        if self.pushButton_startOrStop.property("status") == "stop":
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/Tool Button/resources/start.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.pushButton_startOrStop.setIcon(icon)
            self.pushButton_startOrStop.setProperty("status", "start")

            comName = self.comboBox_Com.currentText()
            comBaud = int(self.comboBox_baud.currentText())
            self.com.setPortName(comName)
            self.com.setBaudRate(comBaud)
            try:
                if not self.com.open(QSerialPort.ReadWrite):
                    QMessageBox.critical(self, '严重错误', '串口打开失败')
                    return
            except:
                QMessageBox.critical(self, '严重错误', '串口打开失败')
                return
            self.pushButton_search.setEnabled(False)
            self.comboBox_Com.setEnabled(False)
            self.comboBox_baud.setEnabled(False)


        elif self.pushButton_startOrStop.property("status") == "start":
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/Tool Button/resources/stop.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.pushButton_startOrStop.setIcon(icon)
            self.pushButton_startOrStop.setProperty("status", "stop")

            self.com.close()
            self.pushButton_search.setEnabled(True)
            self.comboBox_Com.setEnabled(True)
            self.comboBox_baud.setEnabled(True)

    def searchComPort(self):
        self.comboBox_Com.clear()
        com = QSerialPort()
        comList = QSerialPortInfo.availablePorts()
        for comInfo in comList:
            com.setPort(comInfo)
            if com.open(QSerialPort.ReadWrite):
                self.comboBox_Com.addItem(comInfo.portName())
                com.close()

    def hexSendingOrWriting(self):
        if self.pushButton_readOrWrite.property("status") == "read":
            self.pushButton_readOrWrite.setProperty("readHex", self.checkBox_16.isChecked())
            # 接收区换行
            self.textEdit_read.insertPlainText("\n")
        else:
            self.pushButton_readOrWrite.setProperty("writeHex", self.checkBox_16.isChecked())

    def sendData(self):
        self.comSendData()

    def clearData(self):
        if self.pushButton_readOrWrite.property("status") == "read":
            self.textEdit_read.clear()
            self.lcdNumber_readNum.display(0)
        else:
            self.textEdit_write.clear()
            self.lcdNumber_writeNum.display(0)

    # 串口发送数据
    def comSendData(self):
        txData = self.textEdit_write.toPlainText()
        if len(txData) == 0:
            return
        if not self.pushButton_readOrWrite.property("writeHex"):
            self.com.write(txData.encode('UTF-8'))
            self.lcdNumber_writeNum.display(self.lcdNumber_writeNum.value() + len(bytes(txData.encode('UTF-8'))))
        else:
            Data = txData.replace(' ', '')
            Data = Data.replace('0x', '')
            # 如果16进制不是偶数个字符, 去掉最后一个, [ ]左闭右开
            if len(Data) % 2 == 1:
                Data = Data[0:len(Data) - 1]
            # 如果遇到非16进制字
            if Data.isalnum() is False:
                QMessageBox.critical(self, '错误', '包含非十六进制数')
            try:
                hexData = binascii.a2b_hex(Data)
            except:
                QMessageBox.critical(self, '错误', '转换编码错误')
                return
            # 发送16进制数据, 发送格式如 ‘31 32 33 41 42 43’, 代表'123ABC'
            try:
                self.com.write(hexData)
                self.lcdNumber_writeNum.display(self.lcdNumber_writeNum.value() + len(hexData))
            except:
                QMessageBox.critical(self, '异常', '十六进制发送错误')
                return

    # 串口接收数据
    def comReceiveData(self):
        try:
            rxData = bytes(self.com.readAll())
        except:
            QMessageBox.critical(self, '严重错误', '串口接收数据错误')
        if not self.pushButton_readOrWrite.property("readHex"):
            try:
                self.textEdit_read.insertPlainText(rxData.decode('UTF-8'))
                self.lcdNumber_readNum.display(self.lcdNumber_readNum.value()+len(rxData))
            except:
                pass
        else:
            Data = binascii.b2a_hex(rxData).decode('ascii')
            # re 正则表达式 (.{2}) 匹配两个字母
            hexStr = ' 0x'.join(re.findall('(.{2})', Data))
            # 补齐第一个 0x
            hexStr = '0x' + hexStr
            self.textEdit_read.insertPlainText(hexStr)
            self.textEdit_read.insertPlainText(' ')
            self.lcdNumber_readNum.display(self.lcdNumber_readNum.value() + len(rxData))


if __name__ == '__main__':

    import sys
    import qdarkgraystyle

    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkgraystyle.load_stylesheet())
    mywin = MyWin()
    mywin.show()
    sys.exit(app.exec_())