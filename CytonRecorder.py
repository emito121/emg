import serial
import time
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
import threading

class CytonDataRecorder:
    def __init__(self, port: str, sampling_rate: int = 250, num_canales: int = 8, longitud_segmento: int = 3, buffer_size: int = 100):
        """
        Inicializa el grabador de datos de la placa Cyton de OpenBCI con un buffer de tamaño fijo.
        
        :param port: Puerto serial donde está conectada la Cyton (ej. "COM3" en Windows o "/dev/ttyUSB0" en Linux).
        :param sampling_rate: Frecuencia de muestreo de la Cyton (por defecto 250 Hz).
        :param num_canales: Número de canales de datos (por defecto 8 canales).
        :param longitud_segmento: Longitud de cada segmento de datos en bytes.
        :param buffer_size: Tamaño del buffer para almacenar las últimas muestras de cada canal.
        """
        self.port = port
        self.sampling_rate = sampling_rate
        self.num_canales = num_canales
        self.longitud_segmento = longitud_segmento
        self.buffer_size = buffer_size

        # Inicializar el buffer como un array de NumPy
        self.buffer = np.zeros((self.num_canales, self.buffer_size), dtype=np.int16)
        self.buffer_index = np.zeros(self.num_canales, dtype=int)  # Índices para seguir el último lugar donde insertar

        # Variables para controlar la comunicación serial
        self.ser = None
        self.capturando = False
        self.thread = None

    def procesar_linea_datos(self, linea_bytes):
        """
        Procesa una línea de datos en bytes y la convierte a una lista de valores enteros por canal.
        
        :param linea_bytes: Línea de datos en formato `bytes`.
        :return: Lista de listas de valores enteros procesados, uno por canal.
        """
        datos_procesados = [[] for _ in range(self.num_canales)]
        
        for i in range(0, len(linea_bytes), self.longitud_segmento):
            segmento = linea_bytes[i:i + self.longitud_segmento]
            valor = int.from_bytes(segmento, byteorder='big', signed=False)
            canal_index = (i // self.longitud_segmento) % self.num_canales
            datos_procesados[canal_index].append(valor)
        
        return datos_procesados

    def iniciar_captura(self):
        """
        Inicia la captura de datos desde el puerto serial de manera continua.
        """
        try:
            self.ser = serial.Serial(self.port, baudrate=115200, timeout=1)
            time.sleep(2)  # Esperar a que el puerto serial esté listo
            print(f"Conectado al puerto {self.port} a 115200 baudios.")
        except serial.SerialException:
            print(f"No se pudo abrir el puerto {self.port}. Asegúrate de que la Cyton esté conectada.")
            return
        
        # Enviar comando para iniciar el flujo de datos
        self.ser.write(b'b')  # Comando 'b' para comenzar el streaming en Cyton
        print("Iniciando la captura de datos desde Cyton...")

        # Marcar la captura como activa
        self.capturando = True

        # Iniciar un hilo para la captura continua de datos
        self.thread = threading.Thread(target=self._capturar_datos)
        self.thread.start()

    def _capturar_datos(self):
        """
        Función privada que corre en un hilo separado para capturar datos continuamente.
        """
        try:
            while self.capturando:
                line = self.ser.readline().strip()  # Leer una línea de datos
                
                if line:
                    print(f"Datos crudos recibidos: {line}")  # Depuración: Imprimir los datos crudos
                    processed_data = self.procesar_linea_datos(line)
                    print(f"Datos procesados: {processed_data}")  # Depuración: Ver los datos procesados
                    
                    for i, canal_data in enumerate(processed_data):
                        # Insertar los datos procesados en el buffer de cada canal, sobrescribiendo las muestras más antiguas
                        for valor in canal_data:
                            index = self.buffer_index[i]
                            self.buffer[i, index] = valor
                            self.buffer_index[i] = (index + 1) % self.buffer_size  # Ciclar el índice para buffer circular
                        
        except Exception as e:
            print(f"Error durante la captura de datos: {e}")
        finally:
            self.ser.close()
            print("Conexión serial cerrada.")

    def detener_captura(self):
        """
        Detiene la captura de datos y cierra la conexión serial.
        """
        self.capturando = False
        
        # Esperar a que el hilo de captura termine
        if self.thread is not None:
            self.thread.join()
        
        print("Captura detenida.")

    def obtener_ultimas_muestras(self, n=10):
        """
        Devuelve las últimas `n` muestras de cada canal almacenadas en el buffer.
        
        :param n: Número de muestras que se desean obtener de cada canal.
        :return: Un array de NumPy con las últimas `n` muestras de cada canal.
        """
        # Devolver las últimas `n` muestras de cada canal
        return self.buffer[:, -n:]

    # Métodos para aplicar los filtros

    def butter_bandpass(self, lowcut, highcut, fs, order=4):
        nyquist = 0.5 * fs
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = butter(order, [low, high], btype='band')
        return b, a

    def apply_bandpass_filter(self, data, lowcut, highcut, fs, order=4):
        b, a = self.butter_bandpass(lowcut, highcut, fs, order)
        return filtfilt(b, a, data)

    def apply_notch_filter(self, data, notch_freq, fs, quality_factor=30):
        nyquist = 0.5 * fs
        notch = notch_freq / nyquist
        b, a = butter(2, [notch - 1/quality_factor, notch + 1/quality_factor], btype='bandstop')
        return filtfilt(b, a, data)

    def graficar_datos(self, data, lowcut=5, highcut=120, notch_freq=50, fs=250):
        """
        Graficar los datos de los canales después de aplicar los filtros pasa-banda y notch.
        
        :param data: Datos de los canales a graficar.
        :param lowcut: Frecuencia de corte inferior para el filtro pasa-banda (Hz).
        :param highcut: Frecuencia de corte superior para el filtro pasa-banda (Hz).
        :param notch_freq: Frecuencia para el filtro notch (Hz).
        :param fs: Frecuencia de muestreo (Hz).
        """
        plt.figure(figsize=(10, 6))
        
        for i, canal_data in enumerate(data):
            # Aplicar filtro pasa-banda y filtro notch
            filtered_data = self.apply_bandpass_filter(canal_data, lowcut, highcut, fs)
            filtered_data = self.apply_notch_filter(filtered_data, notch_freq, fs)

            # Graficar los datos filtrados
            plt.plot(filtered_data, label=f"Canal {i+1}")
        
        plt.xlabel("Tiempo (muestras)")
        plt.ylabel("Valor")
        plt.title("Datos Filtrados de los Canales de Cyton")
        plt.legend()
        plt.show()

# Uso de la clase

# Configuración y grabación de datos
recorder = CytonDataRecorder(port="COM4", buffer_size=10000)

# Iniciar la captura
recorder.iniciar_captura()

# Después de un tiempo, se pueden obtener las últimas muestras y graficarlas
time.sleep(5)  # Capturar por 5 segundos
ultimas_muestras = recorder.obtener_ultimas_muestras(n=1000)
print(ultimas_muestras)

# Graficar las muestras
recorder.graficar_datos(ultimas_muestras)

# Detener la captura
recorder.detener_captura()