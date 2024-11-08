import numpy as np
import serial
import time
from PyQt5.QtWidgets import QDialog, QGraphicsScene, QApplication
from PyQt5.QtGui import QFont, QKeyEvent
import pyqtgraph as pg
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from PyQt5.QtCore import QTimer
from scipy.signal import butter, filtfilt, iirnotch
from PyQt5 import uic

class EMGControlSystem(QDialog):
    def __init__(self, emg_channel, t_lenght=10, arduino_port='COM4', threshold_emg=100, placa=3, placa_port='COM6'):
        super().__init__()

        self.opciones_placas = {
            1: [BoardIds.CYTON_BOARD, 250],
            2: [BoardIds.GANGLION_BOARD, 200],
            3: [BoardIds.SYNTHETIC_BOARD, 200]
        }
        self.placa_port = placa_port
        self.board_type = self.opciones_placas.get(placa)[0]
        self.emg_channel = emg_channel
        self.t_lenght = t_lenght
        self.arduino_port = arduino_port
        self.threshold_emg = threshold_emg
        self.fs = self.opciones_placas.get(placa)[1]
        uic.loadUi('interfaz.ui', self)
        # Crear el temporizador de actualización
        self.timer = QTimer()
        self.timer_promedio = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer_promedio.timeout.connect(self.mean_emg)

        # Inicializar OpenBCI y la interfaz gráfica
        self.board = self._setup_board()
        self._init_ui()
        self.show()

    # Inicializar OpenBCI y Brainflow
    def _setup_board(self):
        
        params = BrainFlowInputParams()
        params.serial_port = self.placa_port
        board = BoardShim(self.board_type.value, params)
        board.prepare_session()
        board.start_stream()
        return board

    # Inicializar la interfaz gráfica usando pyqtgraph
    def _init_ui(self):
        scene = QGraphicsScene()
        self.graphicsView.setScene(scene)
        self.graphics_window = pg.GraphicsLayoutWidget(title='EMG Plot', size=(950, 390))
        self.graphics_window.setBackground('w')
        scene.addWidget(self.graphics_window)
        self._init_timeseries()

        # Iniciar el temporizador
        

    # Inicializar la gráfica de la serie temporal
    def _init_timeseries(self):
        self.plot = self.graphics_window.addPlot(row=0, col=0)
        self.plot.showAxis('left', True)
        self.plot.setMenuEnabled('left', True)
        self.plot.showGrid(x=True, y=True)

        ax0 = self.plot.getAxis('left')
        ax0.setStyle(showValues=True)
        ax0.setLabel(f"Canal {self.emg_channel}", color='r', size='14pt', bold=True)
        self.plot.setYRange(-1000, 1000)  # Rango fijo en el eje Y
        self.plot.setXRange(0,self.fs*self.t_lenght)
        ax1 = self.plot.getAxis('bottom')
        ax1.setStyle(showValues=True)
        ax1.setTickFont(QFont('Arial', 8))
        ax1.setRange(0, self.t_lenght)

        self.plot.showAxis('top', False)
        self.plot.showAxis('bottom', True)

        self.curve = self.plot.plot(pen='r', name=f'Canal {self.emg_channel}')

    # Función para aplicar un filtro pasa-banda a la señal EMG
    def _filter_emg_signal(self, emg_signal):
        lowcut = 30.0
        highcut = 90.0
        nyquist = 0.5 * self.fs
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = butter(2, [low, high], btype='band')
        filtered_signal = filtfilt(b, a, emg_signal)

        # Definir y aplicar el filtro notch en 50 Hz
        notch_freq = 50.0
        quality_factor = 30
        b_notch, a_notch = iirnotch(notch_freq / nyquist, quality_factor)
        filtered_signal = filtfilt(b_notch, a_notch, filtered_signal)

        return filtered_signal

    def update_plot(self):
        try:
            data = self.board.get_current_board_data(self.fs*self.t_lenght)  # Obtener los nuevos datos del board
            emg_signal = data[self.emg_channel, :]
            # emg_signal = np.where((emg_signal < -self.threshold_emg) | (emg_signal > self.threshold_emg), 0, emg_signal)
            filtered_signal = self._filter_emg_signal(emg_signal)
            self.curve.setData(filtered_signal)
        except:
            pass

    def mean_emg(self):
        try:
            data = self.board.get_current_board_data(self.fs)
            average_value = np.mean(data[self.emg_channel,:])
            print(average_value)
        except:
            pass

    def closeEvent(self, event):
        self.board.stop_stream()
        self.board.release_session()
        event.accept()  # Aceptar el cierre de la ventana

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == ord('Q'):
            self.close()

# Ejemplo de ejecución
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    emg_system = EMGControlSystem(emg_channel=1, placa=3, t_lenght=2, threshold_emg=250, placa_port='COM6')
    emg_system.timer.start(50)  # Puedes ajustar el intervalo aquí
    emg_system.timer_promedio.start(1500)  # Puedes ajustar el intervalo aquí
    sys.exit(app.exec_())