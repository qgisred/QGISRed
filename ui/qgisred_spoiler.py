# -*- coding: utf-8 -*-
from PyQt5.QtCore import pyqtSignal, QParallelAnimationGroup, QPropertyAnimation, Qt, QAbstractAnimation
from PyQt5.QtWidgets import QWidget, QScrollArea, QFrame, QToolButton, QGridLayout, QSizePolicy

class Spoiler(QWidget):
    toggledState = pyqtSignal(bool)

    def __init__(self, parent=None, title='', animationDuration=10):
        super(Spoiler, self).__init__(parent)
        self.animationDuration = animationDuration

        self.toggleAnimation = QParallelAnimationGroup()
        self.contentArea = QScrollArea()
        self.headerLine = QFrame()
        self.toggleButton = QToolButton()
        self.mainLayout = QGridLayout()

        self.toggleButton.setStyleSheet("QToolButton { border: none; font-weight: bold; font-size: 9pt; }")
        self.toggleButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggleButton.setArrowType(Qt.RightArrow)
        self.toggleButton.setText(title)
        self.toggleButton.setCheckable(True)
        self.toggleButton.setChecked(False)

        self.headerLine.setFrameShape(QFrame.HLine)
        self.headerLine.setFrameShadow(QFrame.Sunken)
        self.headerLine.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        self.contentArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.contentArea.setMaximumHeight(0)
        self.contentArea.setMinimumHeight(0)

        self.toggleAnimation.addAnimation(QPropertyAnimation(self, b"minimumHeight"))
        self.toggleAnimation.addAnimation(QPropertyAnimation(self, b"maximumHeight"))
        self.toggleAnimation.addAnimation(QPropertyAnimation(self.contentArea, b"maximumHeight"))

        self.toggleAnimation.finished.connect(self.onAnimationFinished)

        self.mainLayout.setVerticalSpacing(0)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        row = 0
        self.mainLayout.addWidget(self.toggleButton, row, 0, 1, 1, Qt.AlignLeft)
        self.mainLayout.addWidget(self.headerLine, row, 2, 1, 1)
        row += 1
        self.mainLayout.addWidget(self.contentArea, row, 0, 1, 3)
        self.setLayout(self.mainLayout)

        self.toggleButton.clicked.connect(self.startAnimation)

    def startAnimation(self, checked):
        arrow_type = Qt.DownArrow if checked else Qt.RightArrow
        self.toggleButton.setArrowType(arrow_type)
        direction = QAbstractAnimation.Forward if checked else QAbstractAnimation.Backward
        self.toggleAnimation.setDirection(direction)
        self.toggleAnimation.start()

    def onAnimationFinished(self):
        self.toggledState.emit(self.toggleButton.isChecked())

    def setContentLayout(self, contentLayout):
        self.contentArea.setLayout(contentLayout)
        collapsedHeight = self.sizeHint().height() - self.contentArea.maximumHeight()
        contentHeight = contentLayout.sizeHint().height()
        for i in range(self.toggleAnimation.animationCount()-1):
            anim = self.toggleAnimation.animationAt(i)
            anim.setDuration(self.animationDuration)
            anim.setStartValue(collapsedHeight)
            anim.setEndValue(collapsedHeight + contentHeight)
        contentAnimation = self.toggleAnimation.animationAt(self.toggleAnimation.animationCount()-1)
        contentAnimation.setDuration(self.animationDuration)
        contentAnimation.setStartValue(0)
        contentAnimation.setEndValue(contentHeight)

    def isExpanded(self):
        return self.toggleButton.isChecked()
    
    def setExpanded(self, expanded):
        if self.toggleButton.isChecked() == expanded:
            return
        self.toggleButton.setChecked(expanded)
        self.startAnimation(expanded)