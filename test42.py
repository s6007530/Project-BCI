from PyQt5.QtWidgets import (QPushButton, QLabel, QVBoxLayout, QApplication, QWidget
                             ,QHBoxLayout, QLineEdit, QMessageBox,QDesktopWidget,QGridLayout, QRadioButton,QCheckBox,QTextEdit,QFileDialog)
import serial
import sys
import csv
import numpy as np
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
from scipy.fftpack import fft
import struct
from PyQt5.QtCore import *
import time
from scipy.signal import butter, filtfilt, cheby2, firwin
import os

def cheby2_filter_lowpass(data,rs,cof,fs,ftype,order,analog=True, output='ba'):
    nyq = fs
    cof = cof/nyq
    b, a = cheby2(order, rs, cof, ftype)
    filter_data = filtfilt(b,a, data)
    return filter_data

def byte_to_int(byte):
  num = int.from_bytes(byte,byteorder='little')
  bin2 = 2**((len(byte))*8)
  if num>bin2/2:
    num = num-bin2
  return num

def DTABG(x,y):
    y1 = 0
    for i in range(len(x)):
        if x[i]>=1 and x[i]<=45:
            y1+=y[i]
    return y1

def alpha_beta(x,y):
    y1 =0
    y2 =0
    for i in range(len(x)):
        if x[i]>=8 and x[i]<13:
            y1+=y[i]
        elif x[i]>=13 and x[i]<30:
            y2+=y[i]
    return np.array([y1,y2])

def alpha(x,y):
    y1 = 0
    for i in range(len(x)):
        if x[i]>=13 and x[i]<30:
            y1+=y[i]
    return y1

def beta(x,y):
    y1 = 0
    for i in range(len(x)):
        if x[i]>=13 and x[i]<30:
            y1+=y[i]
    return y1

class Notepad(QWidget):

    def __init__(self):
        super(Notepad,self).__init__()
        self.setWindowTitle('Data')
        self.setMaximumSize(500,500)
        self.setStyleSheet('QWidget{background-color:rgb(255,255,255);color =black}')
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
        self.init_ui()

    def init_ui(self):
        self.Label = QLabel('Time(s)           Alpha_1           Beta_1          Alpha_2         Beta_2')
        self.opn_btn = QPushButton('Open')
        self.sv_btn = QPushButton('Save')
        self.clr_btn = QPushButton('Clear')
        self.text = QTextEdit(self)
        self.text.setAlignment(Qt.AlignLeft)

        self.opn_btn.clicked.connect(lambda: self.open())
        self.sv_btn.clicked.connect(lambda: self.save())
        self.clr_btn.clicked.connect(lambda: self.clear())

        self.v = QVBoxLayout()
        self.v.addWidget(self.opn_btn)
        self.v.addWidget(self.clr_btn)
        self.v.addWidget(self.sv_btn)

        self.v2 =QVBoxLayout()
        self.v2.addWidget(self.Label)
        self.v2.addWidget(self.text)

        self.h = QHBoxLayout()
        self.h.addLayout(self.v2)
        self.h.addLayout(self.v)
        self.setLayout(self.h)

        self.show()
    def clear(self):
        self.text.clear()

    def save(self):
        filename = QFileDialog.getSaveFileName(self, 'Save File', os.getenv('HOME'), 'Text files (*.txt)')
        if filename != ('', ''):
            with open(filename[0], 'w') as f:
                my_text = self.text.toPlainText()
                f.write(my_text)

    def open(self):
        filename = QFileDialog.getOpenFileName(self,'Save File', os.getenv('HOME'),'Text files (*.txt)')
        if filename != ('', ''):
            with open(filename[0],'r') as f:
                file_text = f.read()
                self.text.setText(file_text)


class window(QWidget):

    def __init__(self):
        super(window,self).__init__()
        self.init_ui()
        self.setWindowTitle('Project')
        self.resize(1280,640)
        self.setStyleSheet('QWidget{background-color:rgb(255,255,255);color =black}')
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

    def init_ui(self):
        # identify variable

        self.storage1 = []
        self.storage2 = []
        self.value = []
        self.califlag = False
        self.ready2 = False
        self.treshold = 23
        self.revalue()
        self.comflag = 0
        self.forceflag = 0
        self.collectflag = False
        self.color1 = (255,0,0)
        self.color2 = (0,0,255)

        # widget component for generate data

        self.reply = QMessageBox()
        self.LineEdit1 = QLineEdit('COM9')
        self.LineEdit2 = QLineEdit('COM3')
        self.LineEdit3 = QLineEdit('3')
        self.LineEdit4 = QLineEdit('2')
        self.Label1 = QLabel('State:')
        self.Label2 = QLabel('State:')
        self.Label4 = QLabel('Time per Collections:')
        self.Label3 = QLabel('Number of Collections:')
        self.Label5 = QLabel('Collection State: 0')
        self.Label6 = QLabel('Second pass: %s' % (self.a,))
        self.Label7 = QLabel('Please Connect')
        self.np = Notepad()

        self.LineEdit1.setAlignment(Qt.AlignCenter)
        self.LineEdit2.setAlignment(Qt.AlignCenter)
        self.LineEdit3.setAlignment(Qt.AlignCenter)
        self.LineEdit4.setAlignment(Qt.AlignCenter)

        self.LineEdit1.setMaximumSize(250,40)
        self.LineEdit2.setMaximumSize(250,40)
        self.Label3.setMaximumSize(100,40)
        self.Label4.setMaximumSize(100,40)
        self.Label5.setMaximumSize(100,40)
        self.Label6.setMaximumSize(100,40)
        self.Label7.setMaximumSize(100, 40)
        self.LineEdit3.setMaximumSize(100,40)
        self.LineEdit4.setMaximumSize(100,40)

        # widget component for control

        self.start_btn = QPushButton('Start')
        self.stop_btn = QPushButton('Stop')
        self.col_btn = QPushButton('Collect')
        self.clr_btn = QPushButton('Clear')
        self.con_btn1 = QPushButton('Connect')
        self.con_btn2 = QPushButton('Connect')
        self.chkbox1 = QCheckBox('Channel 1')
        self.chkbox2 = QCheckBox('Channel 2')
        self.filter = QCheckBox('Filter')
        self.com_btn = QRadioButton('Command')
        self.force_btn = QRadioButton('Force')
        self.cali_btn = QPushButton('Calibrate')

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.com_btn.setEnabled(False)
        self.force_btn.setEnabled(False)
        self.col_btn.setEnabled(False)
        self.clr_btn.setEnabled(False)
        self.chkbox2.setEnabled(False)
        self.chkbox1.setEnabled(False)
        self.cali_btn.setEnabled(False)

        self.start_btn.setMaximumSize(80, 80)
        self.stop_btn.setMaximumSize(80, 80)
        self.clr_btn.setMaximumSize(80, 80)
        self.col_btn.setMaximumSize(80, 80)
        self.con_btn1.setMaximumSize(80, 80)
        self.con_btn2.setMaximumSize(80, 80)
        self.chkbox1.setMaximumSize(100, 40)
        self.chkbox2.setMaximumSize(100, 40)
        self.com_btn.setMaximumSize(100,40)
        self.force_btn.setMaximumSize(100, 40)
        self.cali_btn.setMaximumSize(80, 80)

        self.start_btn.setStyleSheet('QPushButton{background-color:rgb(240,128,128);color:black;font-size:14px}')
        self.stop_btn.setStyleSheet('QPushButton{background-color:rgb(255,165,0);color:black;font-size:14px}')
        self.clr_btn.setStyleSheet('QPushButton{background-color:rgb(173,255,47);color:black;font-size:14px}')
        self.col_btn.setStyleSheet('QPushButton{background-color:rgb(135,206,235);color:black;font-size:14px}')
        self.con_btn1.setStyleSheet('QPushButton{background-color:rgb(255,250,205);color:black;font-size:12px}')
        self.con_btn2.setStyleSheet('QPushButton{background-color:rgb(255,250,205);color:black;font-size:12px}')
        self.com_btn.setStyleSheet('QRadioButton{background-color:rgb(255,255,255);color:black;font-size:16px}')
        self.force_btn.setStyleSheet('QRadioButton{background-color:rgb(255,255,255);color:black;font-size:16px}')
        self.cali_btn.setStyleSheet('QPushButton{background-color:rgb(255,255,0);color:black;font-size:14px}')
        self.Label1.setStyleSheet('QLabel{font-size:14px}')
        self.Label2.setStyleSheet('QLabel{font-size:14px}')
        self.Label7.setStyleSheet('QLabel{font-size:14px}')

        # control system

        self.start_btn.clicked.connect(lambda: self.start())
        self.stop_btn.clicked.connect(lambda: self.stop())
        self.clr_btn.clicked.connect(lambda: self.clear())
        self.col_btn.clicked.connect(lambda: self.collect())
        self.con_btn1.clicked.connect(lambda: self.connect1())
        self.con_btn2.clicked.connect(lambda: self.connect2())
        self.com_btn.clicked.connect(lambda: self.command())
        self.force_btn.clicked.connect(lambda: self.force())
        self.cali_btn.clicked.connect(lambda: self.calibrate())

        # graph making

        self.tdm1 = pg.PlotWidget(title="Ch1")
        self.tdm1.setBackground('w')
        self.tdm2 = pg.PlotWidget(title="Ch2")
        self.tdm2.setBackground('w')
        self.fft = pg.PlotWidget(title="Frequency Domain Graph")
        self.fft.setBackground('w')
        #self.ratio = pg.PlotWidget(title='alpha beta ratio')
        #self.ratio.setBackground('w')

        # time domain graph

        #self.tdm1.setLabel('left', 'Value', units='V')
        #self.tdm1.setLabel('bottom', 'Time', units='s')
        self.tdm1.setYRange(-1200, 1200)
        self.tdm2.setYRange(-4000, 4000)
        self.p1_1 = self.tdm1.plot()
        self.p1_1.setPen(self.color1)
        self.p1_2 = self.tdm2.plot()
        self.p1_2.setPen(self.color2)
        self.T = 2 * self.sampling
        self.xd = np.linspace(self.ii / self.T, self.ii / self.T + 1, self.T)
        self.xd2 = np.linspace(0.0, self.sampling - 1, self.sampling)
        self.data1_raw = np.zeros(self.sampling)
        self.data2_raw = np.zeros(self.sampling)
        self.data1_fil = np.zeros(self.sampling)
        self.data2_fil = np.zeros(self.sampling)
        self.data1 = np.zeros(self.T)
        self.data2 = np.zeros(self.T)
        # frequency domain graph

        self.fft.setXRange(1, 50)
        self.fft.setYRange(0, 200)
        self.p2_1 = self.fft.plot()
        self.p2_1.setPen(self.color1)

        self.p2_2 = self.fft.plot()
        self.p2_2.setPen(self.color2)

        # alpha beta ratio graph

        #self.ratio.setYRange(0, 5)
        #self.ratio.setLabel('left', 'ratio', units='')
        #self.ratio.setLabel('bottom', 'Times', units='')
        #self.p3_1 = self.ratio.plot()
        #self.p3_1.setPen(self.color1)
        #self.p3_2 = self.ratio.plot()
        #self.p3_2.setPen(self.color2)
        self.storeX = np.arange(1, 11)
        self.storeY1 = np.zeros(10)
        self.storeY2 = np.zeros(10)

        # sequencing

        v_conbox1 = QVBoxLayout()
        h_conbox1 = QHBoxLayout()
        v_conbox1.addWidget(self.LineEdit1)
        h_conbox1.addWidget(self.con_btn1)
        h_conbox1.addWidget(self.Label1)
        v_conbox1.addLayout(h_conbox1)

        v_conbox2 = QVBoxLayout()
        h_conbox2 = QHBoxLayout()
        v_conbox2.addWidget(self.LineEdit2)
        h_conbox2.addWidget(self.con_btn2)
        h_conbox2.addWidget(self.Label2)
        v_conbox2.addLayout(h_conbox2)

        h_colbox1 = QHBoxLayout()
        h_colbox1.addWidget(self.Label3)
        h_colbox1.addWidget(self.LineEdit3)

        h_colbox2 = QHBoxLayout()
        h_colbox2.addWidget(self.Label4)
        h_colbox2.addWidget(self.LineEdit4)

        g_colbox = QGridLayout()
        #g_colbox.addWidget(self.Label7)
        g_colbox.addLayout(h_colbox1,1,0)
        g_colbox.addLayout(h_colbox2, 2, 0)
        g_colbox.addWidget(self.Label5,1,1)
        g_colbox.addWidget(self.Label6, 2, 1)

        v_showbox = QVBoxLayout()
        v_showbox.addWidget(self.Label5)
        v_showbox.addWidget(self.Label6)


        v_stressbox = QVBoxLayout()
        v_stressbox.addWidget(self.com_btn)
        v_stressbox.addWidget(self.force_btn)

        h_ctrbox = QHBoxLayout()
        h_ctrbox.addLayout(v_conbox1)
        h_ctrbox.addLayout(v_conbox2)
        h_ctrbox.addLayout(g_colbox)
        h_ctrbox.addLayout(v_stressbox)
        h_ctrbox.addWidget(self.start_btn)
        h_ctrbox.addWidget(self.stop_btn)
        h_ctrbox.addWidget(self.clr_btn)
        h_ctrbox.addWidget(self.col_btn)
        h_ctrbox.addWidget(self.cali_btn)

        h_chkbox = QHBoxLayout()
        h_chkbox.addWidget(self.chkbox1)
        h_chkbox.addWidget(self.chkbox2)
        h_chkbox.addWidget(self.Label7)

        v_ratiobox = QVBoxLayout()
        v_ratiobox.addWidget(self.np)
        v_ratiobox.addLayout(h_chkbox)

        v_tdmbox = QVBoxLayout()
        v_tdmbox.addWidget(self.tdm2)

        g_grhbox = QGridLayout()
        g_grhbox.setColumnStretch(2, 1)
        g_grhbox.setColumnStretch(0, 2)
        g_grhbox.addWidget(self.tdm1,0,0)
        g_grhbox.addLayout(v_tdmbox, 1, 0)
        g_grhbox.addWidget(self.fft, 0, 2)
        g_grhbox.addLayout(v_ratiobox, 1, 2)

        v_totbox = QVBoxLayout()
        v_totbox.addLayout(h_ctrbox)
        v_totbox.addLayout(g_grhbox)
        self.setLayout(v_totbox)
        self.show()

# control function

    def start(self):
        self.clr_btn.setEnabled(True)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.com_btn.setEnabled(True)
        self.chkbox1.setEnabled(True)
        self.chkbox2.setEnabled(True)
        self.cali_btn.setEnabled(True)
        if self.LineEdit3.text() == '' or self.LineEdit4.text() == '':
            self.Label7.setText('Please Enter Data')
        elif bool(int(self.LineEdit3.text()) < 1) or bool(int(self.LineEdit4.text()) < 1):
            self.Label7.setText('Please Enter Data')
        else:
            self.state = True
            self.plotgraph()
            self.Label7.setText('Start')
            self.LineEdit3.setEnabled(False)
            self.LineEdit4.setEnabled(False)

    def plotgraph(self):
        self.time = QtCore.QTimer()
        if self.state == True:
            self.col_btn.setEnabled(True)
            if self.ser1.isOpen() == False and self.ready1 == False:
                self.ser1.open()
            self.clr_btn.setEnabled(True)
            self.time.timeout.connect(lambda: self.input())
            self.time.start(4)
        else:
            self.col_btn.setEnabled(False)
            self.time.stop()
            self.start_btn.setEnabled(True)
            if self.ser1.isOpen() == True and self.ready1 == True:
                self.ser1.close()
                self.ready1 = False
    def input(self):
        self.ser_bytes = self.ser1.readline()
        self.counter+=1
        print(self.counter,self.ser1.inWaiting())
        self.ser_bytes = self.ser_bytes[0:-1]
        if len(self.ser_bytes) == 8:
            self.bin1 = self.ser_bytes[0:4]
            self.bin2 = self.ser_bytes[4:8]
            self.data1_raw[self.i%self.sampling] = struct.unpack("<l", self.bin1)[0]
            self.data2_raw[self.i%self.sampling] = struct.unpack("<l", self.bin2)[0]
            self.ready1 = True
            #print(self.data1[1])
            self.create_data()
        if len(self.ser_bytes) == 4:
            self.bin1 = self.ser_bytes[0:4]
            self.data1_raw[self.i % self.sampling] = struct.unpack("<l", self.bin1)[0]
            self.ready1 = True
            self.create_data()
    def create_data(self):
        self.i += 1
        self.a += 1
        self.b += 1
        self.bb += 1
        self.lowcut = 50
        self.order = 10
        if self.b % self.sampling == 0:
            self.data1_fil = cheby2_filter_lowpass(self.data1_raw, 20, self.lowcut, self.sampling, 'low',self.order)
            self.data2_fil = cheby2_filter_lowpass(self.data2_raw, 20, self.lowcut, self.sampling, 'low',self.order)
        if self.b >= self.sampling:
            if self.b == self.sampling:
                self.bb = 1
            if self.bb % 10 == 1:
                if self.bb % self.T == 491:
                    self.data1[((self.bb - 1) % self.T): self.T] = \
                        self.data1_fil[((self.bb - 1) % self.sampling): self.sampling]
                    self.data2[((self.bb - 1) % self.T): self.T] = \
                        self.data2_fil[((self.bb - 1) % self.sampling): self.sampling]
                    self.p1_1.setData(y=self.data1, x=self.xd)
                    self.p1_2.setData(y=self.data2, x=self.xd)
                elif self.bb % self.sampling == 241:
                    self.data1[((self.bb - 1) % self.T):((self.bb + 9) % self.T)] = \
                        self.data1_fil[((self.bb - 1) % self.sampling): self.sampling]
                    self.data2[((self.bb - 1) % self.T):((self.bb + 9) % self.T)] = \
                        self.data2_fil[((self.bb - 1) % self.sampling): self.sampling]
                    self.p1_1.setData(y=self.data1, x=self.xd)
                    self.p1_2.setData(y=self.data2, x=self.xd)
                else:
                    self.data1[((self.bb-1) % self.T):((self.bb+9) % self.T)] = \
                        self.data1_fil[((self.bb-1) % self.sampling):((self.bb+9) % self.sampling)]
                    self.data2[((self.bb - 1) % self.T):((self.bb + 9) % self.T)] = \
                        self.data2_fil[((self.bb - 1) % self.sampling):((self.bb + 9) % self.sampling)]
                    self.p1_1.setData(y=self.data1, x=self.xd)
                    self.p1_2.setData(y=self.data2, x=self.xd)
            # self.data1[(self.bb - 1) % self.T] = \
            #    self.data1_fil[(self.bb - 1) % self.sampling)]
            # self.data2[(self.bb - 1) % self.T] = \
            #    self.data2_fil[(self.bb - 1) % self.sampling)]
            # self.p1_1.setData(y=self.data1, x=self.xd)
            # self.p1_2.setData(y=self.data2, x=self.xd)
            self.ptr += 1
            if self.ptr % self.T == self.T-1:
                #self.ratio.enableAutoRange('y', True)
                self.fft.enableAutoRange('y', True)
                self.tdm1.enableAutoRange('y', True)
                self.tdm2.enableAutoRange('y', True)
            elif self.ptr % self.T == 0:
                self.tdm1.enableAutoRange('y', False)
                self.tdm2.enableAutoRange('y', False)
                self.fft.enableAutoRange('y', False)
            self.timer = self.a//self.sampling
            self.Label6.setText('Second pass: %s' % (self.timer,))
            if self.count//self.sampling == 10:
                self.storeY2.fill(0)
                self.storeY1.fill(0)
                self.count -= 10*self.sampling
            if self.count2 == self.T:
                self.data1 = np.zeros(self.T)
                self.data2 = np.zeros(self.T)
                self.data1.fill(0)
                self.data2.fill(0)
                self.count2 -= self.T
            self.count += 1
            self.count2 += 1
            if self.count2 == 250 or self.count2 == 500:
                if self.count2 == 250:
                    self.calfft_1 = 1 / self.sampling * abs(fft(self.data1[0:250]))
                    self.calfft_2 = 1 / self.sampling * abs(fft(self.data2[0:250]))
                elif self.count2 == 500:
                    self.calfft_1 = 1 / self.sampling * abs(fft(self.data1[250:500]))
                    self.calfft_2 = 1 / self.sampling * abs(fft(self.data2[250:500]))
                self.calfft_1[0] = 0
                self.calfft_2[0] = 0
                self.freq1 = DTABG(self.xd2, self.calfft_1)
                self.freq2 = DTABG(self.xd2, self.calfft_2)
                self.ra1 = (alpha_beta(self.xd2, self.calfft_1)/self.freq1)*100
                self.ra2 = (alpha_beta(self.xd2, self.calfft_2)/self.freq2)*100
                if self.previous != self.timer:
                    #print(type(self.np.text.toPlainText()))
                    i = 10
                    self.np.text.append('%s'%(self.timer)+' '*i
                                        +'%s'%(round(self.ra1[0],2))+' '*i
                                        +'%s'%(round(self.ra1[1],2))+' '*i
                                        +'%s'%(round(self.ra2[0],2))+' '*i
                                        +'%s'%(round(self.ra2[1],2)))
                self.previous = self.timer
                if self.ra1[0] != 0:
                    self.ratio_1 = self.ra1[1]/self.ra1[0]
                    self.storeY1[((self.i-250)//self.sampling) % 10] = self.ratio_1
                    #if self.chkbox1.isChecked() == True:
                        #self.p3_1.setData(y=self.storeY1, x=self.storeX)
                if self.ra2[0] != 0:
                    self.ratio_2 = self.ra2[1]/self.ra2[0]
                    self.storeY2[((self.i-250)//self.sampling) % 10] = self.ratio_2
                    #if self.chkbox2.isChecked() == True:
                        #self.p3_2.setData(y=self.storeY2, x=self.storeX)
                if self.chkbox1.isChecked() == True:
                    self.p2_1.setData(y=self.calfft_1, x=self.xd2)
                elif self.chkbox1.isChecked() == False:
                    self.p2_1.clear()
                    #self.p3_1.clear()
                if self.chkbox2.isChecked() == True:
                    self.p2_2.setData(y=self.calfft_2, x=self.xd2)
                elif self.chkbox2.isChecked() == False:
                    self.p2_2.clear()
                    #self.p3_2.clear()
                if self.ready2 == True:
                    self.allalpha = alpha(self.xd2, self.calfft_1)
                    self.allfreq = DTABG(self.xd2, self.calfft_1)
                    self.exp = self.allalpha / self.allfreq * 100
                    if self.exp >= self.treshold:
                        self.ser2.write(bytes('1', 'utf-8'))
                        self.Label7.setText('Open')
                    else:
                        self.ser2.write(bytes('2', 'utf-8'))
                        self.Label7.setText('Close')
                if self.califlag == True:
                    #print('hello')
                    self.aph = alpha(self.xd2, self.calfft_1)
                    self.freq = DTABG(self.xd2, self.calfft_1)
                    self.p = self.aph / self.freq * 100
                    self.value.append(self.p)
                    if self.timer - self.clock == 9:
                        if self.calitime == 1:
                            for i in self.value:
                                self.k += i
                            self.k = self.k / len(self.value)
                            print(self.k)
                            self.value = []
                            self.calitime = 2
                            self.califlag = False
                            self.Label7.setStyleSheet('QLabel{font-size:14px}')
                            self.Label7.setText('First Calibrate')
                        elif self.calitime == 2:
                            for i in self.value:
                                self.j += i
                            self.j = self.j / len(self.value)
                            print(self.j)
                            self.value = []
                            self.treshold = (self.k + self.j) / 2
                            print(self.k,self.j,self.treshold)
                            self.caltime = 1
                            self.Label7.setStyleSheet('QLabel{font-size:14px}')
                            self.Label7.setText('Second Calibrate')
                            self.califlag = False
                            self.com_btn.setEnabled(True)




        # collect part
            if self.collectflag == False:
                self.stop_btn.setEnabled(True)
                self.clr_btn.setEnabled(True)
                if self.coltime == int(self.LineEdit3.text()):
                    self.col_btn.setEnabled(False)
                else:
                    self.col_btn.setEnabled(True)
            elif self.collectflag == True:
                self.col_btn.setEnabled(False)
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(False)
                self.clr_btn.setEnabled(False)
                if int(self.LineEdit4.text()) != 1 and self.a % self.sampling == 0:
                    print(len(self.col1_1))
                    print(len(self.data1))
                    if len(self.col1_1) > self.T or len(self.col1_1) == int(self.LineEdit4.text()):
                        self.collectflag = False
                        print(1.1)
                    elif len(self.col1_1) == 0:
                        #print('hello')
                        if len(self.col1_1) == 0:
                            self.col1_1 = np.append(self.col1_1, self.data1)
                        else:
                            self.col1_1 = np.vstack((self.col1_1, self.data1))
                        if len(self.col1_2) == 0:
                            self.col1_2 = np.append(self.col1_2, self.data2)
                        else:
                            self.col1_2 = np.vstack((self.col1_2, self.data2))
                        if len(self.col2_1) != 0:
                            self.col2_1 = np.vstack((self.col2_1, self.calfft_1))
                        else:
                            self.col2_1 = np.append(self.col2_1, self.calfft_1)
                        if len(self.col2_2) != 0:
                            self.col2_2 = np.vstack((self.col2_2, self.calfft_2))
                        else:
                            self.col2_2 = np.append(self.col2_2, self.calfft_2)
                        self.col3_1 = np.append(self.col3_1, np.array([self.ratio_1]))
                        self.col3_2 = np.append(self.col3_2, np.array([self.ratio_2]))
                        self.ab1 = np.append(self.ab1,np.array([self.ra1]))
                        self.ab2 = np.append(self.ab2,np.array([self.ra2]))
                        print(1.2)
                    elif bool(len(self.col1_1) == int(self.LineEdit4.text()) - 1) or bool(
                                len(self.col1_1) == self.T and int(self.LineEdit4.text()) == 2):
                        self.col1_1 = np.vstack((self.col1_1, self.data1))
                        self.col1_2 = np.vstack((self.col1_2, self.data2))
                        self.col2_1 = np.vstack((self.col2_1, self.calfft_1))
                        self.col2_2 = np.vstack((self.col2_2, self.calfft_2))
                        self.col3_1 = np.append(self.col3_1, np.array([self.ratio_1]))
                        self.col3_2 = np.append(self.col3_2, np.array([self.ratio_2]))
                        self.ab1 = np.append(self.ab1, np.array([self.ra1]))
                        self.ab2 = np.append(self.ab2, np.array([self.ra2]))
                        self.a = 0
                        self.sv()
                        if self.ser1.isOpen() == True:
                            self.plotgraph()
                        print(1.3)
                    elif len(self.col1_1) == self.T or len(self.col1_1) < int(self.LineEdit4.text()) - 1:
                        self.col1_1 = np.vstack((self.col1_1, self.data1))
                        self.col1_2 = np.vstack((self.col1_2, self.data2))
                        self.col2_1 = np.vstack((self.col2_1, self.calfft_1))
                        self.col2_2 = np.vstack((self.col2_2, self.calfft_2))
                        self.col3_1 = np.append(self.col3_1, np.array([self.ratio_1]))
                        self.col3_2 = np.append(self.col3_2, np.array([self.ratio_2]))
                        self.ab1 = np.append(self.ab1, np.array([self.ra1]))
                        self.ab2 = np.append(self.ab2, np.array([self.ra2]))
                        print(1.4)
                elif int(self.LineEdit4.text()) == 1 and self.a % self.sampling == 0:
                    self.col1_1 = np.vstack((self.col1_1, self.data1))
                    self.col1_2 = np.vstack((self.col1_2, self.data2))
                    self.col2_1 = np.vstack((self.col2_1, self.calfft_1))
                    self.col2_2 = np.vstack((self.col2_2, self.calfft_2))
                    self.col3_1 = np.append(self.col3_1, np.array([self.ratio_1]))
                    self.col3_2 = np.append(self.col3_2, np.array([self.ratio_2]))
                    self.ab1 = np.append(self.ab1, np.array([self.ra1]))
                    self.ab2 = np.append(self.ab2, np.array([self.ra2]))
                    self.l4.setText('Already Collect')
                    self.a = 0
                    self.sv()
                    if self.ser1.isOpen() == True:
                        self.plotgraph()
                    print(2)
            self.ii += self.T
            if self.ser1.isOpen() ==True and self.ready1 == True:
                self.plotgraph()
            elif self.ser1.isOpen() == False:
                self.state = False
                self.plotgraph()
                self.reply.setText('Please Connect with Aduino(%s)'%self.LineEdit3)
                self.reply.setWindowTitle('Caution')
                self.reply.exec_()
                print("Keyboard Interrupt")

    def stop(self):
        self.state = False
        self.plotgraph()
        self.Label7.setText('Stop')
        self.start_btn.setEnabled(True)
        self.clr_btn.setEnabled(True)
        self.LineEdit3.setEnabled(True)
        self.LineEdit4.setEnabled(True)
        self.cali_btn.setEnabled(False)


    def clear(self):
        if self.state == False:
            print('hello1')
            self.LineEdit3.setText('3')
            self.LineEdit4.setText('2')
            self.p1_1.clear()
            self.p1_2.clear()
            if self.chkbox1.isChecked() == True:
                self.p2_1.clear()
                self.p3_1.clear()
                self.chkbox1.setChecked(False)
            if self.chkbox2.isChecked() == True:
                self.p2_2.clear()
                self.p3_2.clear()
                self.chkbox2.setChecked(False)
            if self.filter.isChecked() == True:
                self.filter.setChecked(False)
            self.revalue()
            self.data1 = np.zeros(self.T)
            self.data2 = np.zeros(self.T)
            self.storeY1 = np.zeros(10)
            self.storeY2 = np.zeros(10)
            self.chkbox1.setChecked(False)
            self.chkbox2.setChecked(False)
            self.start_btn.setEnabled(True)
            self.collectflag = False
            self.LineEdit3.setText('3')
            self.LineEdit4.setText('2')
            self.Label3.setText('Number of Collections:')
            self.Label4.setText('Time of Collections:')
            self.Label5.setText('Collection State: 0')
            self.Label6.setText('Second pass: %s' % (self.a//self.sampling,))
            self.Label7.setText('Clear All')
        elif self.state == True:
            self.Label7.setText('Please Stop First')

    def collect(self):
        self.col1_1 = np.array([])
        self.col1_2 = np.array([])
        self.col2_1 = np.array([])
        self.col2_2 = np.array([])
        self.col3_1 = np.array([])
        self.col3_2 = np.array([])
        self.ab1 = np.array([])
        self.ab2 = np.array([])
        self.col_btn.setEnabled(False)
        self.coltime += 1
        self.Label5.setText('Collection State: %s' % (self.coltime,))
        self.collectflag = True

    def sv(self):
        self.c += 1
        self.filename = ['TDM_%s' % (self.c,), 'FFT_%s' % (self.c,),'Ratio_%s' % (self.c,)]
        # print(len(self.filename))
        with open('%s.csv' % (self.filename[0]), mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file, dialect='excel')
            writer.writerow(['CH1'])
            for i in range(len(self.col1_1)):
                writer.writerow(self.col1_1[i])
            writer.writerow(['CH2'])
            for j in range(len(self.col1_2)):
                writer.writerow(self.col1_2[j])
            print('%s.csv' % (self.filename[0]))
        with open('%s.csv' % (self.filename[1]), mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file, dialect='excel')
            writer.writerow(self.xd2)
            writer.writerow(['CH1'])
            for i in range(len(self.col2_1)):
                writer.writerow(self.col2_1[i])
            writer.writerow(['CH2'])
            for j in range(len(self.col2_2)):
                writer.writerow(self.col2_2[j])
            print('%s.csv' % (self.filename[1]))
        with open('%s.csv' % (self.filename[2]), mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file, dialect='excel')
            writer.writerow(['CH1'])
            writer.writerow(self.col3_1)
            writer.writerow(self.ab1)
            writer.writerow(['CH2'])
            writer.writerow(self.col3_2)
            writer.writerow(self.ab2)
            print('%s.csv' % (self.filename[2]))
        print('already save')


    def connect1(self):
        try:
            self.ser1 = serial.Serial(self.LineEdit1.text(), 115200, bytesize=serial.EIGHTBITS, timeout=None)
            time.sleep(2)
            self.con_btn1.setEnabled(False)
            self.LineEdit1.setEnabled(False)
            self.start_btn.setEnabled(True)
            self.chkbox2.setEnabled(True)
            self.chkbox1.setEnabled(True)
            self.Label1.setText('State: Already Connect')
            self.flag_con1 = True
            self.LineEdit1.setEnabled(False)
        except:
            self.Label1.setText('State: Disconnect')
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.com_btn.setEnabled(False)
            self.col_btn.setEnabled(False)
            self.clr_btn.setEnabled(False)
            self.chkbox2.setEnabled(False)
            self.chkbox1.setEnabled(False)
            self.LineEdit1.setEnabled(True)

    def connect2(self):
        try:
            self.ser2 = serial.Serial(self.LineEdit2.text(), 115200, bytesize=serial.EIGHTBITS, timeout=None)
            time.sleep(2)
            self.con_btn2.setEnabled(False)
            self.LineEdit2.setEnabled(False)
            self.com_btn.setEnabled(True)
            self.force_btn.setEnabled(True)
            self.Label2.setText('State: Already Connect')
            self.flag_con2 = True
            self.LineEdit2.setEnabled(False)
            self.comflag = 1
            self.forceflag = 1

        except:
            self.Label2.setText('State: Disconnect')
            self.com_btn.setEnabled(False)
            self.LineEdit2.setEnabled(True)

    def command(self):
        if self.comflag == 1:
            self.ready2 = True
            self.force_btn.setEnabled(False)
            self.comflag = 0
            self.Label7.setText('Open')
            if self.force_btn.isChecked() == True:
                self.force_btn.setChecked(False)
                self.forceflag = 1

        else:
            self.ready2 = False
            self.force_btn.setEnabled(True)
            self.com_btn.setChecked(False)
            self.comflag = 1
            self.Label7.setText('Close')

    def force(self):
        if self.forceflag == 1:
            self.ser2.write(bytes('1', 'utf-8'))
            self.Label7.setText('Forced')
            self.forceflag = 0
            self.com_btn.setEnabled(False)
            if self.com_btn.isChecked() == True:
                self.com_btn.setChecked(False)
                self.comflag = 1
        else:
            self.ser2.write(bytes('2', 'utf-8'))
            self.Label7.setText('Unforced')
            self.forceflag = 1
            self.com_btn.setEnabled(True)
            self.force_btn.setChecked(False)

    def revalue(self):
        self.calitime = 1
        self.c = 0
        self.state = False
        self.a = 0
        self.b = 0
        self.bb = 0
        self.i = 0
        self.ii = 0
        self.count = 0
        self.count2 = 1
        self.ptr = 0
        self.coltime = 0
        self.sampling = 250
        self.previous = 0
        self.counter = 0

    def calibrate(self):
        if self.calitime == 1:
            self.k = 0
        elif self.calitime == 2:
            self.j = 0
        self.clock = self.timer
        if self.com_btn.isChecked() == True:
            self.com_btn.setChecked(False)
        self.com_btn.setEnabled(False)
        self.Label7.setStyleSheet('QLabel{font-size:10px}')
        self.Label7.setText('Calibrate')
        self.califlag = True
# finish programme

app = QApplication(sys.argv)
a_window = window()
sys.exit(app.exec_())
