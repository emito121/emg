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
    def __init__(self, emg_channel, t_lenght=10, arduino_port='COM4', threshold_emg=100, placa=3, placa_port='COM6', arduino_use = False):
        super().__init__()

        self.opciones_placas = {
            1: [BoardIds.CYTON_BOARD, 250],
            2: [BoardIds.GANGLION_BOARD, 200],
            3: [BoardIds.SYNTHETIC_BOARD, 250]
        }
        self.placa_port = placa_port
        self.board_type = self.opciones_placas.get(placa)[0]
        print(str(self.board_type))
        self.emg_channel = emg_channel
        self.t_lenght = t_lenght
        self.arduino_port = arduino_port
        self.threshold_emg = threshold_emg
        
        self.fs = self.opciones_placas.get(placa)[1]
        
        # Configurar arduino si se utiliza
        self.arduino_use = arduino_use
        if self.arduino_use:
            self.arduino_port = arduino_port
            self._init_serial()  # Conectar con Arduino

        #Asociar la interfaz gráfica
        uic.loadUi('interfaz.ui', self)
        self.label_umbral.setText('Umbral Seleccionado: ' + str(self.threshold_emg))
        self.button_umbral.clicked.connect(self.cambiar_umbral)
        # Crear el temporizador de actualización
        self.timer = QTimer()
        self.timer_promedio = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer_promedio.timeout.connect(self.mean_emg)
        
        self.button_close.clicked.connect(self.closeEvent)

        # Inicializar OpenBCI y la interfaz gráfica
        self.board = self._setup_board()
        self._init_ui()
        self.show()

    def cambiar_umbral(self):
        try:
            self.threshold_emg = float(self.line_umbral.text())
            self.label_umbral.setText('Umbral Seleccionado: ' + str(self.threshold_emg))
        except:
            pass

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

    # Inicializar la gráfica de la serie temporal
    def _init_timeseries(self):
        self.plot = self.graphics_window.addPlot(row=0, col=0)
        self.plot.showAxis('left', True)
        self.plot.setMenuEnabled('left', True)
        self.plot.showGrid(x=True, y=True)

        ax0 = self.plot.getAxis('left')
        ax0.setStyle(showValues=True)
        ax0.setLabel(f"Canal {self.emg_channel}", color='r', size='14pt', bold=True)
        self.plot.setYRange(-100, 100)  # Rango fijo en el eje Y
        self.plot.setXRange(0,self.fs*self.t_lenght-300)
        ax1 = self.plot.getAxis('bottom')
        ax1.setStyle(showValues=True)
        ax1.setTickFont(QFont('Arial', 8))
        ax1.setRange(0, self.t_lenght)

        self.plot.showAxis('top', False)
        self.plot.showAxis('bottom', True)

        self.curve = self.plot.plot(pen='r', name=f'Canal {self.emg_channel}')

    # Función para aplicar un filtro pasa-banda a la señal EMG
    def _filter_emg_signal(self, emg_signal):
        lowcut = 5.0
        highcut = 120.0
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
        data = self.board.get_current_board_data(self.fs*self.t_lenght) 

        emg_signal = data[self.emg_channel, :]
        filtered_signal = self._filter_emg_signal(emg_signal)
        self.curve.setData(filtered_signal[150:-150])
        # self.curve.setData(filtered_signal)

    def mean_emg(self):
        try:
            data = self.board.get_current_board_data(self.fs*2)
            data = data[self.emg_channel,:]
            filer_data = self._filter_emg_signal(data)
            average_value = np.sqrt(np.mean(filer_data[300:-150]**2))
            RMS = round(average_value, 2)
            print('RMS: ' + str(RMS))
            self.label_RMS.setText('RMS: ' + str(RMS))
            if self.arduino_use:
                self._control_servo(average_value)
        except:
            pass

    def closeEvent(self):
        self.board.stop_stream()
        self.board.release_session()
        self.close()
        if self.arduino_use:
            self.arduino.write(f"0\n".encode())
            self.arduino.close()
        self.closeEvent()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == ord('Q'):
            self.close()
            self.arduino.close()
            self.closeEvent()

    # Conectar con Arduino usando pySerial
    def _init_serial(self):
        self.arduino = serial.Serial(self.arduino_port, 9600)
        time.sleep(2)  # Dar tiempo a la conexión para establecerse

    def _control_servo(self, rms_value):
        if rms_value > self.threshold_emg:
            mensaje = '1' # Mover el servo
            self.label_Arduino.setText('Enviado a Arduino: ' + mensaje)
        else:
            mensaje = '0'  # Retornar el servo a 0 grados
            self.label_Arduino.setText('Enviado a Arduino: ' + mensaje)

        print("Envio a Arduino: " + str(mensaje))
        self.arduino.write(f"{mensaje}\n".encode())

# Ejemplo de ejecución
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    emg_system = EMGControlSystem(emg_channel=1, placa=1, t_lenght=5, threshold_emg=5, placa_port='COM4', arduino_port='COM8', arduino_use = True)
    emg_system.timer.start(50)  # Puedes ajustar el intervalo aquí
    emg_system.timer_promedio.start(200)  # Puedes ajustar el intervalo aquí
    sys.exit(app.exec_())