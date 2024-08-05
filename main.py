from PyQt6.QtWidgets import QWidget, QApplication, QComboBox, QPushButton, QSplashScreen, QLabel, QLineEdit
from PyQt6.QtGui import QIcon, QGuiApplication, QMouseEvent, QMovie
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6 import uic
import sys
import serial
import cv2
import time


class LoadingScreen(QSplashScreen):
    def __init__(self):
        super(QSplashScreen, self).__init__()
        self.progressBar = None
        uic.loadUi('LoadingScreen.ui', self)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def progress(self):
        for i in range(100):
            time.sleep(0.05)
            self.progressBar.setValue(i)


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()
        self.exit_pushButton = None
        self.ser = None
        uic.loadUi("Gui.ui", self)
        self.setWindowTitle("Robotic Arm GUI")
        self.setWindowIcon(QIcon("Design_Images/Icon.png"))
        self.setFixedWidth(850)
        self.setFixedHeight(640)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.offset = QPoint()  # Track the offset between the mouse click position and window position

        # Initialize the widgets
        self.Error_lineEdit = self.findChild(QLineEdit, "Error_lineEdit")
        self.Error_lineEdit_2 = self.findChild(QLineEdit, "Error_lineEdit_2")
        self.baud_comboBox = self.findChild(QComboBox, "baud_comboBox")
        self.com_comboBox = self.findChild(QComboBox, "com_comboBox")
        self.connect_pushButton = self.findChild(QPushButton, "connect_pushButton")
        self.webcam_pushButton = self.findChild(QPushButton, "webcam_pushButton")
        self.exit_pushButton = self.findChild(QPushButton, "exit_pushButton")

        # Set image to exit button
        exit_button_icon = QIcon("Design_Images/exit_icon.png")
        self.exit_pushButton.setIcon(exit_button_icon)

        # Add status_show QLabel
        self.status_show = QLabel(self)
        self.status_show.setGeometry(71, 123, 71, 20)
        self.status_show.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_show.setStyleSheet("QLabel { color: red; font: 600 11pt Segoe UI;}")
        self.status_show.setText("Inactive")

        # Connect the signals
        self.connect_pushButton.clicked.connect(self.toggle_connection)
        self.webcam_pushButton.clicked.connect(self.toggle_webcam)
        self.exit_pushButton.clicked.connect(lambda: app.exit())

        # Initialize a QLabel for displaying the GIF
        self.gif_label = QLabel(self)
        self.gif_label.setGeometry(0, 0, 850, 640)
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gif_label.hide()  # Hide initially

    def mousePressEvent(self, event: QMouseEvent):
        self.offset = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)

    def toggle_connection(self):
        if not hasattr(self, 'ser') or self.ser is None or not self.ser.is_open:
            self.connect_arduino()
        else:
            self.disconnect_arduino()

    def connect_arduino(self):
        com = self.com_comboBox.currentText()
        baud = self.baud_comboBox.currentText()
        try:
            self.ser = serial.Serial(com, baud, timeout=1)
            print(f"Connected to Arduino on {com} with baud rate {baud}")
            self.connect_pushButton.setText("Disconnect")
            self.status_show.setText("Active")
            self.status_show.setStyleSheet("QLabel { color: #18f02a; font: 600 11pt Segoe UI;}")
            self.Error_lineEdit.clear()  # Clear the error message
        except serial.SerialException as e:
            print(f"Error: {e}")
            self.Error_lineEdit.setText("Error: Arduino not connected")
            self.Error_lineEdit.setStyleSheet("color: red; font: 650 12px; border: none; background: transparent;")
            self.connect_pushButton.setText("Connect")
            if hasattr(self, 'ser') and self.ser is not None and self.ser.is_open:
                self.ser.close()
                self.status_show.setText("Inactive")
                self.status_show.setStyleSheet("QLabel { color: red; font: 600 11pt Segoe UI;}")

    def disconnect_arduino(self):
        if hasattr(self, 'ser') and self.ser is not None and self.ser.is_open:
            self.ser.close()
            print("Disconnected from Arduino")
            self.connect_pushButton.setText("Connect")
            self.status_show.setText("Inactive")
            self.status_show.setStyleSheet("QLabel { color: red; font: 600 11pt Segoe UI;}")

    def toggle_webcam(self):
        if hasattr(self, 'ser') and self.ser is not None and self.ser.is_open:
            self.Error_lineEdit_2.clear()  # Clear the error message
            print("Opening Webcam")

            # Show the GIF
            movie = QMovie("Design_Images/tech-gif-unscreen.gif")
            self.gif_label.setMovie(movie)
            movie.setSpeed(200)
            movie.start()
            self.gif_label.show()

            # Schedule hiding of GIF after 2.55 seconds
            QTimer.singleShot(2550, self.hide_gif_and_open_webcam)
        else:
            print("Arduino not connected. Cannot open webcam.")
            self.Error_lineEdit_2.setText(f"Webcam cannot open until Arduino is connected")
            self.Error_lineEdit_2.setStyleSheet("color: red; font: 650 12px; border: none; background: transparent;")

    @staticmethod
    def calculate_bbox_properties(x, y, w, h):
        length = w
        width = h
        area = length * width
        return length, width, area

    def detect_faces(self, frame):
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
        for (x, y, w, h) in faces:
            length, width, area = self.calculate_bbox_properties(x, y, w, h)
            print(f'Bounding Box Properties: Length={length}, Width={width}, Area={area}')
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            center_x = x + w // 2
            center_y = y + h // 2
            cv2.circle(frame, (center_x, center_y), radius=5, color=(0, 0, 255), thickness=-1)
            cv2.putText(frame, f'Face: ({center_x}, {center_y})', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 125, 125), 2)
        return frame

    def hide_gif_and_open_webcam(self):
        # Hide the GIF
        self.gif_label.hide()

        width = 680
        height = 480
        cam = cv2.VideoCapture(0)
        cam.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cam.set(cv2.CAP_PROP_FPS, 30)
        while True:
            _, frame = cam.read()
            frame = self.detect_faces(frame)
            cv2.putText(frame, f'Press ESC to Exit', (10, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 0, 255), 2)
            cv2.imshow('My Webcam', frame)
            cv2.moveWindow('My Webcam', 470, 190)
            if cv2.waitKey(1) & 0xFF == 27:  # Press 'Esc' to exit
                break
        cam.release()
        cv2.destroyAllWindows()

    def setText(self, param):
        pass

    def clear(self):
        pass

    def setIconSize(self, param):
        pass

    def setIcon(self, exit_button_icon):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = LoadingScreen()
    splash.show()
    splash.progress()
    window = Window()
    window.show()
    splash.finish(window)
    sys.exit(app.exec())
