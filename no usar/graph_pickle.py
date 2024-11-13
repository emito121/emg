import pickle
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt

# Función para crear un filtro pasa-banda
def butter_bandpass(lowcut, highcut, fs, order=4):
    nyquist = 0.5 * fs  # Frecuencia de Nyquist
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    return b, a

# Función para aplicar un filtro pasa-banda
def apply_bandpass_filter(data, lowcut, highcut, fs, order=4):
    b, a = butter_bandpass(lowcut, highcut, fs, order)
    return filtfilt(b, a, data)

# Función para aplicar un filtro notch (eliminación de una frecuencia específica)
def apply_notch_filter(data, notch_freq, fs, quality_factor=30):
    # Crea un filtro notch para eliminar una frecuencia específica
    nyquist = 0.5 * fs
    notch = notch_freq / nyquist
    b, a = butter(2, [notch - 1/quality_factor, notch + 1/quality_factor], btype='bandstop')
    return filtfilt(b, a, data)

def graficar_datos_pickle(pickle_file, lowcut=5, highcut=120, notch_freq=50, fs=250):
    """
    Carga los datos desde un archivo pickle, aplica un filtro pasa-banda y un filtro notch,
    y los grafica.
    
    :param pickle_file: Ruta al archivo pickle que contiene los datos.
    :param lowcut: Frecuencia de corte inferior para el filtro pasa-banda (Hz).
    :param highcut: Frecuencia de corte superior para el filtro pasa-banda (Hz).
    :param notch_freq: Frecuencia para el filtro notch (Hz).
    :param fs: Frecuencia de muestreo (Hz).
    """
    # Cargar los datos desde el archivo pickle
    with open(pickle_file, "rb") as f:
        data = pickle.load(f)
    
    # Crear la figura y los ejes para la gráfica
    plt.figure(figsize=(10, 6))
    
    # Graficar cada canal
    for i, canal_data in enumerate(data):
        if i == 0:
            # Aplicar filtro pasa-banda y filtro notch
            filtered_data = apply_bandpass_filter(canal_data, lowcut, highcut, fs)
            filtered_data = apply_notch_filter(filtered_data, notch_freq, fs)

        # Graficar los datos filtrados
            plt.plot(filtered_data[:int(len(filtered_data)/2)], label=f"Canal {i+1}")

    # Añadir etiquetas y título
    plt.xlabel("Tiempo (muestras)")
    plt.ylabel("Valor")
    plt.title("Datos Filtrados de los Canales de Cyton")
    plt.legend()  # Mostrar la leyenda
    
    # Mostrar la gráfica
    plt.show()

# Llamada a la función para graficar los datos
graficar_datos_pickle("datos_cyton.pkl")