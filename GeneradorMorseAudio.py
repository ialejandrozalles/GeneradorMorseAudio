import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from scipy.io import wavfile
import os

class GeneradorMorseAudio:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Generador Morse en Audio")
        self.ventana.geometry("550x550")
        self.ventana.resizable(False, False)
        
        self.codigoMorse = {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
            'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
            'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
            'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
            'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
            '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
            '8': '---..', '9': '----.', ' ': '/'
        }
        
        self.archivoAudio = None
        self.configurarInterfaz()
    
    def configurarInterfaz(self):
        ttk.Label(self.ventana, text="Texto a Convertir:", font=("Arial", 10, "bold")).pack(pady=(20,5))
        self.entradaTexto = tk.Text(self.ventana, height=4, width=55, font=("Arial", 10))
        self.entradaTexto.pack(padx=20)
        
        frameArchivo = ttk.Frame(self.ventana)
        frameArchivo.pack(pady=15)
        ttk.Button(frameArchivo, text="Seleccionar Audio", command=self.seleccionarArchivo).pack(side=tk.LEFT, padx=5)
        self.labelArchivo = ttk.Label(frameArchivo, text="Ningún archivo seleccionado", foreground="gray")
        self.labelArchivo.pack(side=tk.LEFT, padx=5)
        
        frameOpciones = ttk.LabelFrame(self.ventana, text="Configuración", padding=15)
        frameOpciones.pack(padx=20, pady=10, fill=tk.X)
        
        ttk.Label(frameOpciones, text="Canal:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.selectorCanal = ttk.Combobox(frameOpciones, values=["Izquierdo (L)", "Derecho (R)", "Ambos (L+R)"], state="readonly", width=18)
        self.selectorCanal.set("Izquierdo (L)")
        self.selectorCanal.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(frameOpciones, text="Frecuencia (Hz):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.entradaFrecuencia = ttk.Entry(frameOpciones, width=20)
        self.entradaFrecuencia.insert(0, "800")
        self.entradaFrecuencia.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(frameOpciones, text="Velocidad (WPM):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.entradaVelocidad = ttk.Entry(frameOpciones, width=20)
        self.entradaVelocidad.insert(0, "20")
        self.entradaVelocidad.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(frameOpciones, text="Volumen Morse (%):").grid(row=3, column=0, sticky=tk.W, pady=5)
        frameVolumen = ttk.Frame(frameOpciones)
        frameVolumen.grid(row=3, column=1, padx=10, pady=5, sticky=tk.W)
        self.labelVolumen = ttk.Label(frameVolumen, text="30%", width=5)
        self.sliderVolumen = ttk.Scale(frameVolumen, from_=1, to=100, orient=tk.HORIZONTAL, length=120, command=self.actualizarValorVolumen)
        self.sliderVolumen.set(30)
        self.sliderVolumen.pack(side=tk.LEFT)
        self.labelVolumen.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(frameOpciones, text="Fade In/Out (ms):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.entradaFade = ttk.Entry(frameOpciones, width=20)
        self.entradaFade.insert(0, "5")
        self.entradaFade.grid(row=4, column=1, padx=10, pady=5)
        
        ttk.Label(frameOpciones, text="Posición Inicio (s):").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.entradaPosicion = ttk.Entry(frameOpciones, width=20)
        self.entradaPosicion.insert(0, "0")
        self.entradaPosicion.grid(row=5, column=1, padx=10, pady=5)
        
        ttk.Label(frameOpciones, text="Modo Mezcla:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.selectorMezcla = ttk.Combobox(frameOpciones, values=["Sumar", "Reemplazar"], state="readonly", width=18)
        self.selectorMezcla.set("Sumar")
        self.selectorMezcla.grid(row=6, column=1, padx=10, pady=5)
        
        ttk.Button(self.ventana, text="Generar Audio con Morse", command=self.procesarAudio).pack(pady=20)
    
    def actualizarValorVolumen(self, valor):
        self.labelVolumen.config(text=f"{int(float(valor))}%")
    
    def seleccionarArchivo(self):
        archivo = filedialog.askopenfilename(filetypes=[("Archivos WAV", "*.wav")])
        if archivo:
            self.archivoAudio = archivo
            self.labelArchivo.config(text=os.path.basename(archivo), foreground="black")
    
    def textoAMorse(self, texto):
        return ' '.join(self.codigoMorse.get(c.upper(), '') for c in texto)
    
    def aplicarFade(self, senal, sampleRate, duracionMs):
        if duracionMs <= 0:
            return senal
        muestras = int((duracionMs / 1000) * sampleRate)
        muestras = min(muestras, len(senal) // 4)
        fadeIn = np.linspace(0, 1, muestras)
        fadeOut = np.linspace(1, 0, muestras)
        senal[:muestras] *= fadeIn
        senal[-muestras:] *= fadeOut
        return senal
    
    def generarTonos(self, morse, sampleRate, frecuencia, wpm, duracionFade):
        unidadTiempo = 1.2 / wpm
        senalMorse = []
        
        for simbolo in morse:
            if simbolo == '.':
                duracion = int(unidadTiempo * sampleRate)
                t = np.linspace(0, unidadTiempo, duracion, False)
                tono = np.sin(2 * np.pi * frecuencia * t)
                tono = self.aplicarFade(tono, sampleRate, duracionFade)
                senalMorse.extend(tono)
                senalMorse.extend(np.zeros(duracion))
            elif simbolo == '-':
                duracion = int(3 * unidadTiempo * sampleRate)
                t = np.linspace(0, 3 * unidadTiempo, duracion, False)
                tono = np.sin(2 * np.pi * frecuencia * t)
                tono = self.aplicarFade(tono, sampleRate, duracionFade)
                senalMorse.extend(tono)
                senalMorse.extend(np.zeros(int(unidadTiempo * sampleRate)))
            elif simbolo == ' ':
                senalMorse.extend(np.zeros(int(3 * unidadTiempo * sampleRate)))
            elif simbolo == '/':
                senalMorse.extend(np.zeros(int(7 * unidadTiempo * sampleRate)))
        
        return np.array(senalMorse)
    
    def procesarAudio(self):
        texto = self.entradaTexto.get("1.0", tk.END).strip()
        if not texto:
            messagebox.showerror("Error", "Ingrese el texto a convertir")
            return
        
        if not self.archivoAudio:
            messagebox.showerror("Error", "Seleccione un archivo de audio")
            return
        
        try:
            frecuencia = float(self.entradaFrecuencia.get())
            velocidad = float(self.entradaVelocidad.get())
            volumen = float(self.sliderVolumen.get()) / 100
            duracionFade = float(self.entradaFade.get())
            posicionInicio = float(self.entradaPosicion.get())
        except ValueError:
            messagebox.showerror("Error", "Valores numéricos inválidos")
            return
        
        sampleRate, audioData = wavfile.read(self.archivoAudio)
        codigoMorse = self.textoAMorse(texto)
        senalMorse = self.generarTonos(codigoMorse, sampleRate, frecuencia, velocidad, duracionFade)
        
        if len(audioData.shape) == 1:
            audioData = np.column_stack((audioData, audioData))
        
        inicioMuestra = int(posicionInicio * sampleRate)
        if inicioMuestra >= len(audioData):
            messagebox.showerror("Error", "La posición de inicio excede la duración del audio")
            return
        
        longitudDisponible = len(audioData) - inicioMuestra
        senalMorse = senalMorse[:longitudDisponible]
        
        audioModificado = audioData.copy().astype(np.float32)
        amplitudMaxima = np.max(np.abs(audioModificado))
        senalMorseEscalada = senalMorse * volumen * amplitudMaxima
        
        canalSeleccion = self.selectorCanal.get()
        modoMezcla = self.selectorMezcla.get()
        
        finMuestra = inicioMuestra + len(senalMorse)
        
        if modoMezcla == "Sumar":
            if "Izquierdo" in canalSeleccion:
                audioModificado[inicioMuestra:finMuestra, 0] += senalMorseEscalada
            elif "Derecho" in canalSeleccion:
                audioModificado[inicioMuestra:finMuestra, 1] += senalMorseEscalada
            else:
                audioModificado[inicioMuestra:finMuestra, 0] += senalMorseEscalada
                audioModificado[inicioMuestra:finMuestra, 1] += senalMorseEscalada
        else:
            if "Izquierdo" in canalSeleccion:
                audioModificado[inicioMuestra:finMuestra, 0] = senalMorseEscalada
            elif "Derecho" in canalSeleccion:
                audioModificado[inicioMuestra:finMuestra, 1] = senalMorseEscalada
            else:
                audioModificado[inicioMuestra:finMuestra, 0] = senalMorseEscalada
                audioModificado[inicioMuestra:finMuestra, 1] = senalMorseEscalada
        
        audioModificado = np.clip(audioModificado, -32768, 32767).astype(np.int16)
        
        archivoSalida = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("Archivos WAV", "*.wav")])
        if archivoSalida:
            wavfile.write(archivoSalida, sampleRate, audioModificado)
            messagebox.showinfo("Éxito", f"Audio generado:\n{os.path.basename(archivoSalida)}")

if __name__ == "__main__":
    ventana = tk.Tk()
    app = GeneradorMorseAudio(ventana)
    ventana.mainloop()