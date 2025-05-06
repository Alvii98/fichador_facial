import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
from io import BytesIO
import cv2 # opencv-python==4.9.0.80
import numpy as np # numpy==1.26.3
import face_recognition as fr # dlib-19.24.99-cp312-cp312-win_amd64.whl luego install face_recognition
# import dlib
import os
import time
from datetime import datetime
import locale
import threading
# import math
import pandas as pd # pandas y openpyxl
import requests
# from requests.auth import HTTPBasicAuth
import re
import base64

# Crear entorno virtualenv -p python3 mientorno
# PARA EXE: pyinstaller --onefile --windowed --add-data "libs/shape_predictor_68_face_landmarks.dat;face_recognition_models/models" --add-data "libs/dlib_face_recognition_resnet_model_v1.dat;face_recognition_models/models" --add-data "libs/shape_predictor_5_face_landmarks.dat;face_recognition_models/models" --add-data "libs/mmod_human_face_detector.dat;face_recognition_models/models" main.py
# ejecutar para actualizar dependencias  pip install --upgrade setuptools
class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fichador facial 2.0")
        self.ancho = 780
        self.alto = 550
        self.x = (self.winfo_screenwidth() // 2) - (self.ancho // 2)
        self.y = (self.winfo_screenheight() // 2) - (self.alto // 2) - 60
        self.geometry(f'{self.ancho}x{self.alto}+{self.x}+{self.y}')
        # print((self.winfo_screenheight()*25)/100)
        # 640x480 píxeles Mínimo: 540x380 píxeles
        self.anchoVideo = 540
        self.altoVideo = 380
        self.xV = (self.winfo_screenwidth() // 2) - (self.anchoVideo // 2)
        self.yV = (self.winfo_screenheight() // 2) - (self.altoVideo // 2)
        self.intentosFacial = 0
        self.notificacion = True
        self.cargar_video = True
        self.cara = None
        icono = Image.open("img/ico.ico")
        icono = ImageTk.PhotoImage(icono)
        # Establecerlo como ícono de la ventana
        self.iconphoto(True, icono)
        # PARA CUANDO ES DE PRUEBA
        # id = datetime.now().strftime('%Y')
        # if id != '2024':
        #     quit()
        self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
        self.menu = ImageTk.PhotoImage(file="img/menu.png")
        # Cargar el modelo preentrenado (por ejemplo, un modelo YOLO)
        self.net = None
        self.outs = None
        self.classes = None
        threading.Thread(target=self.cargar_lib).start()
        self.menu_desplegado = False
        # self.api = 'https://estudio6.site/fichado/api.php'
        self.api = ''
        # self.api = 'https://www1.dnm.gov.ar/anexo/api.php'
        self.api_user = 'api_user'
        self.api_pass = 'api_password'
        self.foto_api = ''
        self.nombre_agente = ''
        if self.api != '':
            self.verificar_api()
        self.predictor = ''
        # CARGO LIBRERIA Y OBTENGO LUGAR POR ESO LO COMENTE ARRIBA
        # threading.Thread(target=self.cargar_lib).start()
        self.validar_vida = 0
        self.nueva_ventana = None
        self.okk = 0
        self.crear_widgets()
        # self.video_molde()
        self.update_clock()
        threading.Thread(target=self.validar_fichado).start()

    def verificar_api(self):
        try:
            respuesta = requests.get(self.api)
            if respuesta.status_code == 200:
                print("La API responde correctamente.")
                return False
            else:
                messagebox.showerror("Error de sistema", "Error al intentar conectar con la API, intente mas tarde.")
                print(f"La API respondio con el codigo de estado: {respuesta.status_code}")
                quit()
                return True
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error de sistema", "Error al intentar conectar con la API, intente mas tarde.")
            print(f"Error al intentar conectar con la API: {e}")
            quit()
            return True

    def cargar_lib(self):
        # Cargar el modelo preentrenado (modelo YOLO)
        self.net = cv2.dnn.readNet("libs/yolov3.weights", "libs/yolov3.cfg")
        layer_names = self.net.getLayerNames()
        self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
        self.outs = None
        # Cargar las clases
        with open("libs/coco.names", "r") as f:
            self.classes = [line.strip() for line in f.readlines()]

        # self.predictor = dlib.shape_predictor('face_recognition/shape_predictor_68_face_landmarks.dat')

    def insertar_registro(self, documento, archivo):
        cruce = ''
        observacion = ''
        if self.documento2.get().strip() != '':
            fecha_obj = datetime.strptime(self.fechaYHora.get(), '%d/%m/%Y %H:%M:%S')
            fecha = fecha_obj.strftime('%Y-%m-%d %H:%M:%S')
            if self.cruce.get().strip() != 'ENTRADA' and self.cruce.get().strip() != 'SALIDA':
                return self.notificaciones('El cruce tiene que ser ENTRADA o SALIDA.','#df2626')
            cruce = self.cruce.get().strip()

            if self.observacion.get("1.0", tk.END).strip() != '':
                observacion = self.observacion.get("1.0", tk.END).strip()
        else:
            fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        base64_image = ''
        with open(archivo, 'rb') as file:
            base64_image = base64.b64encode(file.read())

        data = {
            'tipo': 'INSERTAR REGISTRO',
            'documento': documento,
            'agente': self.nombre_agente,
            'cruce': cruce,
            'observacion': observacion,
            'fecha': fecha,
            'lugar': self.lugar.get(),
            'foto': base64_image
        }
        try:
            response = requests.post(self.api, data=data)
            
            if response.json()['status'] == 'success':
                self.notificaciones(response.json()['message'],'#35c82b')
            elif response.json()['status'] == 'error':
                self.notificaciones(response.json()['message'],'#df2626')
            else:
                self.notificaciones(response.json()['message'],'#df2626')

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error de sistema", "Error al intentar conectar con la API, intente mas tarde.")

        os.remove(archivo)
    
    def borrar_registros(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def traer_registros(self, agente):
        data = {
            'tipo': 'REGISTROS AGENTE',
            'documento': agente
        }
        # self.verificar_api()
        try:
            response = requests.post(self.api, data=data)

            if response.json()['status'] == 'success':
                registros = response.json()['data']
                
                for item in self.tree.get_children():
                    self.tree.delete(item)

                for registro in registros:
                    self.tree.insert("", tk.END, values=(registro['documento'], registro['fecha'], registro['cruce']))
                    # self.tree.insert("", tk.END, values=registro)

                self.notificaciones(response.json()['message'],'#35c82b')
            elif response.json()['status'] == 'error':
                self.notificaciones(response.json()['message'],'#df2626')
            else:
                self.notificaciones(response.json()['message'],'#df2626')

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error de sistema", "Error al intentar conectar con la API, intente mas tarde.")

    def exportar_excel(self):
        rows = []
        try:
            for row_id in self.tree.get_children():
                row = self.tree.item(row_id)['values']
                rows.append(row)
            if not rows:
                self.notificaciones('No hay datos para exportar.', '#ff0000')
            else:
                df = pd.DataFrame(rows, columns=("Agente", "Fecha", "Cruce"))
                fecha = datetime.now().strftime('%Y%m%d%H%M')
                archivo = f"registros_{fecha}.xlsxd"
                df.to_excel(archivo, index=False)
                os.startfile(archivo)
                self.notificaciones(f'Exportado correctamente {archivo}','#35c82b')
        except Exception as e:
            self.notificaciones('Ocurrio un error al exportar.', '#ff0000')

    def validar_fecha_hora(self, event=None, *args):
        entrada = self.fecha_hora_var.get()
        if event.keysym != 'BackSpace' and event.keysym != 'Left' and event.keysym != 'right':
            self.lblValidFecha.configure(text='El formato de fecha y hora tiene que ser DD/MM/AAAA HH:MM:SS.')
            formateada = re.sub(r'[^0-9]', '', entrada)
            # Formatear la entrada a DD/MM/YYYY HH:MM:SS
            if len(formateada) >= 2:
                if int(formateada[:2]) > 31:
                    formateada = '31/' + formateada[2:]
                else:
                    formateada = formateada[:2] + '/' + formateada[2:]
            if len(formateada) >= 5:
                if int(formateada[3:5]) > 12:
                    formateada = formateada[:3]+'12/'+formateada[5:]
                else:
                    formateada = formateada[:5] + '/' + formateada[5:]
            if len(formateada) >= 10:
                if int(formateada[6:10]) > int(datetime.now().year):
                    formateada = formateada[:6] + str(datetime.now().year)+' ' + formateada[10:]
                else:
                    formateada = formateada[:10] + ' ' + formateada[10:]
            if len(formateada) >= 13:
                if int(formateada[11:13]) > 23:
                    formateada = formateada[:11] + '23:' + formateada[13:]
                else:
                    formateada = formateada[:13] + ':' + formateada[13:]
            if len(formateada) >= 16:
                if int(formateada[14:16]) > 59:
                    formateada = formateada[:14] + '59:' + formateada[16:]
                else:
                    formateada = formateada[:16] + ':' + formateada[16:]
            if len(entrada) >= 19:
                formateada = entrada[:19]
                if int(formateada[17:19]) > 59:
                    formateada = formateada[:17] + '59'
                try:
                    datetime.strptime(formateada, '%d/%m/%Y %H:%M:%S')
                    self.lblValidFecha.configure(text='Formato de fecha correcto.')
                except ValueError:
                    self.lblValidFecha.configure(text='El formato de fecha y hora tiene que ser DD/MM/AAAA HH:MM:SS.')
                    print("Fecha y hora invalida")

            self.fecha_hora_var.set(formateada)
            self.fechaYHora.icursor(self.fechaYHora.index(tk.INSERT) + 1)
            # self.fechaYHora.after(10, lambda: )
        else:
            self.fecha_hora_var.set(entrada)


    def crear_widgets(self):
        locale.setlocale(locale.LC_TIME, 'es_ES')

        self.barraSuperior = tk.Frame(self, bg="#1f2329", height=100)
        self.barraSuperior.pack(side=tk.TOP, fill='x')

        self.menuLateral = tk.Frame(self, bg="#2a3138", width=190)
        self.menuLateral.pack(side=tk.LEFT, fill='x')
        self.menuLateral.pack_forget()

        self.botInicio = tk.Button(self.menuLateral, text="Inicio", font=("Helvetica", 14), bg="#2a3138", fg="gray", width=15, cursor="hand2", command=self.clickInicio)
        self.botInicio.pack(side=tk.TOP)

        self.botDiferido = tk.Button(self.menuLateral, text="Carga diferida", font=("Helvetica", 14), bg="#2a3138", fg="white", width=15, cursor="hand2", command=self.clickDiferido)
        self.botDiferido.pack(side=tk.TOP)

        self.botRegistros = tk.Button(self.menuLateral, text="Registros", font=("Helvetica", 14), bg="#2a3138", fg="white", width=15, cursor="hand2", command=self.clickRegistros)
        self.botRegistros.pack(side=tk.TOP)

        self.cuerpoPrincipal = tk.Frame(self, bg="#fff8e6")
        self.cuerpoPrincipal.pack(side=tk.RIGHT, fill='both', expand=True)

        boton = tk.Button(self.barraSuperior, image=self.menu, cursor="hand2", width=32, height=32, command=self.expandir_menu)
        boton.pack(side=tk.LEFT, padx=10)

        self.frameLugar = tk.Frame(self.barraSuperior, bg="#1f2329")
        self.frameLugar.pack(side=tk.LEFT)
        
        self.lblLugar = tk.Label(self.frameLugar, text="Nombre del local:", bg="#1f2329", fg="white", font=("Helvetica", 10))
        self.lblLugar.grid(sticky="W")
        
        self.lugar = tk.Entry(self.frameLugar, width=30, text="Local 1", bg="#fff8e6", fg="black", font=("Helvetica", 10))
        self.lugar.grid(sticky="W")
        self.lugar.insert(0, "Local 1")

        self.frameFecha = tk.Frame(self.barraSuperior, bg="#1f2329")
        self.frameFecha.pack(side=tk.RIGHT)

        self.lblHs = tk.Label(self.frameFecha, text='', bg="#1f2329", fg="white", font=("Helvetica", 30))
        self.lblHs.grid(sticky="W")

        self.lblFecha = tk.Label(self.frameFecha, text='', bg="#1f2329", fg="white", font=("Helvetica", 15))
        self.lblFecha.grid()
        
        self.frameRegistros = tk.Frame(self.cuerpoPrincipal, bg="#fff8e6")
        self.frameRegistros.pack(fill=tk.BOTH, expand=True)


        self.frameDocRegistros = tk.Frame(self.frameRegistros, bg="#fff8e6")
        self.frameDocRegistros.pack(side=tk.TOP, pady=5)

        self.frameBotRegistros = tk.Frame(self.frameRegistros, bg="#fff8e6")
        self.frameBotRegistros.pack(side=tk.TOP, pady=5)

        boton = tk.Button(self.frameBotRegistros, text="Exportar a Excel", cursor="hand2", bg="green", fg="#fff8e6", command=self.exportar_excel)
        boton.grid(row=0, column=0, sticky="W", padx=5)

        boton2 = tk.Button(self.frameBotRegistros, text="Eliminar registros", cursor="hand2", bg="red", fg="#fff8e6", command=self.borrar_registros)
        boton2.grid(row=0, column=1, sticky="W", padx=5)
        
        self.lblDoc3 = tk.Label(self.frameDocRegistros, text="Documento:", bg="#fff8e6", fg="black", font=("Helvetica", 10))
        self.lblDoc3.grid(sticky="W")
        
        vcmd3 = (self.register(self.validate_input), '%P')
        self.documento3 = tk.Entry(self.frameDocRegistros, width=30, bg="#fff8e6", fg="black", font=("Helvetica", 10), state="disabled", validate='key', validatecommand=vcmd3)
        self.documento3.grid(sticky="W")
        self.documento3.bind('<Return>', self.enter)

        self.lblDoc3 = tk.Label(self.frameDocRegistros, text="Presione Enter para fichar.", bg="#fff8e6", fg="#707070", font=("Helvetica", 10))
        self.lblDoc3.grid(sticky="W")

        self.tree = ttk.Treeview(self.frameRegistros, columns=("Agente", "Fecha", "Cruce"), height=self.alto, show='headings')
        self.tree.heading("Agente", text="Agente")
        self.tree.heading("Fecha", text="Fecha")
        self.tree.heading("Cruce", text="Cruce")
        self.tree.column("Agente", anchor="center")
        self.tree.column("Fecha", anchor="center")
        self.tree.column("Cruce", anchor="center", width=50)
        # Crear la Scrollbar vertical
        vsb = ttk.Scrollbar(self.frameRegistros, orient="vertical", command=self.tree.yview)
        vsb.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side='left', fill=tk.BOTH, expand=True)
        self.frameRegistros.pack_forget()
        
        self.frameDatos = tk.Frame(self.cuerpoPrincipal, bg="#fff8e6")
        self.frameDatos.pack(side=tk.TOP, pady=10)
        
        self.lblDoc = tk.Label(self.frameDatos, text="Documento:", bg="#fff8e6", fg="black", font=("Helvetica", 10))
        self.lblDoc.grid(sticky="W")
        
        vcmd = (self.register(self.validate_input), '%P')
        self.documento = tk.Entry(self.frameDatos, width=30, bg="#fff8e6", fg="black", font=("Helvetica", 10), state="disabled", validate='key', validatecommand=vcmd)
        self.documento.grid(sticky="W")
        self.documento.bind('<Return>', self.enter)

        self.lblDoc = tk.Label(self.frameDatos, text="Presione Enter para fichar.", bg="#fff8e6", fg="#707070", font=("Helvetica", 10))
        self.lblDoc.grid(sticky="W")

        self.frameDiferido = tk.Frame(self.cuerpoPrincipal, bg="#fff8e6")
        self.frameDiferido.pack(fill=tk.BOTH, expand=True)

        self.lblDoc2 = tk.Label(self.frameDiferido, text="Documento:", bg="#fff8e6", fg="black", font=("Helvetica", 10))
        self.lblDoc2.grid(sticky="W")
        
        vcmd = (self.register(self.validate_input), '%P')
        self.documento2 = tk.Entry(self.frameDiferido, width=30, bg="#fff8e6", fg="black", font=("Helvetica", 10), state="disabled", validate='key', validatecommand=vcmd)
        self.documento2.grid(sticky="W")
        self.documento2.bind('<Return>', self.enter)

        self.lblDoc2 = tk.Label(self.frameDiferido, text="Presione Enter para fichar.", bg="#fff8e6", fg="#707070", font=("Helvetica", 10))
        self.lblDoc2.grid(sticky="W")
        
        self.lblCruce = tk.Label(self.frameDiferido, text="Cruce:", bg="#fff8e6", fg="black", font=("Helvetica", 10))
        self.lblCruce.grid(sticky="W")
        
        # Crear un estilo personalizado
        style = ttk.Style()
        style.theme_use('default')
        # Configurar el estilo del Combobox
        style.configure("TCombobox",
                        fieldbackground="#fff8e6",  # Color de fondo del campo
                        background="#fff8e6",       # Color de fondo del desplegable
                        foreground="black",         # Color de la letra
                        selectbackground="#fff8e6", # Color de fondo de la selección
                        selectforeground="black")
        self.cruce = ttk.Combobox(self.frameDiferido, width=33, style="TCombobox")
        self.cruce['values'] = ("ENTRADA", "SALIDA")
        self.cruce.current(0) 
        self.cruce.grid(sticky="W")

        self.lblFechaHora = tk.Label(self.frameDiferido, text="Fecha y hora:", bg="#fff8e6", fg="black", font=("Helvetica", 10))
        self.lblFechaHora.grid(sticky="W")

        self.fecha_hora_var = tk.StringVar()
        # self.fecha_hora_var.trace_add('write', self.validar_fecha_hora)
        self.fechaYHora = tk.Entry(self.frameDiferido, width=30, bg="#fff8e6", fg="black", font=("Helvetica", 10), textvariable=self.fecha_hora_var)
        self.fechaYHora.grid(sticky="W")
        self.fechaYHora.bind('<KeyRelease>', self.validar_fecha_hora)

        self.lblValidFecha = tk.Label(self.frameDiferido, text="El formato de fecha y hora tiene que ser DD/MM/AAAA HH:MM:SS.", bg="#fff8e6", fg="#707070", font=("Helvetica", 7))
        self.lblValidFecha.grid(sticky="W")
        
        self.lblObservacion = tk.Label(self.frameDiferido, text="Observación:", bg="#fff8e6", fg="black", font=("Helvetica", 10))
        self.lblObservacion.grid(sticky="W")

        self.observacion = tk.Text(self.frameDiferido, height=8, width=35, bg="#fff8e6", fg="black", font=("Helvetica", 10))
        self.observacion.grid(sticky="W")
        self.frameDiferido.pack_forget()
        self.foto = tk.Label(self.frameDatos, image=self.img, width=self.anchoVideo, height=self.altoVideo, borderwidth=2, relief="groove")
        self.foto.grid(sticky="W")

        self.lblFich = tk.Label(self.frameDatos, text="", bg="#fff8e6", fg="#ffffff", font=("Helvetica", 15))
        self.lblFich.grid(pady=5)
    
    def validate_input(self,value):
        # Verificar si el nuevo valor es un número y tiene una longitud máxima de 9 caracteres
        return (value.isdigit() and len(value) <= 9) or (len(value) == 0)
    
    def clickInicio(self):
        self.botInicio.config(fg="gray")
        self.botDiferido.config(fg="white")
        self.botRegistros.config(fg="white")
        self.documento2.delete(0, tk.END)
        self.documento3.delete(0, tk.END)
        self.fechaYHora.delete(0, tk.END)
        self.observacion.delete("1.0", tk.END)
        self.frameDatos.pack(side=tk.TOP, pady=10)
        self.frameRegistros.pack_forget()
        self.frameDiferido.pack_forget()

    def clickDiferido(self):
        self.botInicio.config(fg="white")
        self.botDiferido.config(fg="gray")
        self.botRegistros.config(fg="white")
        self.documento.delete(0, tk.END)
        self.documento3.delete(0, tk.END)
        self.frameDiferido.pack(side=tk.TOP, pady=10)
        self.frameDatos.pack_forget()
        self.frameRegistros.pack_forget()

    def clickRegistros(self):
        self.botInicio.config(fg="white")
        self.botDiferido.config(fg="white")
        self.botRegistros.config(fg="gray")
        self.documento.delete(0, tk.END)
        self.documento2.delete(0, tk.END)
        self.fechaYHora.delete(0, tk.END)
        self.observacion.delete("1.0", tk.END)
        self.frameRegistros.pack(fill=tk.BOTH)
        self.frameDiferido.pack_forget()
        self.frameDatos.pack_forget()
    
    def expandir_menu(self):
        if self.menu_desplegado:
            self.menuLateral.pack_forget()
            self.menu_desplegado = False
        else:
            self.menuLateral.pack(side=tk.LEFT, fill='both', expand=False)
            self.menu_desplegado = True

    def update_clock(self):
        now = time.strftime("%H:%M:%S")
        self.lblHs.configure(text=now)
        fecha_actual = datetime.now().strftime("%A, %d de %B de %Y")
        self.lblFecha.configure(text=fecha_actual)
        self.after(1000, self.update_clock)

    def mensajes(self,txt,color):
        if txt == '':
            self.lblFich.config(text=txt, bg="#fff8e6")
        else:
            self.lblFich.config(text=txt, bg=color)
        
          
    def texto_informativo(self,frame,texto = ''):
        if texto != '':
            cv2.putText(frame, texto, (3, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.80, (0, 0, 0), 2)
        cv2.namedWindow('Reconocimiento facial', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Reconocimiento facial', self.anchoVideo, self.altoVideo)
        cv2.moveWindow('Reconocimiento facial', self.xV, self.yV)
        cv2.imshow('Reconocimiento facial', frame)

    def eliminarNotificacion(self):
        time.sleep(3)
        self.notificacion = True
        self.nueva_ventana.destroy()
        self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
        self.foto.config(image=self.img)

    def notificaciones(self,texto,color):
        if self.notificacion:
            self.notificacion = False
            self.nueva_ventana = tk.Toplevel()
            self.nueva_ventana.title("Notificacion")
            x = (self.winfo_screenwidth() // 2) - (600 // 2)
            # y = (self.winfo_screenheight() // 2) - (40 // 2) - 100
            y = int(self.winfo_screenheight() - (self.winfo_screenheight() * 0.20))
            self.nueva_ventana.geometry(f'{600}x{40}+{x}+{y}')
            self.notPrincipal = tk.Frame(self.nueva_ventana, bg=color)
            self.notPrincipal.pack(side=tk.RIGHT, fill='both', expand=True)
            self.lblNot = tk.Label(self.notPrincipal, text=texto, bg=color, fg="white", font=("Helvetica", 16))
            self.lblNot.pack(side="top", pady=10)
            threading.Thread(target=self.eliminarNotificacion).start()

    def prueba_vida(self, frame):
        if self.okk == 10: return False
        self.validar_vida = 0
        # Detectar objetos
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (320, 320), (0, 0, 0), True, crop=False)
        self.net.setInput(blob)
        self.outs = self.net.forward(self.output_layers)

        for out in self.outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    if self.classes[class_id] == "cell phone" or self.classes[class_id] == "credential" or self.classes[class_id] == "dni":
                        self.okk = 10
                        return False
        if self.okk < 3:
            self.okk = 4
        elif self.okk == 5:
            self.okk = 6
        elif self.okk == 6:
            self.okk = 7
        elif self.okk == 7:
            self.okk = 8
        
    def calidad_imagen(self,frame):
        imagen_gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        laplacian_var = cv2.Laplacian(imagen_gris, cv2.CV_64F).var()
        histograma = cv2.calcHist([imagen_gris], [0], None, [256], [0, 256])
        print(int(np.mean(histograma)),int(laplacian_var))
        if int(np.mean(histograma)) > 100 and int(laplacian_var) < 80:
            self.cara = frame

    def video_molde(self,frame,texto = ''):
        if self.nueva_ventana is None:
            self.nueva_ventana = tk.Toplevel()
            self.nueva_ventana.title("Reconocimiento facial")
            self.nueva_ventana.geometry(f'{self.anchoVideo}x{self.altoVideo}+{self.xV}+{self.y+20}')
            self.foto_rec = tk.Label(self.nueva_ventana, image=self.img, width=self.anchoVideo, height=self.altoVideo, borderwidth=2, relief="groove")
            self.foto_rec.pack(side="top", pady=10)
        if not self.nueva_ventana.winfo_exists():
            self.nueva_ventana = tk.Toplevel()
            self.nueva_ventana.title("Reconocimiento facial")
            self.nueva_ventana.geometry(f'{self.anchoVideo}x{self.altoVideo}+{self.xV}+{self.y}')
            self.foto_rec = tk.Label(self.nueva_ventana, image=self.img, width=self.anchoVideo, height=self.altoVideo, borderwidth=2, relief="groove")
            self.foto_rec.pack(side="top", pady=10)
        if texto != '':
            cv2.putText(frame, texto, (13, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.80, (0, 0, 0), 2)
        # frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if texto != 'Rostro detectado: Desconocido':
            frame = cv2.resize(frame, (self.anchoVideo, self.altoVideo))
        frame_image = Image.fromarray(frame)
        if texto != 'Rostro detectado: Desconocido':
            molde_imagen = Image.open("img/face.png").convert("RGBA")
            molde_imagen = molde_imagen.resize((250, 230), Image.Resampling.LANCZOS)
            frame_image.paste(molde_imagen, (int((self.anchoVideo-250)/2), int((self.altoVideo-280)/2)), molde_imagen) 
        self.img = ImageTk.PhotoImage(frame_image)
        self.foto_rec.config(image=self.img)

    def validar_fichado(self): 
        if self.cargar_video:
            global cap
            self.lblDoc.configure(text='Cargando video..')
            self.lblDoc2.configure(text='Cargando video..')
            self.lblDoc3.configure(text='Cargando video..')
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                self.cargar_video = False
                self.documento.config(state="normal")
                self.lblDoc.configure(text='Presione Enter para fichar.')
                self.documento2.config(state="normal")
                self.lblDoc2.configure(text='Presione Enter para fichar.')
                self.documento3.config(state="normal")
                self.lblDoc3.configure(text='Presione Enter para validar busqueda.')
                print('cargo el video')
                self.documento.focus_set() 
            else:
                self.notificaciones('Ocurrio un error al cargar el video, revise la camara por favor.','#df2626')
        else:
            ret, frame = cap.read()
            if ret:
                if self.okk == 0 or self.okk == 1:
                    # self.texto_informativo(frame)
                    self.video_molde(frame)
                    if self.okk == 0: 
                        self.okk = 1
                    else: 
                        self.okk = 2
                    return self.after(10, self.validar_fichado)

                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    cv2.destroyAllWindows()
                    self.nueva_ventana.destroy()
                    self.pos_cara = 0
                    self.okk = 0
                    self.intentosFacial = 0
                    self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
                    self.foto.config(image=self.img)
                    return False

                encontro_face = 0
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                face_locations = fr.face_locations(cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY))
                for i,(top, right, bottom, left) in enumerate(face_locations):
                    encontro_face = 1
                    if (top > 16 and top < 36) and (right > 96 and right < 116) and (bottom > 68 and bottom < 88) and (left > 45 and left < 65):
                        if self.cara is None: 
                            # guarda el frame en self.cara si la calidad es buena
                            self.calidad_imagen(frame)
                            self.okk = 5
                            self.video_molde(frame)
                        else:
                            self.video_molde(frame,'No se mueva, estamos haciendo el reconocimiento.')
                    else:
                        self.video_molde(frame,'Coloque su cara dentro del marco.')
                if encontro_face < 1:
                    self.video_molde(frame,'Coloque su cara dentro del marco.')
                
                # print(self.okk)
                if (self.intentosFacial >= 3):
                    self.okk = 0
                    self.intentosFacial = 0
                    self.documento.delete(0, tk.END)
                    self.documento2.delete(0, tk.END)
                    self.fechaYHora.delete(0, tk.END)
                    self.observacion.delete("1.0", tk.END)
                    self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
                    self.foto.config(image=self.img)
                    self.nueva_ventana.destroy()
                    self.notificaciones('No encontramos coincidencias con su rostro.','#df2626')
                    cv2.destroyAllWindows()
                elif self.okk == 10:
                    self.okk = 0
                    self.intentosFacial = 0
                    self.documento.delete(0, tk.END)
                    self.documento2.delete(0, tk.END)
                    self.fechaYHora.delete(0, tk.END)
                    self.observacion.delete("1.0", tk.END)
                    self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
                    self.foto.config(image=self.img)
                    self.nueva_ventana.destroy()
                    self.notificaciones('Detectamos un objeto inapropiado, vuelva a intentar.','#df2626')
                    cv2.destroyAllWindows()
                elif self.cara is not None:
                    self.okk = 0

                    if self.foto_api is None or self.foto_api == '':
                        print('Comparando con la misma foto que el video.')
                        foto = self.cara
                    else:
                        # foto = self.cara
                        foto = fr.load_image_file(BytesIO(self.foto_api))
                    
                    self.cara = cv2.resize(self.cara, (self.anchoVideo, self.altoVideo))
                    face_locations = fr.face_locations(cv2.cvtColor(self.cara, cv2.COLOR_BGR2GRAY))
                    face_encodings = fr.face_encodings(self.cara, face_locations)

                    foto = cv2.resize(foto, (self.anchoVideo, self.altoVideo))
                    # Encontrar los rostros en la imagen
                    face_locations2 = fr.face_locations(cv2.cvtColor(foto, cv2.COLOR_BGR2GRAY))
                    face_encodings2 = fr.face_encodings(foto, face_locations2)
                    # for face_encoding in face_encodings:
                    if len(face_encodings) > 0 and len(face_encodings2) > 0:
                        matches = fr.compare_faces([face_encodings2[0]], face_encodings[0])
                        distance = fr.face_distance([face_encodings2[0]], face_encodings[0])
                        print(f"¿Coincidencia?: {matches[0]}")
                        print(f"Distancia: {distance[0]}")
                        # Si se encuentra una coincidencia 
                        if True in matches:
                            cv2.destroyAllWindows()
                            self.intentosFacial = 0
                            if self.foto_api is None or self.foto_api == '':
                                imagen_pil = Image.fromarray(cv2.cvtColor(foto, cv2.COLOR_BGR2RGB))
                            else:
                                foto = cv2.imdecode(np.frombuffer(self.foto_api, np.uint8), cv2.IMREAD_COLOR)
                                imagen_pil = Image.fromarray(cv2.cvtColor(foto, cv2.COLOR_BGR2RGB))
                            imagen_pil = imagen_pil.resize((self.anchoVideo, self.altoVideo), Image.Resampling.LANCZOS)
                            self.img = ImageTk.PhotoImage(imagen_pil)
                            self.foto.config(image=self.img)
                            documento = self.documento.get() if self.documento.get().strip() != '' else self.documento2.get()
                            # Formatear la fecha y hora como un ID único
                            id = datetime.now().strftime('%Y%m%d%H%M')
                            path = f'img/log/{id}_{documento}.png'
                            if not os.path.exists(os.path.dirname(path)): os.makedirs(os.path.dirname(path))
                            cv2.imwrite(path, cv2.resize(self.cara, (self.anchoVideo, self.altoVideo)))
                            self.documento.delete(0, tk.END)
                            self.documento2.delete(0, tk.END)
                            self.fechaYHora.delete(0, tk.END)
                            self.observacion.delete("1.0", tk.END)
                            self.nueva_ventana.destroy()
                            self.notificaciones(f'Fichado correctamente.','#35c82b')
                            self.cara = None

                            if self.documento3.get().strip() != '':
                                if self.api != '':
                                    self.traer_registros(self.documento3.get().strip())
                                else:
                                    print('Cargar registros.')
                            else:
                                if self.api != '':
                                    self.insertar_registro(documento, path)
                                else:
                                    print('Registrado correctamente.')                                    
                        else:
                            self.intentosFacial = self.intentosFacial + 1
                            texto = "Rostro detectado: Desconocido"
                            self.video_molde(self.cara,texto)
                            print(f"Rostro detectado: Desconocido intentos: {self.intentosFacial}")
                            # return self.after(10, self.validar_fichado)
                else:
                    return self.after(10, self.validar_fichado)
            else:
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    self.cargar_video = False
                    self.documento.config(state="normal")
                    self.lblDoc.configure(text='Presione Enter para fichar.')
                    print('cargo el video')
                    self.documento.focus_set() 
                else:
                    self.notificaciones('Ocurrio un error al cargar el video, revise la camara por favor.','#df2626')

    def enter(self, event=None):
        documento = self.documento.get() if self.documento.get().strip() != '' else self.documento2.get()
        documento = self.documento3.get() if self.documento3.get().strip() != '' else documento
        error = 0
        self.foto_api = ''
        self.intentosFacial = 0
        if documento.strip() == '':
            self.documento.delete(0, tk.END)
            self.documento2.delete(0, tk.END)
            self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
            self.foto.config(image=self.img)
            return self.notificaciones('Ingrese el numero de documento.','#df2626')
        else:
            if self.documento2.get().strip() != '':
                if self.cruce.get().strip() != 'ENTRADA' and self.cruce.get().strip() != 'SALIDA':
                    error = 1
                    return self.notificaciones('El cruce tiene que ser ENTRADA o SALIDA.','#df2626')
                elif self.observacion.get("1.0", tk.END).strip() == '':
                    error = 1
                    return self.notificaciones('Debe poner una observación sobre el fichado.','#df2626')

                if error == 0:
                    try:
                        datetime.strptime(self.fechaYHora.get(), '%d/%m/%Y %H:%M:%S')
                        self.lblValidFecha.configure(text='Formato de fecha correcto.')
                    except ValueError:
                        error = 1
                        self.lblValidFecha.configure(text='El formato de fecha y hora tiene que ser DD/MM/AAAA HH:MM:SS.')
                        return self.notificaciones('El formato de la fecha debe ser DD/MM/AAAA HH:MM:SS.','#df2626')
            
            if error == 0:
                if self.api == '':
                    return self.validar_fichado()

                data = {
                    'tipo': 'VALIDAR AGENTE',
                    'documento': documento
                }
                # return self.validar_fichado()

                # self.verificar_api()
                try:
                    response = requests.post(self.api, data=data)
                    if response.status_code == 200:
                        if response.json()['status'] == 'error':
                            if self.documento3.get().strip() == '':
                                respuesta = messagebox.askyesno("Confirmar", f"El agente {documento} no esta registrado ¿Desea registrar este agente?")
                                if respuesta:
                                    self.nombre_agente = simpledialog.askstring("Registrar Agente", "Ingrese el nombre del agente:")
                                    if self.nombre_agente:
                                        print(f"Registrando agente {self.nombre_agente} con documento {documento}")
                                        time.sleep(3)
                                        return self.validar_fichado()
                                    else:
                                        messagebox.showwarning("Advertencia", "Debe ingresar un nombre para registrar al agente.")
                            else:
                                return self.notificaciones('El agente no existe en la base de datos.','#df2626')
                        else:
                            if response.json()['data'][0]['foto'] != '':
                                # with open(f'img/tmp/{documento}.png', 'wb') as f:
                                #     f.write(base64.b64decode(response.json()['data'][0]['foto']))
                                #     self.foto_api = f'img/tmp/{documento}.png'
                                self.foto_api = base64.b64decode(response.json()['data'][0]['foto'])
                            return self.validar_fichado()
                    else:
                        messagebox.showerror("Error de sistema", f"Error al intentar conectar con la API, intente mas tarde. Resp:{response.status_code}")
                except requests.exceptions.RequestException as e:
                    messagebox.showerror("Error de sistema", "Error al intentar conectar con la API, intente mas tarde.")


    def __del__(self):
        if cap:
            cap.release()

if __name__ == "__main__":
    app2 = VentanaPrincipal()
    app2.mainloop()

