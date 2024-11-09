import serial
import time
import numpy as np
import matplotlib.pyplot as plt
import pickle  # Importamos pickle

def procesar_linea_datos(linea_bytes, longitud_segmento=3, num_canales=8):
    """
    Procesa una línea de datos en bytes y la convierte a una lista de valores enteros por canal.
    
    :param linea_bytes: línea de datos en formato `bytes`
    :param longitud_segmento: longitud de cada segmento en bytes
    :param num_canales: número de canales de datos
    :return: lista de listas de valores enteros procesados, uno por canal
    """
    datos_procesados = [[] for _ in range(num_canales)]  # Lista para cada canal
    
    # Recorrer la línea en segmentos de longitud definida
    for i in range(0, len(linea_bytes), longitud_segmento):
        # Obtener el segmento de datos
        segmento = linea_bytes[i:i + longitud_segmento]
        
        # Convertir el segmento a un entero (modificar el formato si es necesario)
        valor = int.from_bytes(segmento, byteorder='big', signed=False)
        
        # Asignar el valor al canal correspondiente (usando el índice)
        canal_index = (i // longitud_segmento) % num_canales
        datos_procesados[canal_index].append(valor)
    
    return datos_procesados

def record_data_from_cyton_serial(port: str, duration: int = 10, sampling_rate: int = 250, longitud_segmento=3, num_canales=8):
    """
    Función para registrar datos desde la placa Cyton de OpenBCI utilizando comunicación serial directa.
    
    Parámetros:
        port (str): Puerto serial donde está conectada la Cyton (ej. "COM3" en Windows o "/dev/ttyUSB0" en Linux).
        duration (int): Duración en segundos para registrar los datos.
        sampling_rate (int): Frecuencia de muestreo esperada de la Cyton (por defecto 250 Hz).
        longitud_segmento (int): Longitud de cada segmento de datos en bytes.
        num_canales (int): Número de canales de datos.
        
    Retorno:
        list: Lista de listas que contiene los datos por canal.
    """
    # Configuración del puerto serial
    try:
        ser = serial.Serial(port, baudrate=115200, timeout=1)
        time.sleep(2)  # Esperar a que el puerto serial esté listo
        print(f"Conectado al puerto {port} a 115200 baudios.")
    except serial.SerialException:
        print(f"No se pudo abrir el puerto {port}. Asegúrate de que la Cyton esté conectada.")
        return None
    
    # Enviar comando para iniciar el flujo de datos
    ser.write(b'b')  # Comando 'b' para comenzar el streaming en Cyton
    print("Iniciando la captura de datos desde Cyton...")

    data_list = [[] for _ in range(num_canales)]  # Crear una lista vacía para cada canal
    start_time = time.time()
    
    try:
        while True:
            # Verificar si se ha alcanzado el tiempo de captura
            if duration > 0 and (time.time() - start_time) >= duration:
                break
            
            # Leer datos desde el puerto serial
            line = ser.readline().strip()  # Leer línea y eliminar espacios en blanco
            
            # Verificar si la línea no está vacía y procesarla
            if line:
                processed_data = procesar_linea_datos(line, longitud_segmento, num_canales)
                for i, canal_data in enumerate(processed_data):
                    data_list[i].extend(canal_data)  # Añadir los datos de cada canal a su lista correspondiente
                
                # Imprimir los datos procesados
                print(f"Datos procesados por canal: {processed_data}")
                
    except Exception as e:
        print(f"Error durante la captura de datos: {e}")
    
    # Asegurarse de que todos los canales tengan la misma longitud (rellenar con ceros)
    max_length = max(len(canal) for canal in data_list)  # Longitud máxima de canal
    for canal in data_list:
        while len(canal) < max_length:
            canal.append(0)  # Rellenar con ceros

    # Convertir la lista de datos por canal en un arreglo homogéneo de NumPy
    # No es necesario convertir a un array NumPy aquí, ya que ya estamos manejando las listas correctamente
    # pero si quieres usarlo:
    data_array = np.array(data_list)

    # Guardar los datos en un archivo pickle
    with open("datos_cyton.pkl", "wb") as f:
        pickle.dump(data_list, f)  # Guardamos las listas directamente
    print("Datos guardados en 'datos_cyton.pkl'")
    
    return data_array

# Llamada a la función para registrar datos
data = record_data_from_cyton_serial(port="COM4", duration=10)
print(data)