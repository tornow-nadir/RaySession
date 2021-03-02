# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'resources/ui/client_trash.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(333, 311)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.toolButtonIcon = FakeToolButton(Dialog)
        self.toolButtonIcon.setStyleSheet("QToolButton{border:none}")
        icon = QtGui.QIcon.fromTheme("application-pdf")
        self.toolButtonIcon.setIcon(icon)
        self.toolButtonIcon.setIconSize(QtCore.QSize(64, 64))
        self.toolButtonIcon.setObjectName("toolButtonIcon")
        self.horizontalLayout_2.addWidget(self.toolButtonIcon)
        self.labelPrettierName = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.labelPrettierName.setFont(font)
        self.labelPrettierName.setObjectName("labelPrettierName")
        self.horizontalLayout_2.addWidget(self.labelPrettierName)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.labelDescription = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setItalic(True)
        self.labelDescription.setFont(font)
        self.labelDescription.setObjectName("labelDescription")
        self.verticalLayout.addWidget(self.labelDescription)
        self.line = QtWidgets.QFrame(Dialog)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout.addWidget(self.line)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label_3 = QtWidgets.QLabel(Dialog)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 1)
        self.label_4 = QtWidgets.QLabel(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_4.sizePolicy().hasHeightForWidth())
        self.label_4.setSizePolicy(sizePolicy)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 1, 0, 1, 1)
        self.label_7 = QtWidgets.QLabel(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_7.sizePolicy().hasHeightForWidth())
        self.label_7.setSizePolicy(sizePolicy)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 0, 1, 1, 1)
        self.label_5 = QtWidgets.QLabel(Dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 1, 1, 1, 1)
        self.labelId = QtWidgets.QLabel(Dialog)
        self.labelId.setObjectName("labelId")
        self.gridLayout.addWidget(self.labelId, 0, 2, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 3, 1, 1)
        self.labelExecutable = QtWidgets.QLabel(Dialog)
        self.labelExecutable.setObjectName("labelExecutable")
        self.gridLayout.addWidget(self.labelExecutable, 1, 2, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem1)
        self.toolButtonAdvanced = QtWidgets.QToolButton(Dialog)
        icon = QtGui.QIcon.fromTheme("dialog-information")
        self.toolButtonAdvanced.setIcon(icon)
        self.toolButtonAdvanced.setObjectName("toolButtonAdvanced")
        self.horizontalLayout_3.addWidget(self.toolButtonAdvanced)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.line_2 = QtWidgets.QFrame(Dialog)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.verticalLayout.addWidget(self.line_2)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem2)
        self.label_11 = QtWidgets.QLabel(Dialog)
        self.label_11.setObjectName("label_11")
        self.verticalLayout.addWidget(self.label_11)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem3)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButtonRemove = QtWidgets.QPushButton(Dialog)
        icon = QtGui.QIcon.fromTheme("draw-eraser-delete-objects")
        self.pushButtonRemove.setIcon(icon)
        self.pushButtonRemove.setObjectName("pushButtonRemove")
        self.horizontalLayout.addWidget(self.pushButtonRemove)
        self.pushButtonRestore = QtWidgets.QPushButton(Dialog)
        icon = QtGui.QIcon.fromTheme("restoration")
        self.pushButtonRestore.setIcon(icon)
        self.pushButtonRestore.setObjectName("pushButtonRestore")
        self.horizontalLayout.addWidget(self.pushButtonRestore)
        self.pushButtonCancel = QtWidgets.QPushButton(Dialog)
        icon = QtGui.QIcon.fromTheme("dialog-cancel")
        self.pushButtonCancel.setIcon(icon)
        self.pushButtonCancel.setObjectName("pushButtonCancel")
        self.horizontalLayout.addWidget(self.pushButtonCancel)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(Dialog)
        self.pushButtonCancel.clicked.connect(Dialog.reject)
        self.pushButtonRestore.clicked.connect(Dialog.accept)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Trashed client"))
        self.toolButtonIcon.setText(_translate("Dialog", "..."))
        self.labelPrettierName.setText(_translate("Dialog", "Prettier Name"))
        self.labelDescription.setText(_translate("Dialog", "Description"))
        self.label_3.setText(_translate("Dialog", "Client id"))
        self.label_4.setText(_translate("Dialog", "Executable"))
        self.label_7.setText(_translate("Dialog", ":"))
        self.label_5.setText(_translate("Dialog", ":"))
        self.labelId.setText(_translate("Dialog", "nsmid"))
        self.labelExecutable.setText(_translate("Dialog", "executable"))
        self.toolButtonAdvanced.setToolTip(_translate("Dialog", "<html><head/><body><p>Get more informations on this trashed client.</p></body></html>"))
        self.toolButtonAdvanced.setText(_translate("Dialog", "..."))
        self.label_11.setText(_translate("Dialog", "<html><head/><body><p align=\"center\">Do you want to restore this client in the session ?<br/>You can also definitely remove the client and its files.</p></body></html>"))
        self.pushButtonRemove.setToolTip(_translate("Dialog", "<html><head/><body><p>Remove definitely the client and its files.</p></body></html>"))
        self.pushButtonRemove.setText(_translate("Dialog", "Remove"))
        self.pushButtonRestore.setToolTip(_translate("Dialog", "<html><head/><body><p>Restore this client in current session.</p></body></html>"))
        self.pushButtonRestore.setText(_translate("Dialog", "Restore Client"))
        self.pushButtonCancel.setText(_translate("Dialog", "Cancel"))

from surclassed_widgets import FakeToolButton