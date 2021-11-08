import sys

from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QColorDialog, QFileDialog

from form import Ui_EditWindow, Ui_dialog
from classes import Canvas, export, save, fileToPixels, PEN, ERASER, PIPETTE
from PyQt5.QtCore import Qt

MIN_SCALE = 10


class CreateProjectDialog(QDialog, Ui_dialog):  # окно создания или открытия проекта
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.btn_create.clicked.connect(self.createEmptyProject)
        self.btn_open.clicked.connect(self.open)

    def createEmptyProject(self):
        global ex
        width, height = self.getSize()
        if width == 0 or height == 0:
            pass
        else:
            ex = EditWindow(width, height)
            ex.show()
            self.hide()

    def getSize(self):  # возвращает кортеж размеров окна в соответсвии с размером холста
        return (self.widthEdit.value(), self.heightEdit.value())

    def open(self):
        global ex
        path = QFileDialog.getOpenFileNames(self, "Select file",
                                            '', 'Проект (*.pixels)')
        pixels = fileToPixels(path)
        width, height = pixels.shape
        ex = EditWindow(width, height)
        ex.canvas.setPixels(pixels)
        ex.show()
        self.hide()


class EditWindow(QMainWindow, Ui_EditWindow):
    def __init__(self, weight, height):  # ширина и высота изображения в пикселах
        super().__init__()
        self.setupUi(self)

        self.canvas = Canvas(self, weight, height)

        self.setSize()

        self.btn_colorChange.clicked.connect(self.choiceColor)
        self.slider_scaleEdit.valueChanged.connect(self.setCanvasScale)
        self.btn_turnGrid.clicked.connect(self.turnGrid)
        self.btn_gridColorChange.clicked.connect(self.changeGridColor)
        self.toolsButtons.buttonClicked.connect(self.changeTool)
        self.btn_export.clicked.connect(self.export)
        self.btn_save.clicked.connect(self.save)
        self.pushButton.clicked.connect(self.newProject)

    def paintEvent(self, event) -> None:
        self.btn_colorChange.setStyleSheet(f"background-color: {self.canvas.color.name()}")

    def setCanvasScale(self):
        self.canvas.setScale(self.slider_scaleEdit.value() + MIN_SCALE)

    def wheelEvent(self, event):
        delta = int(event.angleDelta().y())
        if delta > 0:
            self.slider_scaleEdit.setValue(self.slider_scaleEdit.value() + 1)
        if delta < 0:
            self.slider_scaleEdit.setValue(self.slider_scaleEdit.value() - 1)

    def choiceColor(self):
        col = QColorDialog.getColor()
        if col.isValid():
            self.canvas.color = QColor(col.name())

    def setSize(self):
        width = self.canvas.geometry().width() + 200
        height = self.canvas.geometry().height()

        self.resize(width, height)

    def turnGrid(self):
        self.canvas.grid_on = not self.canvas.grid_on
        self.canvas.repaint()

    def changeGridColor(self):
        col = QColorDialog.getColor()
        if col.isValid():
            self.btn_gridColorChange.setStyleSheet(f"background-color: {col.name()}")
            self.canvas.grid_color = QColor(col.name())

    def changeTool(self):
        select = self.toolsButtons.checkedButton()

        if select == self.btn_pen:
            self.canvas.tool = PEN
        elif select == self.btn_eraser:
            self.canvas.tool = ERASER
        elif select == self.btn_pipette:
            self.canvas.tool = PIPETTE

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_1:
            self.btn_pen.setChecked(True)
            self.changeTool()
        elif event.key() == Qt.Key_2:
            self.btn_eraser.setChecked(True)
            self.changeTool()
        elif event.key() == Qt.Key_3:
            self.btn_pipette.setChecked(True)
            self.changeTool()
        elif event.key() == Qt.Key_Q:
            self.choiceColor()
        self.canvas.repaint()

    def export(self):
        path = QFileDialog.getSaveFileName(self, "Select output folder",
                                           'C:', 'Картинка (*.png)')
        export(path, self.canvas.pixels)

    def save(self):
        path = QFileDialog.getSaveFileName(self, "Select output folder",
                                           'C:', 'Проект (*.pixels)')
        save(path, self.canvas.pixels)

    def open(self):  # сейчас не нужен
        path = QFileDialog.getOpenFileNames(self, "Select file",
                                            '', 'Проект (*.pixels)')
        new_pixels = fileToPixels(path)
        self.canvas.setPixels(new_pixels)
        self.canvas.setScale(10)

    def newProject(self):
        global dial
        dial = CreateProjectDialog()  # создание проекта
        dial.show()
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    ex = None

    dial = CreateProjectDialog()  # создание проекта
    dial.show()

    sys.exit(app.exec())
