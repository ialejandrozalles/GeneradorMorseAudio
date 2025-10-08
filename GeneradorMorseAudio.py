import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from scipy.io import wavfile
import os
import pygame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class GeneradorMorseAudio:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Generador Morse en Audio")
        self.ventana.geometry("900x700")
        self.ventana.resizable(True, False)
        
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
        self.audioData = None
        self.sampleRate = None
        self.senalMorse = None
        self.duracionAudio = 0
        self.posicionMorse = 0
        self.reproduciendo = False
        self.archivoTemporal = None
        
        pygame.mixer.init()
        
        self.configurarInterfaz()
    
    def configurarInterfaz(self):
        frameSuperior = ttk.Frame(self.ventana)
        frameSuperior.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        frameIzquierdo = ttk.Frame(frameSuperior)
        frameIzquierdo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,5))
        
        ttk.Label(frameIzquierdo, text="Texto a Convertir:", font=("Arial", 10, "bold")).pack(pady=(0,5))
        self.entradaTexto = tk.Text(frameIzquierdo, height=3, width=40, font=("Arial", 10))
        self.entradaTexto.pack()
        self.entradaTexto.bind('<KeyRelease>', lambda e: self.actualizarVisualizacion())
        
        frameArchivo = ttk.Frame(frameIzquierdo)
        frameArchivo.pack(pady=10)
        ttk.Button(frameArchivo, text="Seleccionar Audio", command=self.seleccionarArchivo).pack(side=tk.LEFT, padx=5)
        self.labelArchivo = ttk.Label(frameArchivo, text="Sin audio", foreground="gray")
        self.labelArchivo.pack(side=tk.LEFT, padx=5)
        
        frameOpciones = ttk.LabelFrame(frameIzquierdo, text="Configuración", padding=10)
        frameOpciones.pack(fill=tk.X, pady=5)
        
        ttk.Label(frameOpciones, text="Canal:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.selectorCanal = ttk.Combobox(frameOpciones, values=["Izquierdo (L)", "Derecho (R)", "Ambos (L+R)"], state="readonly", width=15)
        self.selectorCanal.set("Izquierdo (L)")
        self.selectorCanal.grid(row=0, column=1, padx=5, pady=3)
        
        ttk.Label(frameOpciones, text="Frecuencia (Hz):").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.entradaFrecuencia = ttk.Entry(frameOpciones, width=17)
        self.entradaFrecuencia.insert(0, "800")
        self.entradaFrecuencia.grid(row=1, column=1, padx=5, pady=3)
        self.entradaFrecuencia.bind('<KeyRelease>', lambda e: self.actualizarVisualizacion())
        
        ttk.Label(frameOpciones, text="Velocidad (WPM):").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.entradaVelocidad = ttk.Entry(frameOpciones, width=17)
        self.entradaVelocidad.insert(0, "20")
        self.entradaVelocidad.grid(row=2, column=1, padx=5, pady=3)
        self.entradaVelocidad.bind('<KeyRelease>', lambda e: self.actualizarVisualizacion())
        
        ttk.Label(frameOpciones, text="Volumen (%):").grid(row=3, column=0, sticky=tk.W, pady=3)
        frameVolumen = ttk.Frame(frameOpciones)
        frameVolumen.grid(row=3, column=1, padx=5, pady=3, sticky=tk.W)
        self.labelVolumen = ttk.Label(frameVolumen, text="30%", width=4)
        self.sliderVolumen = ttk.Scale(frameVolumen, from_=1, to=100, orient=tk.HORIZONTAL, length=80, command=self.actualizarValorVolumen)
        self.sliderVolumen.set(30)
        self.sliderVolumen.pack(side=tk.LEFT)
        self.labelVolumen.pack(side=tk.LEFT, padx=3)
        
        ttk.Label(frameOpciones, text="Pitch:").grid(row=4, column=0, sticky=tk.W, pady=3)
        framePitch = ttk.Frame(frameOpciones)
        framePitch.grid(row=4, column=1, padx=5, pady=3, sticky=tk.W)
        self.labelPitch = ttk.Label(framePitch, text="1.00x", width=4)
        self.sliderPitch = ttk.Scale(framePitch, from_=0.5, to=2.0, orient=tk.HORIZONTAL, length=80, command=self.actualizarValorPitch)
        self.sliderPitch.set(1.0)
        self.sliderPitch.pack(side=tk.LEFT)
        self.labelPitch.pack(side=tk.LEFT, padx=3)
        self.sliderPitch.bind('<ButtonRelease-1>', lambda e: self.actualizarVisualizacion())
        
        ttk.Label(frameOpciones, text="Fade (ms):").grid(row=5, column=0, sticky=tk.W, pady=3)
        self.entradaFade = ttk.Entry(frameOpciones, width=17)
        self.entradaFade.insert(0, "5")
        self.entradaFade.grid(row=5, column=1, padx=5, pady=3)
        
        ttk.Label(frameOpciones, text="Modo Mezcla:").grid(row=6, column=0, sticky=tk.W, pady=3)
        self.selectorMezcla = ttk.Combobox(frameOpciones, values=["Sumar", "Reemplazar"], state="readonly", width=15)
        self.selectorMezcla.set("Sumar")
        self.selectorMezcla.grid(row=6, column=1, padx=5, pady=3)
        
        frameDerecho = ttk.LabelFrame(frameSuperior, text="Vista Previa", padding=10)
        frameDerecho.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.figura = Figure(figsize=(6, 4), dpi=80)
        self.ax = self.figura.add_subplot(111)
        self.ax.set_xlabel('Tiempo (s)')
        self.ax.set_ylabel('Amplitud')
        self.ax.set_title('Forma de Onda')
        self.ax.grid(True, alpha=0.3)
        
        self.canvas = FigureCanvasTkAgg(self.figura, frameDerecho)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect('button_press_event', self.onClick)
        
        frameControles = ttk.Frame(frameDerecho)
        frameControles.pack(pady=5)
        
        self.btnReproducir = ttk.Button(frameControles, text="▶ Reproducir", command=self.reproducir, state=tk.DISABLED)
        self.btnReproducir.pack(side=tk.LEFT, padx=3)
        
        self.btnDetener = ttk.Button(frameControles, text="⏹ Detener", command=self.detener, state=tk.DISABLED)
        self.btnDetener.pack(side=tk.LEFT, padx=3)
        
        ttk.Label(frameControles, text="Posición:").pack(side=tk.LEFT, padx=5)
        self.labelPosicion = ttk.Label(frameControles, text="0.00 s", foreground="blue")
        self.labelPosicion.pack(side=tk.LEFT)
        
        frameInferior = ttk.Frame(self.ventana)
        frameInferior.pack(fill=tk.X, padx=10, pady=(0,10))
        
        ttk.Button(frameInferior, text="Generar Audio con Morse", command=self.procesarAudio).pack()
    
    def actualizarValorVolumen(self, valor):
        self.labelVolumen.config(text=f"{int(float(valor))}%")
    
    def actualizarValorPitch(self, valor):
        self.labelPitch.config(text=f"{float(valor):.2f}x")
    
    def seleccionarArchivo(self):
        archivo = filedialog.askopenfilename(filetypes=[("Archivos WAV", "*.wav")])
        if archivo:
            self.archivoAudio = archivo
            self.labelArchivo.config(text=os.path.basename(archivo), foreground="black")
            self.cargarAudio()
    
    def cargarAudio(self):
        try:
            self.sampleRate, self.audioData = wavfile.read(self.archivoAudio)
            if len(self.audioData.shape) == 1:
                self.audioData = np.column_stack((self.audioData, self.audioData))
            self.duracionAudio = len(self.audioData) / self.sampleRate
            self.actualizarVisualizacion()
            self.btnReproducir.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el audio: {str(e)}")
    
    def textoAMorse(self, texto):
        return ' '.join(self.codigoMorse.get(c.upper(), '') for c in texto)
    
    def aplicarFade(self, senal, sampleRate, duracionMs):
        if duracionMs <= 0:
            return senal
        muestras = int((duracionMs / 1000) * sampleRate)
        muestras = min(muestras, len(senal) // 4)
        if muestras == 0:
            return senal
        fadeIn = np.linspace(0, 1, muestras)
        fadeOut = np.linspace(1, 0, muestras)
        senal[:muestras] *= fadeIn
        senal[-muestras:] *= fadeOut
        return senal
    
    def cambiarPitch(self, senal, factor):
        if factor == 1.0:
            return senal
        indices = np.arange(0, len(senal), factor)
        return np.interp(indices, np.arange(len(senal)), senal)
    
    def generarTonos(self, morse, sampleRate, frecuencia, wpm, duracionFade, factorPitch):
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
        
        if len(senalMorse) == 0:
            return np.array([])
        
        senalCompleta = np.array(senalMorse)
        return self.cambiarPitch(senalCompleta, factorPitch)
    
    def actualizarVisualizacion(self):
        if self.audioData is None:
            return
        
        texto = self.entradaTexto.get("1.0", tk.END).strip()
        if not texto:
            self.senalMorse = None
            self.dibujarFormaOnda()
            return
        
        try:
            frecuencia = float(self.entradaFrecuencia.get())
            velocidad = float(self.entradaVelocidad.get())
            factorPitch = float(self.sliderPitch.get())
            duracionFade = float(self.entradaFade.get())
        except ValueError:
            return
        
        codigoMorse = self.textoAMorse(texto)
        self.senalMorse = self.generarTonos(codigoMorse, self.sampleRate, frecuencia, velocidad, duracionFade, factorPitch)
        self.dibujarFormaOnda()
    
    def dibujarFormaOnda(self):
        self.ax.clear()
        
        if self.audioData is not None:
            tiempoAudio = np.linspace(0, self.duracionAudio, len(self.audioData))
            audioMono = self.audioData[:, 0].astype(np.float32)
            factor = max(1, len(audioMono) // 5000)
            self.ax.plot(tiempoAudio[::factor], audioMono[::factor], color='blue', alpha=0.6, linewidth=0.5, label='Audio Original')
        
        if self.senalMorse is not None and len(self.senalMorse) > 0:
            duracionMorse = len(self.senalMorse) / self.sampleRate
            tiempoMorse = np.linspace(self.posicionMorse, self.posicionMorse + duracionMorse, len(self.senalMorse))
            factor = max(1, len(self.senalMorse) // 5000)
            volumen = float(self.sliderVolumen.get()) / 100
            senalEscalada = self.senalMorse * volumen * np.max(np.abs(self.audioData))
            self.ax.plot(tiempoMorse[::factor], senalEscalada[::factor], color='red', alpha=0.8, linewidth=0.8, label='Señal Morse')
        
        self.ax.axvline(x=self.posicionMorse, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label='Posición')
        
        self.ax.set_xlabel('Tiempo (s)')
        self.ax.set_ylabel('Amplitud')
        self.ax.set_title('Vista Previa del Audio con Morse')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='upper right', fontsize=8)
        
        self.canvas.draw()
    
    def onClick(self, event):
        if event.inaxes and event.xdata is not None:
            self.posicionMorse = max(0, min(event.xdata, self.duracionAudio))
            self.labelPosicion.config(text=f"{self.posicionMorse:.2f} s")
            self.dibujarFormaOnda()
    
    def reproducir(self):
        if self.audioData is None:
            return
        
        try:
            audioTemp = self.audioData.copy().astype(np.float32)
            
            if self.senalMorse is not None and len(self.senalMorse) > 0:
                inicioMuestra = int(self.posicionMorse * self.sampleRate)
                finMuestra = min(inicioMuestra + len(self.senalMorse), len(audioTemp))
                longitudMorse = finMuestra - inicioMuestra
                
                volumen = float(self.sliderVolumen.get()) / 100
                amplitudMaxima = np.max(np.abs(audioTemp))
                senalMorseEscalada = self.senalMorse[:longitudMorse] * volumen * amplitudMaxima
                
                canalSeleccion = self.selectorCanal.get()
                modoMezcla = self.selectorMezcla.get()
                
                if modoMezcla == "Sumar":
                    if "Izquierdo" in canalSeleccion:
                        audioTemp[inicioMuestra:finMuestra, 0] += senalMorseEscalada
                    elif "Derecho" in canalSeleccion:
                        audioTemp[inicioMuestra:finMuestra, 1] += senalMorseEscalada
                    else:
                        audioTemp[inicioMuestra:finMuestra, 0] += senalMorseEscalada
                        audioTemp[inicioMuestra:finMuestra, 1] += senalMorseEscalada
                else:
                    if "Izquierdo" in canalSeleccion:
                        audioTemp[inicioMuestra:finMuestra, 0] = senalMorseEscalada
                    elif "Derecho" in canalSeleccion:
                        audioTemp[inicioMuestra:finMuestra, 1] = senalMorseEscalada
                    else:
                        audioTemp[inicioMuestra:finMuestra, 0] = senalMorseEscalada
                        audioTemp[inicioMuestra:finMuestra, 1] = senalMorseEscalada
            
            audioTemp = np.clip(audioTemp, -32768, 32767).astype(np.int16)
            
            if self.archivoTemporal and os.path.exists(self.archivoTemporal):
                os.remove(self.archivoTemporal)
            
            self.archivoTemporal = "temp_preview.wav"
            wavfile.write(self.archivoTemporal, self.sampleRate, audioTemp)
            
            pygame.mixer.music.load(self.archivoTemporal)
            pygame.mixer.music.play()
            self.reproduciendo = True
            self.btnDetener.config(state=tk.NORMAL)
            self.btnReproducir.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo reproducir: {str(e)}")
    
    def detener(self):
        pygame.mixer.music.stop()
        self.reproduciendo = False
        self.btnReproducir.config(state=tk.NORMAL)
        self.btnDetener.config(state=tk.DISABLED)
    
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
            factorPitch = float(self.sliderPitch.get())
            duracionFade = float(self.entradaFade.get())
        except ValueError:
            messagebox.showerror("Error", "Valores numéricos inválidos")
            return
        
        codigoMorse = self.textoAMorse(texto)
        senalMorse = self.generarTonos(codigoMorse, self.sampleRate, frecuencia, velocidad, duracionFade, factorPitch)
        
        inicioMuestra = int(self.posicionMorse * self.sampleRate)
        if inicioMuestra >= len(self.audioData):
            messagebox.showerror("Error", "La posición de inicio excede la duración del audio")
            return
        
        longitudDisponible = len(self.audioData) - inicioMuestra
        senalMorse = senalMorse[:longitudDisponible]
        
        audioModificado = self.audioData.copy().astype(np.float32)
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
            wavfile.write(archivoSalida, self.sampleRate, audioModificado)
            messagebox.showinfo("Éxito", f"Audio generado:\n{os.path.basename(archivoSalida)}")
    
    def __del__(self):
        if self.archivoTemporal and os.path.exists(self.archivoTemporal):
            try:
                os.remove(self.archivoTemporal)
            except:
                pass

if __name__ == "__main__":
    ventana = tk.Tk()
    app = GeneradorMorseAudio(ventana)
    ventana.mainloop()