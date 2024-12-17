import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2 # opencv-python==4.9.0.80
import numpy as np # numpy==1.26.3
import face_recognition as fr # dlib-19.24.99-cp312-cp312-win_amd64.whl luego install face_recognition
import dlib
import os
import time
from datetime import datetime, timedelta
import locale
import sqlite3
import threading
import math
import pymysql
from pymysql.err import OperationalError, ProgrammingError
import io
import pandas as pd

# PARA EXE: pyinstaller --onefile --windowed --add-data "shape_predictor_68_face_landmarks.dat;face_recognition_models/models" --add-data "dlib_face_recognition_resnet_model_v1.dat;face_recognition_models/models" --add-data "shape_predictor_5_face_landmarks.dat;face_recognition_models/models" --add-data "mmod_human_face_detector.dat;face_recognition_models/models" main.py
# ejecutar para actualizar dependencias  pip install --upgrade setuptools
class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fichador facial 1.3")
        self.ancho = 780
        self.alto = 480
        self.anchoVideo = 620
        self.altoVideo = 380
        self.anchoFich = 320
        self.altoFich = 260
        self.intentosFacial = 0
        self.notificacion = True
        self.cargar_video = True
        self.cara = ''
        self.xV = (self.winfo_screenwidth() // 2) - (self.anchoVideo // 2)
        self.yV = (self.winfo_screenheight() // 2) - (self.altoVideo // 2) - 100
        # Coordenadas para centrar app
        self.x = (self.winfo_screenwidth() // 2) - (self.ancho // 2)
        self.y = (self.winfo_screenheight() // 2) - (self.alto // 2) - 100
        self.geometry(f'{self.ancho}x{self.alto}+{self.x}+{self.y}')
        # Cargar el archivo de imagen desde el disco
        icono = tk.PhotoImage(file="img/ico.png")
        # Establecerlo como ícono de la ventana
        self.iconphoto(True, icono)
        # PARA CUANDO ES DE PRUEBA
        id = datetime.now().strftime('%Y')
        if id != '2024':
            quit()
        self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
        self.menu = ImageTk.PhotoImage(file="img/menu.png")
        # Cargar el modelo preentrenado (por ejemplo, un modelo YOLO)
        self.net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
        layer_names = self.net.getLayerNames()
        self.output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]
        self.outs = None
        # Cargar las clases
        with open("coco.names", "r") as f:
            self.classes = [line.strip() for line in f.readlines()]

        self.menu_desplegado = False
        
        # self.detector = dlib.get_frontal_face_detector()
        self.predictor = ''
        threading.Thread(target=self.cargar_lib).start()

        self.giro_cara = 0
        self.okk = 0
        self.crear_widgets()
        self.update_clock()
        self.conn_bdd()
        threading.Thread(target=self.registros).start()
        threading.Thread(target=self.agentes).start()
        threading.Thread(target=self.validar_fichado).start()

    def cargar_lib(self):
        self.predictor = dlib.shape_predictor('face_recognition/shape_predictor_68_face_landmarks.dat')

    def conn_bdd(self):
        # Conectar a la base de datos (o crearla si no existe)
        conn = sqlite3.connect('registros.db')
        # Crear un cursor
        cursor = conn.cursor()
        # Crear la tabla de registros si no existe
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agente TEXT NOT NULL,
            cruce TEXT NOT NULL,
            fecha DATETIME NOT NULL
        )''')
        conn.commit()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS agentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agente TEXT NOT NULL,
            fecha DATETIME NOT NULL,
            foto BLOB NOT NULL
        )''')
        conn.commit()
        conn.close()

    def insertar_registro(self, agente, archivo):
        conn = sqlite3.connect('registros.db')
        cursor = conn.cursor()
        
        cursor.execute("""SELECT * FROM agentes
        WHERE agente = ?""", (agente,))
        resp = cursor.fetchall()
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cruce = self.cruce(agente, fecha)
        if not resp:
            respuesta = messagebox.askyesno("Confirmar", f"El agente {agente} no esta registrado ¿Desea registrar este agente?")
            if respuesta:
                with open(archivo, 'rb') as file:
                    blob_data = file.read()
                cursor.execute('''INSERT INTO agentes (agente, fecha, foto)
                VALUES (?, ?, ?)''', (agente, fecha, blob_data))
            else:
                return '',''

        cursor.execute('''INSERT INTO registros (agente, cruce, fecha)
        VALUES (?, ?, ?)''', (agente, cruce, fecha))

        conn.commit()
        conn.close()
        return fecha,cruce
    
    def exportar_excel(self):
        rows = []
        for row_id in self.tree.get_children():
            row = self.tree.item(row_id)['values']
            rows.append(row)

        df = pd.DataFrame(rows, columns=("Agente", "Fecha", "Cruce", "Horas"))
        fecha = datetime.now().strftime('%Y%m%d%H%M')
        archivo = f"registros_{fecha}.xlsx"
        df.to_excel(archivo, index=False)
        os.startfile(archivo)
        self.notificaciones(f'Exportado correctamente {archivo}','#35c82b')


    def dos_minutos(self, agente, fecha):
        conn = sqlite3.connect('registros.db')
        cursor = conn.cursor()

        cursor.execute("""SELECT fecha FROM registros
        WHERE agente = ? ORDER BY fecha DESC LIMIT 1""", (agente,))

        resp = cursor.fetchall()
        conn.close()

        if not resp:
            return False
        else:
            # Convertir las cadenas de texto a objetos datetime
            fecha1 = datetime.strptime(resp[0][0], "%Y-%m-%d %H:%M:%S")
            fecha2 = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S")
            # Calcular la diferencia entre las dos fechas
            diferencia = fecha2 - fecha1
            # Verificar si la diferencia es de 2 minutos o menos
            if diferencia <= timedelta(minutes=1):
                return True
            else:
                return False
    
    def cruce(self, agente, fecha):
        conn = sqlite3.connect('registros.db')
        cursor = conn.cursor()

        cursor.execute("""SELECT agente, cruce, fecha FROM registros
        WHERE fecha >= datetime(?, '-15 hours') AND agente = ? ORDER BY fecha DESC""", (fecha,agente))
        
        registro = cursor.fetchall()
        conn.close()

        if not registro:
            cruce = 'ENTRADA'
        elif registro[0][1] == 'ENTRADA':
            cruce = 'SALIDA'
        else:
            cruce = 'ENTRADA'
        
        return cruce
    
    def registros(self):
        conn = sqlite3.connect('registros.db')
        cursor = conn.cursor()

        cursor.execute("""WITH registros_ordenados AS (SELECT agente, fecha,
                LAG(fecha) OVER (PARTITION BY agente ORDER BY fecha) AS fecha_anterior, cruce
            FROM registros WHERE fecha >= DATE('now', '-2 months')),
        horas_trabajadas AS (SELECT agente, 
                SUM(CASE WHEN cruce = 'SALIDA' THEN (julianday(fecha) - julianday(fecha_anterior)) * 24 * 60 
                    ELSE 0 END) AS minutos_trabajados
            FROM registros_ordenados WHERE cruce = 'SALIDA' GROUP BY agente)
        SELECT agente, strftime('%d/%m/%Y %H:%M:%S', fecha) AS fecha, cruce,
            printf('%02d:%02d', minutos_trabajados / 60, minutos_trabajados % 60) AS horas_trabajadas
        FROM registros_ordenados LEFT JOIN horas_trabajadas USING (agente) ORDER BY fecha DESC""")
        
        registros = cursor.fetchall()
        conn.close()
        for item in self.tree.get_children():
            self.tree.delete(item)

        for registro in registros:
            self.tree.insert("", tk.END, values=registro)

        return registros
    
    def agentes(self):
        conn = sqlite3.connect('registros.db')
        cursor = conn.cursor()

        cursor.execute("SELECT id,agente,strftime('%d/%m/%Y %H:%M:%S', fecha) AS fecha,foto FROM agentes order by fecha")
        
        registros = cursor.fetchall()
        conn.close()
        for widget in self.frameAgentes.winfo_children():
            widget.destroy()
        frame_tarjeta = tk.Canvas(self.frameAgentes, height=100)
        frame_tarjeta.pack(padx=5, pady=5, side='top')
        pos = 0
        for registro in registros:
            pos = pos + 1
            if pos == 6:
                frame_tarjeta = ttk.Frame(self.frameAgentes)
                frame_tarjeta.pack(padx=5, pady=5, side='top')
                pos = 0
            
            tarjeta = ttk.Frame(frame_tarjeta, borderwidth=2, relief="groove")
            tarjeta.pack(padx=5, pady=5, side='left')

            if registro[3]:
                foto_agente = Image.open(io.BytesIO(registro[3]))
                foto_agente = foto_agente.resize((80,60), Image.Resampling.LANCZOS)
                foto_agente = ImageTk.PhotoImage(foto_agente)
                etiqueta_imagen = ttk.Label(tarjeta, image=foto_agente)
                etiqueta_imagen.image = foto_agente  
                etiqueta_imagen.pack(padx=5, pady=5)
            etiqueta_dni = ttk.Label(tarjeta, text=registro[1])
            etiqueta_dni.pack(padx=5, pady=5)
            boton_eliminar = ttk.Button(tarjeta, text="Eliminar", cursor="hand2", command=lambda id=registro[0]: self.eliminar_agente(id))
            boton_eliminar.pack(padx=5, pady=5)

        return registros
    
    def eliminar_agente(self,id):
        conn = sqlite3.connect('registros.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM agentes WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        self.agentes()
        print(f"Agente {id} eliminado")

    def crear_widgets(self):
        locale.setlocale(locale.LC_TIME, 'es_ES')

        self.barraSuperior = tk.Frame(self, bg="#1f2329", height=100)
        self.barraSuperior.pack(side=tk.TOP, fill='x')

        self.menuLateral = tk.Frame(self, bg="#2a3138", width=190)
        self.menuLateral.pack(side=tk.LEFT, fill='x')
        self.menuLateral.pack_forget()

        self.botInicio = tk.Button(self.menuLateral, text="Inicio", font=("Helvetica", 14), bg="#2a3138", fg="gray", width=15, cursor="hand2", command=self.clickInicio)
        self.botInicio.pack(side=tk.TOP)

        self.botAgentes = tk.Button(self.menuLateral, text="Agentes", font=("Helvetica", 14), bg="#2a3138", fg="white", width=15, cursor="hand2", command=self.clickAgentes)
        self.botAgentes.pack(side=tk.TOP)
        
        self.botRegistros = tk.Button(self.menuLateral, text="Registros", font=("Helvetica", 14), bg="#2a3138", fg="white", width=15, cursor="hand2", command=self.clickRegistros)
        self.botRegistros.pack(side=tk.TOP)

        self.cuerpoPrincipal = tk.Frame(self, bg="#fff8e6")
        self.cuerpoPrincipal.pack(side=tk.RIGHT, fill='both', expand=True)

        boton = tk.Button(self.barraSuperior, image=self.menu, cursor="hand2", width=32, height=32, command=self.expandir_menu)
        boton.pack(side=tk.LEFT, padx=10)

        self.frameFecha = tk.Frame(self.barraSuperior, bg="#1f2329")
        self.frameFecha.pack(side=tk.RIGHT)

        self.lblHs = tk.Label(self.frameFecha, text='', bg="#1f2329", fg="white", font=("Helvetica", 30))
        self.lblHs.grid(sticky="W")

        self.lblFecha = tk.Label(self.frameFecha, text='', bg="#1f2329", fg="white", font=("Helvetica", 15))
        self.lblFecha.grid()

        
        self.frameRegistros = tk.Frame(self.cuerpoPrincipal, bg="#fff8e6")
        self.frameRegistros.pack(fill=tk.BOTH, expand=True)
        boton = tk.Button(self.frameRegistros, text="Exportar a Excel", cursor="hand2", bg="green", fg="#fff8e6", command=self.exportar_excel)
        boton.pack(side=tk.TOP, anchor='n')
        self.tree = ttk.Treeview(self.frameRegistros, columns=("Agente", "Fecha", "Cruce", "Horas"), height=self.alto, show='headings')
        self.tree.heading("Agente", text="Agente")
        self.tree.heading("Fecha", text="Fecha")
        self.tree.heading("Cruce", text="Cruce")
        self.tree.heading("Horas", text="Horas")
        self.tree.column("Agente", anchor="center")
        self.tree.column("Fecha", anchor="center")
        self.tree.column("Cruce", anchor="center", width=50)
        self.tree.column("Horas", anchor="center", width=10)
        # Crear la Scrollbar vertical
        vsb = ttk.Scrollbar(self.frameRegistros, orient="vertical", command=self.tree.yview)
        vsb.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side='left', fill=tk.BOTH, expand=True)
        self.frameRegistros.pack_forget()
        
        self.frameAgentes = tk.Frame(self.cuerpoPrincipal, bg="#fff8e6")
        self.frameAgentes.pack(fill=tk.BOTH)

        self.frameAgentes.pack_forget()

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
        
        self.foto = tk.Label(self.frameDatos, image=self.img, width=self.anchoFich, height=self.altoFich, borderwidth=2, relief="groove")
        self.foto.grid(sticky="W")

        self.lblFich = tk.Label(self.frameDatos, text="", bg="#fff8e6", fg="#ffffff", font=("Helvetica", 15))
        self.lblFich.grid(pady=5)
    
    def validate_input(self,value):
        # Verificar si el nuevo valor es un número y tiene una longitud máxima de 9 caracteres
        return (value.isdigit() and len(value) <= 9) or (len(value) == 0)
    
    def clickInicio(self):
        self.botInicio.config(fg="gray")
        self.botAgentes.config(fg="white")
        self.botRegistros.config(fg="white")
        self.frameDatos.pack(side=tk.TOP, pady=10)
        self.frameRegistros.pack_forget()
        self.frameAgentes.pack_forget()

    def clickRegistros(self):
        self.botInicio.config(fg="white")
        self.botAgentes.config(fg="white")
        self.botRegistros.config(fg="gray")
        self.frameRegistros.pack(fill=tk.BOTH)
        self.frameDatos.pack_forget()
        self.frameAgentes.pack_forget()
    
    def clickAgentes(self):
        self.botInicio.config(fg="white")
        self.botAgentes.config(fg="gray")
        self.botRegistros.config(fg="white")
        self.frameAgentes.pack(fill=tk.BOTH, expand=True)
        self.frameDatos.pack_forget()
        self.frameRegistros.pack_forget()

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

    def foto_agente(self,documento):
        conn = sqlite3.connect('registros.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("""SELECT foto FROM agentes
            WHERE agente = ?""", (documento,))
            resp = cursor.fetchone()
            conn.close()
            if resp is not None:
                time.sleep(1)
                imagen_bytes = np.frombuffer(resp[0], dtype=np.uint8)
                imagen = cv2.imdecode(imagen_bytes, cv2.IMREAD_COLOR)
                if imagen is None:
                    return None
            else:
                return None

            return imagen
        except Exception as e:
            print('Error',e)
            return None
        
    def texto_informativo(self,frame,texto):
        cv2.putText(frame, texto, (3, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.80, (0, 0, 0), 2)
        # cv2.namedWindow('Reconocimiento facial', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Reconocimiento facial', self.anchoVideo, self.altoVideo)
        cv2.moveWindow('Reconocimiento facial', self.xV, self.yV)
        cv2.imshow('Reconocimiento facial', frame)

    def eliminarNotificacion(self):
        time.sleep(3)
        self.notificacion = True
        self.nueva_ventana.destroy()

    def notificaciones(self,texto,color):
        if self.notificacion:
            self.notificacion = False
        else:
            self.notificacion = True
            self.nueva_ventana.destroy()

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

    def prueba_vida(self,frame,rect):
        # Detectar objetos
        # blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (320, 320), (0, 0, 0), True, crop=False)
        self.net.setInput(blob)
        self.outs = self.net.forward(self.output_layers)
        # Mostrar información en la pantalla
        for out in self.outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                # confidence = scores[class_id]
                # if confidence > 0.5 and self.classes[class_id] == "cell phone":
                if self.classes[class_id] == "cell phone":
                    self.okk = 10
                # else:
                #     if self.giro_cara > 20:
                #         print(self.giro_cara)
                #         self.okk = 2
                #     else:
                #         self.giro_cara = self.giro_cara + 1

        if self.okk != 10:
            shape = self.predictor(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), rect)
            # distancia entre nariz y oreja izquierda
            distancia = math.sqrt((shape.part(33).x - shape.part(16).x) ** 2 + (shape.part(33).y - shape.part(16).y) ** 2)
            if self.giro_cara == 0: 
                self.giro_cara = distancia
            else:
                self.texto_informativo(frame,'Gire la cara hacia la izquierda por favor..')
            if distancia < (self.giro_cara - 20): # giro cara a la izquierda
                self.okk = 2
    
    def limpiar_foto(self):
        self.registros()
        self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
        self.foto.config(image=self.img)

    def validar_fichado(self): 
        if self.cargar_video:
            global cap
            self.lblDoc.configure(text='Cargando video..')
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                self.cargar_video = False
                self.documento.config(state="normal")
                self.lblDoc.configure(text='Presione Enter para fichar.')
                print('cargo el video')
                self.documento.focus_set() 
            else:
                self.notificaciones('Ocurrio un error al cargar el video, revise la camara por favor.','#df2626')
        else:
            documento = self.documento.get()   
            ret, frame = cap.read()
            if ret:
                cv2.namedWindow('Reconocimiento facial', cv2.WINDOW_NORMAL)
                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    cv2.destroyAllWindows()
                    self.intentosFacial = 0
                    # self.documento.delete(0, tk.END)
                    self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
                    self.foto.config(image=self.img)
                    return False
                face_locations = fr.face_locations(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
                for i,(top, right, bottom, left) in enumerate(face_locations):
                    if (bottom - top) < 130:
                        if self.okk == 0:
                            self.okk = 1
                            self.cara = frame
                        else:
                            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                            # self.prueba_vida(frame,'')
                            threading.Thread(target=self.prueba_vida(frame,dlib.rectangle(left, top, right, bottom))).start()
                        break
                    if self.okk == 1:
                        threading.Thread(target=self.prueba_vida(frame,dlib.rectangle(left, top, right, bottom))).start()
                        # self.prueba_vida(frame,'')
                        break
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

                    if ((bottom - top) > 130) :
                        self.texto_informativo(frame,'Aleje la cara de la camara.')                                              
                else:
                    self.okk = 0
                    self.giro_cara = 0
                    cv2.resizeWindow('Reconocimiento facial', self.anchoVideo, self.altoVideo)
                    cv2.moveWindow('Reconocimiento facial', self.xV, self.yV)
                    cv2.imshow('Reconocimiento facial', frame)

                if (self.intentosFacial > 3):
                    self.intentosFacial = 0
                    self.documento.delete(0, tk.END)
                    self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
                    self.foto.config(image=self.img)
                    self.notificaciones('No encontramos coincidencias con su rostro.','#df2626')
                    cv2.destroyAllWindows()
                elif self.okk == 10:
                    self.okk = 0
                    self.intentosFacial = 0
                    self.documento.delete(0, tk.END)
                    self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
                    self.foto.config(image=self.img)
                    self.notificaciones('Detectamos un objeto inapropiado, vuelva a intentar.','#df2626')
                    cv2.destroyAllWindows()
                elif self.okk == 2:
                    self.okk = 0
                    self.giro_cara = 0
                    foto = self.foto_agente(documento)

                    if foto is None: 
                        print('Comparando con la misma foto que el video.')
                        foto = self.cara

                    face_encodings = fr.face_encodings(self.cara, face_locations)
                    # Encontrar los rostros en la imagen
                    face_locations2 = fr.face_locations(foto)
                    face_encodings2 = fr.face_encodings(foto, face_locations2)
                    # for face_encoding in face_encodings:
                    if len(face_encodings) > 0 and len(face_encodings2) > 0:
                        matches = fr.compare_faces([face_encodings2[0]], face_encodings[0])
                        # Si se encuentra una coincidencia 
                        if True in matches:
                            cv2.destroyAllWindows()
                            self.intentosFacial = 0
                            imagen_pil = Image.fromarray(cv2.cvtColor(foto, cv2.COLOR_BGR2RGB))
                            imagen_pil = imagen_pil.resize((self.anchoFich, self.altoFich), Image.Resampling.LANCZOS)
                            self.img = ImageTk.PhotoImage(imagen_pil)
                            self.foto.config(image=self.img)
                            # Formatear la fecha y hora como un ID único
                            id = datetime.now().strftime('%Y%m%d%H%M')
                            path = f'img/log/{id}_{documento}.png'
                            if not os.path.exists(os.path.dirname(path)): os.makedirs(os.path.dirname(path))
                            cv2.imwrite(path, cv2.resize(self.cara, (self.anchoFich, self.altoFich)))
                            self.documento.delete(0, tk.END) 
                            fecha, cruce = self.insertar_registro(documento, path)
                            if fecha != '' and cruce != '':
                                self.agentes()
                                # self.mensajes("Fichado correctamente.","#35c82b")
                                print(f"Rostro detectado: {documento}")
                                self.notificaciones(f'Fichado correctamente, {cruce} {fecha}','#35c82b')
                                self.registros()
                            self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
                            self.foto.config(image=self.img)
                            # threading.Thread(target=self.limpiar_foto).start()
                        else:
                            self.intentosFacial = self.intentosFacial + 1
                            texto = "Rostro detectado: Desconocido"
                            self.texto_informativo(frame,texto)
                            print(f"Rostro detectado: Desconocido intentos: {self.intentosFacial}")
                            self.after(2, self.validar_fichado)
                else:
                    self.after(10, self.validar_fichado)
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
        documento = self.documento.get()   
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.intentosFacial = 0
        if documento.strip() == '':
            self.documento.delete(0, tk.END)
            self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
            self.foto.config(image=self.img)
            self.notificaciones('Ingrese el numero de documento.','#df2626')
        elif self.dos_minutos(documento, fecha):
            self.documento.delete(0, tk.END)
            self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
            self.foto.config(image=self.img)
            self.notificaciones('Usted acaba de fichar, intente dentro de dos minutos.','#df2626')
        else:
            self.validar_fichado()

    def __del__(self):
        if cap:
            cap.release()

if __name__ == "__main__":
    app2 = VentanaPrincipal()
    app2.mainloop()

