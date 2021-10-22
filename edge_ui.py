#!/usr/bin/env python
# coding: utf-8

import sys, os
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QTextEdit, QPushButton, QLineEdit
from PyQt5.QtWidgets import QTableView
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtWidgets import QGridLayout, QVBoxLayout
from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QPen
from PyQt5 import QtCore
from PyQt5.QtCore import QAbstractTableModel
from PyQt5.QtCore import QThread, QPoint
#from PyQt5 import QtGui
import urllib
import requests
import pandas as pd
import clipboard
import edge_util
import json

__author__ = "T.H.Park <holyanna70@gmail.com>"

Qt = QtCore.Qt

class PandasModel(QAbstractTableModel):
    def __init__(self, data, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def data(self, index, role=Qt.DisplayRole):          
        if index.isValid():
            if role == Qt.DisplayRole:
                return QtCore.QVariant(str(
                    self._data.iloc[index.row()][index.column()]))
        return QtCore.QVariant()
    
    def getData(self, row, col):
        return self._data.iloc[row][col]

    def setData(self, index, value, role=Qt.EditRole):
        print(index)
        if index.isValid():
            row = index.row()
            col = index.column()
            self._data.iloc[row][col] = value
            self.dataChanged.emit(index, index, (Qt.DisplayRole, ))
            return True
        return False
        
    def flags(self, index):
        fl = super(self.__class__,self).flags(index)
        fl |= Qt.ItemIsEditable
        fl |= Qt.ItemIsSelectable
        fl |= Qt.ItemIsEnabled
        fl |= Qt.ItemIsDragEnabled
        fl |= Qt.ItemIsDropEnabled
        return fl
        
class EdgeThread(QtCore.QThread):
    threadEvent = QtCore.pyqtSignal(object, object, object)
    
    def __init__(self, parent=None):
        super(EdgeThread, self).__init__(parent)
        self.main = parent
        self.isRun = False
    
    def run(self):
        self.isRun = True
        json_data1 = None
        json_data2 = None
        json_data1 = edge_util.call_ocr(self.main.img_url, 'A')
        if self.main.isDocuOCR:
            print("DocuOCR called ................................")
            json_data2 = edge_util.call_ocr(self.main.img_url, 'B')
        self.threadEvent.emit(self.main.img_url, json_data1, json_data2)
        self.isRun = False
        
        
class Edge(QWidget):

    def __init__(self):
        QWidget.__init__(self, flags=Qt.Widget)

        self.raw_json = ''
        self.img_url = ''
        self.imageLabel = QLabel()
        self.imageLabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)        
        self.text_area = QTextEdit()
        self.text_area_docu = QTextEdit()
        self.frame_area = QFrame()
        self.frame_area.setFrameShape(QFrame.Box)
        self.list = QTableView()
        self.split_1 = QSplitter()
        self.split_2 = QSplitter()
        self.vbox = QVBoxLayout()
        self.container_vbox = QVBoxLayout()              
        self.init_widget()
        
        self.th = EdgeThread(self)
        self.th.threadEvent.connect(self.threadEventHandler)
        self.isDocuOCR = False

    def init_widget(self):       
        self.label1 = QLabel("사업자 번호 : ")
        self.label2 = QLabel("가맹점명 : ")
        self.label3 = QLabel("가맹점주소 : ")
        self.label4 = QLabel("승인일시 : ")
        self.label5 = QLabel("승인금액 : ")
        self.label6 = QLabel("부가세 : ")
        self.label7 = QLabel("카드번호 : ")
        self.label8 = QLabel("승인번호 : ")
        self.label9 = QLabel("공급금액 : ")
        self.label10 = QLabel("면세금액 : ")
        self.label11 = QLabel("봉사료 : ")
        self.edit_biz_no  = QLineEdit()
        self.edit_mest_nm = QLineEdit()
        self.edit_mest_addr  = QLineEdit()
        self.edit_apv_tm  = QLineEdit()
        self.edit_buy_amt = QLineEdit()
        self.edit_vat_amt = QLineEdit()
        self.edit_card_no = QLineEdit()
        self.edit_apv_no  = QLineEdit()
        self.edit_tax_ant_amt  = QLineEdit()
        self.edit_tax_expn_amt  = QLineEdit()
        self.edit_srv_fee  = QLineEdit()

        self.btnClipboard= QPushButton("Clipboard")
        self.btnClipboard.clicked.connect(self.doClipboard)
        self.btnRetry= QPushButton("Retry")
        self.btnRetry.clicked.connect(self.doRetry)
        self.btnSaveForTest = QPushButton("SaveForTest")
        self.btnSaveForTest.clicked.connect(self.saveForTest)
        self.btnCopyJson = QPushButton("Copy Json")
        self.btnCopyJson.clicked.connect(self.copyJson)

        self.btnSaveData = QPushButton("Save Data")
        self.btnSaveData.clicked.connect(self.saveData)
        self.btnDocuOcrOnOff = QPushButton("Docu OCR Off")
        self.btnDocuOcrOnOff.clicked.connect(self.docuOcrOnOff)
               
        layout = QGridLayout()
        layout.addWidget(self.label1      , 0, 0)
        layout.addWidget(self.edit_biz_no , 0, 1)
        layout.addWidget(self.label2      , 1, 0)
        layout.addWidget(self.edit_mest_nm, 1, 1)
        layout.addWidget(self.label3      , 2, 0)
        layout.addWidget(self.edit_mest_addr , 2, 1)
        layout.addWidget(self.label4      , 3, 0)
        layout.addWidget(self.edit_apv_tm , 3, 1)
        layout.addWidget(self.label5      , 4, 0)
        layout.addWidget(self.edit_buy_amt, 4, 1)
        layout.addWidget(self.label6      , 5, 0)
        layout.addWidget(self.edit_vat_amt, 5, 1)
        layout.addWidget(self.label7      , 6, 0)
        layout.addWidget(self.edit_card_no, 6, 1)
        layout.addWidget(self.label8      , 7, 0)
        layout.addWidget(self.edit_apv_no , 7, 1)
        layout.addWidget(self.label9      , 8, 0)
        layout.addWidget(self.edit_tax_ant_amt , 8, 1)
        layout.addWidget(self.label10      , 9, 0)
        layout.addWidget(self.edit_tax_expn_amt , 9, 1)
        layout.addWidget(self.label11      , 10, 0)
        layout.addWidget(self.edit_srv_fee , 10, 1)
        
        layout.addWidget(self.btnClipboard, 11, 0)
        layout.addWidget(self.btnRetry    , 11, 1)
        layout.addWidget(self.btnSaveForTest, 12, 0)
        layout.addWidget(self.btnCopyJson   , 12, 1)
        layout.addWidget(self.btnSaveData, 13, 0)
        layout.addWidget(self.btnDocuOcrOnOff, 13, 1)
        
        self.frame_area.setLayout(layout)      
        
        self.imageLabel.resize(400,100)
        self.imageLabel.resizeEvent = self.resizeImage
        self.list.selectionChanged = self.selectionEvent
        self.setWindowTitle("Edge")
        self.split_1.addWidget(self.imageLabel)
        self.split_1.addWidget(self.text_area) 
        self.split_1.addWidget(self.frame_area) 
        self.split_1.addWidget(self.text_area_docu)
        self.container_vbox.addWidget(self.split_1)    
        self.split_2.setOrientation(Qt.Vertical)
        self.split_2.addWidget(self.split_1)
        self.split_2.addWidget(self.list)
        self.vbox.addWidget(self.split_2)
        self.setLayout(self.vbox)
        self.setGeometry(50, 50, 1024, 768)
        self.image = QImage()        
    
    def paintEvent(self, event):
        #painter = QPainter(self.image)
        #self.drawBox()
        pass
        
    def drawBox(self) :
        painter = QPainter(self.image)
        painter.setPen(QPen(Qt.red,3))
        
        raw = json.loads(self.raw_json)
        fields = raw['images'][0]['fields']
        for field in fields:
            x1 = field['boundingPoly']['vertices'][0]['x']
            y1 = field['boundingPoly']['vertices'][0]['y']
            x2 = field['boundingPoly']['vertices'][1]['x']
            y2 = field['boundingPoly']['vertices'][1]['y']
            x3 = field['boundingPoly']['vertices'][2]['x']
            y3 = field['boundingPoly']['vertices'][2]['y']
            x4 = field['boundingPoly']['vertices'][3]['x']
            y4 = field['boundingPoly']['vertices'][3]['y']
            p1 = QPoint(x1, y1)
            p2 = QPoint(x2, y2)
            p3 = QPoint(x3, y3)
            p4 = QPoint(x4, y4)
            painter.drawLine(p1, p2)
            painter.drawLine(p2, p3)
            painter.drawLine(p3, p4)
            painter.drawLine(p4, p1)            
               
        
    def showGeneral(self, json_data):       
        self.image = QImage()
        self.image.loadFromData(requests.get(self.img_url).content)
        
        #pix = QPixmap(self.image).scaled(self.imageLabel.width(),   self.imageLabel.height(),                                                         Qt.KeepAspectRatio)
        self.imageLabel.setPixmap(QPixmap(self.image))            
        #self.imageLabel.adjustSize()
        #self.scaleFactor = 1.0
        #self.scaleImage(1)
        
        self.edit_biz_no.setText('')
        self.edit_mest_nm.setText('')
        self.edit_mest_addr.setText('')
        self.edit_apv_tm.setText('')
        self.edit_buy_amt.setText('')
        self.edit_vat_amt.setText('')
        self.edit_card_no.setText('')
        self.edit_apv_no.setText('')        
        self.text_area.setText('처리중...')                      
        self.text_area_docu.setText('')
        
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0  
        
        row_val = 0        
        for ix in self.list.selectedIndexes():
            row_val = ix.row()  

        if self.img_url.startswith('http'):                                  
            resp_data = json_data['RESP_DATA']
            self.raw_json = resp_data['OCR_RAW']
            self.drawBox()
            self.text_area.setText(resp_data['OCR_TEXT'])           
            self.edit_biz_no.setText(resp_data['MEST_BIZ_NO'])
            self.edit_mest_nm.setText(resp_data['MEST_NM'] + ' / ' + resp_data['MEST_TEL_NO']+ ' / ' + resp_data['MEST_REPR_NM'])
            self.edit_mest_addr.setText(resp_data['MEST_ADDR'])
            self.edit_apv_tm.setText(resp_data['TX_DT'] + ' ' + resp_data['TX_TM'])
            self.edit_buy_amt.setText(resp_data['TX_AMT'])
            self.edit_vat_amt.setText(resp_data['TAX_AMT'])
            self.edit_card_no.setText(resp_data['OCR_CD_NO'])
            self.edit_apv_no.setText(resp_data['OCR_PAY_NO'])             
            self.edit_tax_ant_amt.setText(resp_data['SPLY_AMT'])             
            self.edit_tax_expn_amt.setText(resp_data['TAX_EXPN_AMT'])              
            self.edit_srv_fee.setText(resp_data['SRV_FEE'])             
            self.edit_biz_no.setStyleSheet('border: 1px solid black;')
            self.edit_mest_nm.setStyleSheet('border: 1px solid black;')
            self.edit_mest_addr.setStyleSheet('border: 1px solid black;')
            self.edit_apv_tm.setStyleSheet('border: 1px solid black;')
            self.edit_buy_amt.setStyleSheet('border: 1px solid black;')
            self.edit_vat_amt.setStyleSheet('border: 1px solid black;')
            self.edit_card_no.setStyleSheet('border: 1px solid black;')
            self.edit_apv_no.setStyleSheet('border: 1px solid black;')
 
            model = self.list.model()
            
            if str(self.edit_biz_no.text()) != str(model.getData(row_val, 1)):
                self.edit_biz_no.setStyleSheet('border: 1px solid red;')
            #if str(self.edit_mest_addr.text()) != str(model.getData(row_val, 2)):
            #    self.edit_mest_addr.setStyleSheet('border: 1px solid red;')
            #if str(self.edit_apv_tm.text())[:4] != str(model.getData(row_val, 3)).zfill(6)[:4]:
            #    self.edit_apv_tm.setStyleSheet('border: 1px solid red;')
            
            buy_amt = 0.
            if self.edit_buy_amt.text() != '':
                buy_amt = float(self.edit_buy_amt.text())
            if  buy_amt != float(model.getData(row_val, 4)):
                self.edit_buy_amt.setStyleSheet('border: 1px solid red;')
            
            vat_amt = 0.
            if self.edit_vat_amt.text() != '':
                vat_amt = float(self.edit_vat_amt.text())
            
            if abs(vat_amt - float(model.getData(row_val, 5))) > 2:
                self.edit_vat_amt.setStyleSheet('border: 1px solid red;')
            
            apv_no = 0.
            if self.edit_apv_no.text() != '':
                apv_no = float(self.edit_apv_no.text())
                
            if apv_no != float(model.getData(row_val, 7)):
                self.edit_apv_no.setStyleSheet('border: 1px solid red;')  
                                 
    def showReceipt(self, json_data):  
        resp_data = json_data['RESP_DATA']
        docu_text = '*** 네이버 Document OCR 결과 ***\n\n'
        docu_text += '사업자번호        : ' + resp_data['MEST_BIZ_NO'] + '\n'
        docu_text += '가맹점명          : ' +  resp_data['MEST_NM'] + '\n'
        docu_text += '가맹점대표자명  : ' +  resp_data['MEST_REPR_NM'] + '\n'
        docu_text += '지점명           : ' +  resp_data['DEPT_NM'] + '\n'
        docu_text += '가맹점주소       : ' +  resp_data['MEST_ADDR'] + '\n'
        docu_text += '가맹점전화번호  : ' +  resp_data['MEST_TEL_NO'] + '\n'
        docu_text += '거래일자         : ' +  resp_data['TX_DT'] + '\n'
        docu_text += '거래시간         : ' +  resp_data['TX_TM'] + '\n'
        docu_text += '카드번호           : ' +  resp_data['OCR_CD_NO'] + '\n'
        docu_text += '카드사           : ' +  resp_data['OCR_CD_CORP'] + '\n'
        docu_text += '승인번호         : ' +  resp_data['OCR_PAY_NO'] + '\n'
        docu_text += '거래금액         : ' +  resp_data['TX_AMT'] + '\n'
        docu_text += '부가세         : ' +  resp_data['TAX_AMT'] + '\n'
        docu_text += '공급금액         : ' +  resp_data['SPLY_AMT'] + '\n'
        docu_text += '면세금액         : ' +  resp_data['TAX_EXPN_AMT'] + '\n\n'
            
        items = resp_data['REC']
        for item in items:
            docu_text += '품목 : ' + item['ITEM_NM'] + ' ('
            docu_text += item['ITEM_CNT'] + ') ' 
            docu_text += item['ITEM_AMT'] + ' '
            docu_text += item['ITEM_UNIT_AMT'] + '\n'
            
                    
        self.text_area_docu.setText(docu_text)

    def selectionEvent(self, selected, deselected):   
        img_url = ''  
        for ix in self.list.selectedIndexes():
            img_url = ix.data(Qt.DisplayRole) # or ix.data()   
        if img_url.startswith('https'):
            self.img_url = img_url
            self.doIt()
                   
    def doIt(self):
        if self.th.isRun == False:
            self.th.start()            
    def resizeImage(self, event):         
        self.imageLabel.setPixmap(QPixmap(self.image).scaled(self.imageLabel.width(), 
                                                             self.imageLabel.height(), 
                                                             Qt.KeepAspectRatio))        
        self.imageLabel.show()
        
    def resizeEvent(self, event):
        self.resizeImage(event)

    def scaleImage(self, factor):        
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())
 
    def doClipboard(self):
        self.img_url = clipboard.paste();
        self.doIt()

    def doRetry(self):
        self.doIt()

    
    def copyJson(self):
        clipboard.copy(urllib.parse.unquote(self.raw_json))
    
    def saveData(self):
        #print(self.list.model()._data)
        pass
    
    def docuOcrOnOff(self):
        if self.isDocuOCR:
            self.btnDocuOcrOnOff.setText('Docu OCR Off')
            self.isDocuOCR = False
        else:
            self.btnDocuOcrOnOff.setText('Docu OCR On')
            self.isDocuOCR = True
            self.th.start()
        
    
    def threadEventHandler(self, img_url, json_data1, json_data2):
        print('thread called...')
        if self.img_url == img_url:
            self.showGeneral(json_data1) 
            if self.isDocuOCR:
                #print("json_data2 : ", json_data2)
                self.showReceipt(json_data2)
        else:
            self.th.start()

    def saveForTest(self):       
        if self.img_url == '':
            return

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        options |= QFileDialog.DontConfirmOverwrite
        
        fileDialog = QFileDialog()
        fileDialog.setDefaultSuffix("csv")
        fileDialog.setOptions(options)
        fileName, _ = fileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","CSV Files (*.csv)")
        if fileName:
            print(fileName)
            
            if os.path.isfile(fileName):
                good = pd.read_csv(fileName,encoding='utf-8', low_memory=False)
            else:
                good = pd.DataFrame(columns=['mest_nm', 'mest_biz_no', 
                                             'apv_dt', 'apv_tm', 'buy_sum', 
                                             'vat_amt', 'card_no', 'apv_no', 'rcpt_img_url'])
            
            if (good['rcpt_img_url'] == self.img_url).any():
                QMessageBox.about(self, "추가", "이미 존재하는 데이터입니다.")
            else:
                good = good.append({'mest_nm':self.edit_mest_nm.text(),
                                    'mest_biz_no':self.edit_biz_no.text(),
                                    'apv_dt':self.edit_apv_dt.text(),
                                    'apv_tm':self.edit_apv_tm.text(),
                                    'buy_sum':self.edit_buy_amt.text(),
                                    'vat_amt':self.edit_vat_amt.text(),
                                    'card_no':self.edit_card_no.text(),
                                    'apv_no':self.edit_apv_no.text(),
                                    'rcpt_img_url':self.img_url}, ignore_index=True)           
                good.to_csv(fileName, mode='w', index=False, encoding='utf-8-sig')
                QMessageBox.about(self, "추가", "추가되었습니다.")
    
               
if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = Edge()
    form.show()   
    #ptcl_UTLZ_1711011808382
    data = pd.read_csv('edge_ui.csv',
                       encoding='utf-8-sig', 
                       low_memory=False) 
    data = data.sample(frac=1, 
                       random_state=1).dropna(subset=['mest_bz_reg_no', 'rcpt_img_url']).iloc[0:3000]
    data = data[['mest_nm', 'mest_bz_reg_no', 'apv_dt', 'apv_tm', 'buy_sum', 'vat_amt', 'card_no', 'apv_no', 'rcpt_img_url']]    
    model = PandasModel(data)
    form.list.setModel(model)    
    sys.exit(app.exec_())