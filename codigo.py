import numpy as np
import serial
import time
import os
from PyQt5.QtWidgets import QMainWindow, QGraphicsScene, QApplication, QDialog
from PyQt5.QtGui import QFont
from PyQt5 import uic
import pyqtgraph as pg
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
from scipy.signal import butter, filtfilt

class EMGControlSystem(QDialog):
    def __init__(self, emg_channel, t_lenght=10, arduino_port='COM4', placa=3):
        super().__init__()

        self.opciones_placas = {
            1: BoardIds.CYTON_BOARD,
            2: BoardIds.GANGLION_BOARD,
            3: BoardIds.SYNTHETIC_BOARD
        }

        self.board_type = self.opciones_placas.get(placa)

        # Variables de control
        self.emg_channel = emg_channel  # Canal único de EMG
        self.t_lenght = t_lenght  # Duración temporal para visualización
        self.arduino_port = arduino_port  # Puerto para Arduino
        self.threshold = 0.05  # Umbral para mover el servomotor
        self.board = self._setup_board()  # Inicializar la conexión con OpenBCI
        self.fs = 200  # Frecuencia de muestreo (ajusta según tu dispositivo)

        # Cargar la interfaz desde el archivo .ui
        # ui_path = os.path.join(os.path.dirname(__file__), 'interfaz.ui')
        uic.loadUi('interfaz.ui', self)

        # Configurar la gráfica de tiempos
        self._init_ui()
        # self._init_serial()  # Conectar con Arduino

        self.show()  # Mostrar la ventana

    # Inicializar OpenBCI y Brainflow
    def _setup_board(self):
        params = BrainFlowInputParams()
        params.serial_port = 'COM3'  # Cambia según tu configuración
        board = BoardShim(self.board_type.value, params)
        board.prepare_session()
        board.start_stream()
        return board

    # Inicializar la interfaz gráfica usando pyqtgraph y el archivo .ui
    def _init_ui(self):
        # Suponemos que hay un QGraphicsView en el archivo .ui llamado 'graphicsView'
        scene = QGraphicsScene()
        self.graphicsView.setScene(scene)
        self.graphics_window = pg.GraphicsLayoutWidget(title='EMG Plot', size=(950, 390))
        self.graphics_window.setBackground('w')
        scene.addWidget(self.graphics_window)
        
        # Inicializar la serie temporal
        self._init_timeseries()

    # Inicializar la gráfica de la serie temporal
    def _init_timeseries(self):
        self.plot = self.graphics_window.addPlot(row=0, col=0)
        self.plot.showAxis('left', True)
        self.plot.setMenuEnabled('left', True)
        self.plot.showGrid(x=True, y=True)

        ax0 = self.plot.getAxis('left')
        ax0.setStyle(showValues=True)
        ax0.setLabel(f"Canal {self.emg_channel}", color='r', size='14pt', bold=True)

        ax1 = self.plot.getAxis('bottom')
        ax1.setStyle(showValues=True)
        ax1.setTickFont(QFont('Arial', 8))
        ax1.setRange(0, self.t_lenght)

        self.plot.showAxis('top', False)
        self.plot.showAxis('bottom', True)

        self.curve = self.plot.plot(pen='r', name=f'Canal {self.emg_channel}')

    # Conectar con Arduino usando pySerial
    def _init_serial(self):
        self.arduino = serial.Serial(self.arduino_port, 9600)
        time.sleep(2)  # Dar tiempo a la conexión para establecerse

    # Función para aplicar un filtro pasa-banda a la señal EMG
    def _filter_emg_signal(self, emg_signal):
        # Definir un filtro Butterworth pasa-banda (20-500 Hz)
        lowcut = 20.0  # Frecuencia mínima (Hz)
        highcut = 500.0  # Frecuencia máxima (Hz)
        nyquist = 0.5 * self.fs
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = butter(4, [low, high], btype='band')

        # Aplicar el filtro
        filtered_signal = filtfilt(b, a, emg_signal)
        return filtered_signal

    # Función para actualizar la gráfica con datos EMG filtrados
    def update_plot(self):
        data = self.board.get_board_data(500)
        emg_signal = data[self.emg_channel, :]  # Obtener los datos del canal EMG
        self.curve.setData(emg_signal)  # Actualizar la gráfica con la señal filtrada
        # # Filtrar la señal EMG
        # filtered_signal = self._filter_emg_signal(emg_signal)

        # # Procesar la señal filtrada (por ejemplo, RMS)
        # rms_value = self._emg_feature_extraction(filtered_signal)
        # self.curve.setData(filtered_signal)  # Actualizar la gráfica con la señal filtrada
        

        # # Controlar el servomotor basado en el umbral del EMG
        # self._control_servo(rms_value)

    # Función para calcular el RMS de la señal EMG
    def _emg_feature_extraction(self, emg_signal):
        return np.sqrt(np.mean(emg_signal**2))

    # Función para controlar el servomotor
    def _control_servo(self, rms_value):
        if rms_value > self.threshold:
            posicion = 90  # Mover el servo a 90 grados
        else:
            posicion = 0  # Retornar el servo a 0 grados

        self.arduino.write(f"{posicion}\n".encode())

    # Cerrar conexiones cuando se finalice
    def closeEvent(self, event):
        self.board.stop_stream()
        self.board.release_session()
        self.arduino.close()

# Ejemplo de ejecución
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    # Crea una instancia del sistema de control de EMG con el canal 1
    emg_system = EMGControlSystem(emg_channel=1)

    # Simula actualización continua de la gráfica y control
    while True:
        emg_system.update_plot()
        app.processEvents()  # Permite que la UI se actualice en tiempo real

    sys.exit(app.exec_())
