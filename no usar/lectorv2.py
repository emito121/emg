import numpy as np
import pandas as pd
import time
from scipy.signal import butter, filtfilt, iirnotch
from PyQt5.QtWidgets import QDialog, QGraphicsScene, QApplication
from PyQt5.QtGui import QFont, QKeyEvent
import pyqtgraph as pg
from PyQt5.QtCore import QTimer
from PyQt5 import uic
import os
import glob

class EMGControlSystem(QDialog):
    def __init__(self, emg_channel, t_length=10, directorio='ruta_al_archivo.csv', fs=250):
        super().__init__()

        self.emg_channel = emg_channel
        self.t_length = t_length
        self.fs = fs
        self.directorio = directorio

        # Crear el búfer de datos
        self.data_buffer = np.zeros(int(self.fs * self.t_length))
        self.last_row_read = 0  # Última fila procesada
        self.find_latest_file("*.csv")
        uic.loadUi('interfaz.ui', self)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.mean = QTimer()
        self.mean.timeout.connect(self.mean_emg)
        self._init_ui()
        self.show()
        self.timer.start(30)  # Frecuencia de actualización
        self.mean.start(1000)

    def find_latest_file(self, pattern="*"):
            files = glob.glob(os.path.join(self.directorio, pattern))
            if not files:
                return None
            latest_file = max(files, key=os.path.getmtime)
            self.path = latest_file

    def _init_ui(self):
        scene = QGraphicsScene()
        self.graphicsView.setScene(scene)
        self.graphics_window = pg.GraphicsLayoutWidget(title='EMG Plot', size=(950, 390))
        self.graphics_window.setBackground('w')
        scene.addWidget(self.graphics_window)
        self._init_timeseries()

    def _init_timeseries(self):
        self.plot = self.graphics_window.addPlot(row=0, col=0)
        self.plot.showAxis('left', True)
        self.plot.setMenuEnabled('left', True)
        self.plot.showGrid(x=True, y=True)

        ax0 = self.plot.getAxis('left')
        ax0.setStyle(showValues=True)
        ax0.setLabel(f"Canal {self.emg_channel}", color='r', size='14pt', bold=True)
        self.plot.setYRange(-1000, 1000)
        self.plot.setXRange(0, self.fs * self.t_length)

        ax1 = self.plot.getAxis('bottom')
        ax1.setStyle(showValues=True)
        ax1.setTickFont(QFont('Arial', 8))
        ax1.setRange(0, self.t_length)

        self.plot.showAxis('top', False)
        self.plot.showAxis('bottom', True)
        self.curve = self.plot.plot(pen='r', name=f'Canal {self.emg_channel}')

    def bandpass_filter(self, data, lowcut=5, highcut=120):
        nyquist = 0.5 * self.fs
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = butter(4, [low, high], btype="band")
        return filtfilt(b, a, data)

    def notch_filter(self, data, freq=50, quality=30):
        nyquist = 0.5 * self.fs
        notch_freq = freq / nyquist
        b, a = iirnotch(notch_freq, quality)
        return filtfilt(b, a, data)

    def update_plot(self):
        new_data = self.read_new_data()
        if new_data is not None:
            if len(new_data) > len(self.data_buffer):
                new_data = new_data[-len(self.data_buffer):]

            self.data_buffer = np.roll(self.data_buffer, -len(new_data))
            self.data_buffer[-len(new_data):] = new_data

            # Aplicar filtros pasa-banda y notch
            filtered_data = self.bandpass_filter(self.data_buffer)
            filtered_data = self.notch_filter(filtered_data)

            self.curve.setData(filtered_data)

    def mean_emg(self,):
        try:
            data = self.data_buffer[-int(self.fs)*3:]
            filtered_data = self.bandpass_filter(data)
            filtered_data = self.notch_filter(filtered_data)
            average_value = np.mean(filtered_data)
            print(average_value)
        except:
            pass

    def read_new_data(self):
        data = pd.read_csv(self.path, sep='\t', header=None)
        total_rows = len(data)
        
        if total_rows > self.last_row_read:
            new_data = data.iloc[self.last_row_read:total_rows, self.emg_channel]
            self.last_row_read = total_rows
            return new_data.values
        return None

    def closeEvent(self, event):
        self.timer.stop()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == ord('Q'):
            self.close()

# Ejemplo de ejecución
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    file_path = "C:/Users/Usuario/Documents/OpenBCI_GUI/Recordings/OpenBCISession_2024-11-12_23-09-40/"
    emg_system = EMGControlSystem(emg_channel=3, t_length=2, directorio=file_path)
    sys.exit(app.exec_())