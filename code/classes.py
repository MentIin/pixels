import numpy as np
import os
from PIL import Image

from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QTimer

PEN = 1
ERASER = 2
PIPETTE = 3


def fileToPixels(path):
    path = path[0][0]
    path, file_name = '/'.join(path.split('/')[:-1]), path.split('/')[-1]
    os.chdir(path)
    f = open(file_name, 'r')

    size, array = f.read().split('/')
    width, height = size.split(';')
    width, height = int(width), int(height)
    array = array.split(';')

    pixels = np.zeros((width, height), dtype=Pixel)
    n = 0
    for x in range(width):
        for y in range(height):
            p = array[n]
            if p != "None":
                col = eval(p)
                col = QColor(*col)
                pixels[x, y] = Pixel(col)
            n += 1
    f.close()
    return pixels


def save(path, cpixels):
    path = path[0]
    path, file_name = '/'.join(path.split('/')[:-1]), path.split('/')[-1]
    os.chdir(path)
    width, height = cpixels.shape
    file = open(file_name, 'w')
    file_txt = f"{width};{height}/"
    for x in range(width):
        for y in range(height):
            p = cpixels[x, y]
            if p != 0:
                file_txt = file_txt + str(p.color.getRgb())
            else:
                file_txt = file_txt + 'None'
            file_txt = file_txt + ';'
    file.write(file_txt)
    file.close()


def export(path, cpixels):
    path = path[0]
    path, file_name = '/'.join(path.split('/')[:-1]), path.split('/')[-1]

    os.chdir(path)
    width, height = cpixels.shape

    im = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    rpixels = im.load()
    for x in range(width):
        for y in range(height):
            p = cpixels[x, y]
            if p == 0:
                rpixels[x, y] = (0, 0, 0, 0)
            else:
                rpixels[x, y] = p.color.getRgb()
    im.save(file_name, "png", quality=100)


class Pixel:
    def __init__(self, color):
        self.color = color

    def getColor(self):
        return self.color

    def __repr__(self):
        return str(1)


class Canvas(QLabel):
    def __init__(self, form, weight, height):
        super().__init__(form)

        self.pixels = np.zeros((weight, height), dtype=Pixel)  # создание массива пикселей

        self.setScale(10)  # масштаб

        self.tool = PEN
        self.grid_on = True
        self.grid_color = Qt.black
        self.cursor = False
        self.mouse_pressed = False
        self.cursor_x = 0
        self.cursor_y = 0
        self.color = QColor(0, 0, 0, 255)

        self.setMouseTracking(True)

    def setPixels(self, array):
        self.pixels = array

    def setScale(self, k):
        # настройка размера холста
        w, h = self.pixels.shape
        w, h = w * k, h * k
        self.setGeometry(200, 5, w, h)

        self.pixel_size = min(self.geometry().width() / (self.pixels.shape[0]),
                              self.geometry().height() / (self.pixels.shape[1]))  # размер пикселя

        self.resize(self.width() + 1, self.height() + 1)  # нужно для корректного отображения сетки по краям

    def mousePressEvent(self, event) -> None:
        self.mouse_pressed = True
        self.useTool()

    def useTool(self):
        if self.tool == PEN:
            self.addPixel()
        elif self.tool == ERASER:
            self.removePixel()
        elif self.tool == PIPETTE:
            self.choiceColorFromPixels()

    def mouseReleaseEvent(self, event) -> None:
        self.mouse_pressed = False

    def mouseMoveEvent(self, event) -> None:
        if event.x() < 0 or event.y() < 0:
            return
        self.cursor_x = event.x()
        self.cursor_y = event.y()

        if self.mouse_pressed:
            self.useTool()
        QTimer.singleShot(20, self.checkMouse)

    def checkMouse(self):
        if self.underMouse():
            self.cursor = True
        else:
            self.cursor = False
        self.repaint()

    def paintEvent(self, event) -> None:
        qp = QPainter()
        qp.begin(self)

        self.drawPixels(qp)
        if self.grid_on:
            self.drawGrid(qp)
        if self.cursor:
            self.drawCursor(qp)
        qp.end()

    def drawCursor(self, qp):
        if self.tool == PEN:
            qp.setBrush(self.color)
        else:
            qp.setBrush(Qt.NoBrush)
        pen = QPen(Qt.black, 3)
        qp.setPen(pen)

        x, y = self.choisedPixelCoords()
        x, y = int(x * self.pixel_size), int(y * self.pixel_size)

        qp.drawRect(x, y, self.pixel_size, self.pixel_size)

    def drawPixels(self, qp):
        weight, height = self.pixels.shape

        qp.setPen(Qt.NoPen)  # удаление обводки у пикселей

        for x in range(weight):
            for y in range(height):
                if self.pixels[x, y] == 0:  # если ячейку не использовали при рисовании
                    qp.setBrush(QColor(255, 255, 255, 255))  # рисуется бело серая сетка
                    coords = (x * self.pixel_size, y * self.pixel_size)
                    size = (self.pixel_size, self.pixel_size)
                    qp.drawRect(*coords, *size)

                    qp.setBrush(Qt.lightGray)
                    half_size = self.pixel_size / 2
                    size = (half_size, half_size)
                    coords = (x * self.pixel_size, y * self.pixel_size)
                    qp.drawRect(*coords, *size)
                    coords = (x * self.pixel_size + half_size, y * self.pixel_size + half_size)
                    qp.drawRect(*coords, *size)
                else:
                    qp.setBrush(self.pixels[x, y].getColor())
                    coords = (x * self.pixel_size, y * self.pixel_size)
                    size = (self.pixel_size, self.pixel_size)
                    qp.drawRect(*coords, *size)

    def addPixel(self):
        x, y = self.choisedPixelCoords()
        try:
            self.pixels[x, y] = Pixel(self.color)
            self.repaint()
        except IndexError:  # если зажать мышь и увести с холста  будут
            pass  # попытки добавить пиксель за пределом холста

    def removePixel(self):
        x, y = self.choisedPixelCoords()
        try:
            self.pixels[x, y] = 0
            self.repaint()
        except IndexError:  # если зажать мышь и увести с холста  будут
            pass  # попытки добавить пиксель за пределом холста

    def choiceColorFromPixels(self):
        x, y = self.choisedPixelCoords()
        if self.pixels[x, y] != 0:
            col = self.pixels[x, y].color
            self.color = QColor(col.name())

    def drawGrid(self, qp):
        weight, height = self.pixels.shape

        qp.setBrush(Qt.NoBrush)
        pen = QPen(self.grid_color, 1)
        qp.setPen(pen)

        for x in range(weight):
            for y in range(height):
                coords = (x * self.pixel_size, y * self.pixel_size)
                size = (self.pixel_size, self.pixel_size)
                qp.drawRect(*coords, *size)

    def choisedPixelCoords(self):
        x, y = int(self.cursor_x / self.pixel_size), int(self.cursor_y / self.pixel_size)
        return x, y

    def __repr__(self):
        return str(self.pixels)
