
import json
import ollama
import rawpy
import subprocess
import sys
import numpy as np
from PIL import Image
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QLineEdit, QTextEdit


class ImageUploader(QWidget):
    def __init__(self):
        super().__init__()

        self.metadata = None
        self.raw = None
        self.rgb_image = None
        self.pixel_data = ""

        self.setWindowTitle("Image Upload Chatbot")
        self.setGeometry(100, 100, 300, 200)

        layout = QVBoxLayout()
        label = QLabel("Upload an image to analyze its metadata.")
        layout.addWidget(label)

        self.image_label = QLabel(self)
        self.image_label.setFixedSize(100,100)
        self.image_label.setStyleSheet("border: 0.5px solid black;")
        layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        
        self.upload_button = QPushButton("upload image")
        self.upload_button.clicked.connect(self.upload_image)
        layout.addWidget(self.upload_button)

        self.response_label = QTextEdit()
        self.response_label.setFixedHeight(250)
        self.response_label.setPlaceholderText("Ollama Response.")
        self.response_label.setReadOnly(True)
        layout.addWidget(self.response_label)

        self.setLayout(layout)
        
        self.question_input = QTextEdit()
        self.question_input.setPlaceholderText("Ask questions about uploaded raw image.")
        layout.addWidget(self.question_input)
        
        self.ask_ollama = QPushButton("Ask")
        self.ask_ollama.clicked.connect(self.ask_ollama_question)
        layout.addWidget(self.ask_ollama)

    def upload_image(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images(*.png *.jpg *.jpeg *.gif *.cr2 *.nef *.arw *.dng *.orf *.raf *.rw2 *.srw *.pef *.crw *.3fr *.fff *.iiq *.mef *.mos *.nrw *.sr2);;All Files (*)", options=options)
        if file_path:
            try:
                self.raw = rawpy.imread(file_path)
                self.rgb_image = self.raw.postprocess()
                if np.any(np.isnan(self.rgb_image)) or np.any(np.isinf(self.rgb_image)):
                    self.pixel_data = "Corrupt"
                else:
                    self.pixel_data = "Not Corrupt"
            except Exception as err:
                self.pixel_data = "Unkown"

            self.display_image()
            self.analyze_image(file_path)
                
            
    def display_image(self):
        try:
            height, width, _ =  self.rgb_image.shape
            q_image = QImage(self.rgb_image.data, width, height, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            self.image_label.setPixmap(pixmap.scaled(100, 100))
        except Exception as err:
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("Image Uploaded")
    
    def analyze_image(self, file_path):
        self.metadata = self.get_cr2_metadata(file_path)
        print("self.metadata",self.metadata)
        if self.metadata:
            self.response_label.setPlainText("Image uploaded successfully.")

    def get_cr2_metadata(self, file_path):
        result = subprocess.run(['exiftool', '-j', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print("Error reading metadata")
            return None
        metadata_json = result.stdout.decode()
        metadata = json.loads(metadata_json)
        return metadata[0]

    def ask_ollama_question(self):
        text = self.question_input.toPlainText()
        if text.strip():
            prompt = f"Based on the following image metadata: {json.dumps(self.metadata)}, answer this question: {text}, Pixel data of this image is {self.pixel_data}"
            response = ollama.generate(model='llava', prompt=prompt)
            self.response_label.setPlainText(f"Query:{text}\n")
            self.response_label.append(response.get('response', 'No response received from Ollama.'))
            self.question_input.clear()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageUploader()
    window.show()
    sys.exit(app.exec())