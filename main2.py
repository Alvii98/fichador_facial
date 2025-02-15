import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk # pillow
import cv2 # opencv-python==4.9.0.80
import numpy as np # numpy==1.26.3
import os
import time
from datetime import datetime
import locale
import threading
import pandas as pd # pandas y openpyxl
import sqlite3
import re

# PARA EXE: pyinstaller --onefile --windowed main2.py
# ejecutar para actualizar dependencias  pip install --upgrade setuptools
class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Contador de personas 2.1")
        self.ancho = 880
        self.alto = 580
        self.anchoVideo = 620
        self.altoVideo = 340
        self.intentosFacial = 0
        self.notificacion = True
        self.cargar_video = 0
        self.cara = None
        # Coordenadas para centrar app
        self.x = (self.winfo_screenwidth() // 2) - (self.ancho // 2)
        self.y = (self.winfo_screenheight() // 2) - (self.alto // 2) - 50
        self.geometry(f'{self.ancho}x{self.alto}+{self.x}+{self.y}')
        # Cargar el archivo de imagen desde el disco
        icono = tk.PhotoImage(file="img/ico.png")
        # Establecerlo como ícono de la ventana
        self.iconphoto(True, icono)

        self.img = ImageTk.PhotoImage(Image.open("img/imagen.png"))
        self.menu = ImageTk.PhotoImage(file="img/menu.png")
        self.count = 0
        self.fecha_hora = ''
        self.menu_desplegado = False
        self.crear_widgets()
        # Cargar video mientras inicia el programa
        threading.Thread(target=self.validar_persona).start()
        # Cargar el modelo preentrenado (por ejemplo, un modelo YOLO)
        self.net = None
        self.outs = None
        self.classes = None
        self.insert = 0
        threading.Thread(target=self.cargar_lib).start()
        self.update_clock()
        self.conn_bdd()

    def detect_people(self,frame):
        height, width = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        self.net.setInput(blob)
        outs = self.net.forward(self.output_layers)

        class_ids = []
        confidences = []
        boxes = []

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5 and class_id == 0:  # Clase 0 es 'persona' en COCO dataset
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        return [(boxes[i], confidences[i]) for i in indexes]


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

    def borrar_registros(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def conn_bdd(self):
        # Conectar a la base de datos (o crearla si no existe)
        conn = sqlite3.connect('registros.db')
        # Crear un cursor
        cursor = conn.cursor()
        # Crear la tabla de registros si no existe
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATETIME NOT NULL,
            local TEXT NOT NULL,
            archivo TEXT NOT NULL
        )''')
        conn.commit()

    def insertar_registro(self,archivo):
        conn = sqlite3.connect('registros.db')
        cursor = conn.cursor()
        
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''INSERT INTO registros (fecha, local, archivo)
        VALUES (?, ?, ?)''', (fecha, self.lugar.get(), archivo))

        conn.commit()
        conn.close()

    def registros(self):
        conn = sqlite3.connect('registros.db')
        cursor = conn.cursor()
        try:
            inicio = datetime.strptime(self.fecha.get(), '%d/%m/%Y')
            final = datetime.strptime(self.fecha2.get(), '%d/%m/%Y')
            inicio = f'{inicio.strftime('%Y-%m-%d')} 00:00:10'
            final = f'{final.strftime('%Y-%m-%d')} 23:59:59'
        except ValueError:
            conn.close()    
            return self.notificaciones('Una de las fechas tiene un formato incorrecto.','#df2626')

        cursor.execute("""SELECT strftime('%d/%m/%Y %H:%M', fecha) AS fecha,local,archivo from registros 
                       WHERE fecha >= ? and fecha <= ? ORDER BY fecha DESC""", (inicio,final))
        
        registros = cursor.fetchall()
        conn.close()

        if len(registros) == 0:
            return self.notificaciones('No encontramos registros entre esas fechas.', '#ff0000')
        
        self.lblValidFecha.configure(text=f'Encontramos {len(registros)} registros entre esas fechas.')
        

        for item in self.tree.get_children():
            self.tree.delete(item)


        for registro in registros:
            self.tree.insert("", tk.END, values=registro)
        
        return registros

    def open_image(self, event):
        item = self.tree.selection()[0]
        archivo_path = self.tree.item(item, "values")[2]
        try:
            img = Image.open(archivo_path)
            img.show()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la imagen: {e}")

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
                archivo = f"registros_{fecha}.xlsx"
                df.to_excel(archivo, index=False)
                os.startfile(archivo)
                self.notificaciones(f'Exportado correctamente {archivo}','#35c82b')
        except Exception as e:
            self.notificaciones(f'Ocurrio un error al exportar: {e}', '#ff0000')
    
    def validar_fecha(self, event=None, *args):
        entrada = self.fecha_var.get()
        if event.keysym != 'BackSpace' and event.keysym != 'Left' and event.keysym != 'right':
            self.lblValidFecha.configure(text='El formato de fecha requerido DD/MM/AAAA.')
            formateada = re.sub(r'[^0-9]', '', entrada)
            # Formatear la entrada a DD/MM/YYYY
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
                    formateada = formateada[:6] + str(datetime.now().year)
                else:
                    formateada = formateada[:10]
        
                try:
                    datetime.strptime(formateada, '%d/%m/%Y')
                    self.lblValidFecha.configure(text='Formato de fecha correcto.')
                except ValueError:
                    self.lblValidFecha.configure(text='El formato de fecha requerido DD/MM/AAAA.')
                    print("Fecha y hora invalida")

            self.fecha_var.set(formateada)
            self.fecha.icursor(self.fecha.index(tk.INSERT) + 1)
            # self.fechaYHora.after(10, lambda: )
        else:
            self.fecha_var.set(entrada)
    
    def validar_fecha2(self, event=None, *args):
        entrada = self.fecha_var2.get()
        if event.keysym != 'BackSpace' and event.keysym != 'Left' and event.keysym != 'right':
            self.lblValidFecha.configure(text='El formato de fecha requerido DD/MM/AAAA.')
            formateada = re.sub(r'[^0-9]', '', entrada)
            # Formatear la entrada a DD/MM/YYYY
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
                    formateada = formateada[:6] + str(datetime.now().year)
                else:
                    formateada = formateada[:10]
        
                try:
                    datetime.strptime(formateada, '%d/%m/%Y')
                    self.lblValidFecha.configure(text='Formato de fecha correcto.')
                except ValueError:
                    self.lblValidFecha.configure(text='El formato de fecha requerido DD/MM/AAAA.')
                    print("Fecha y hora invalida")

            self.fecha_var2.set(formateada)
            self.fecha2.icursor(self.fecha2.index(tk.INSERT) + 1)
            # self.fechaYHora.after(10, lambda: )
        else:
            self.fecha_var2.set(entrada)

    def crear_widgets(self):
        locale.setlocale(locale.LC_TIME, 'es_ES')

        self.barraSuperior = tk.Frame(self, bg="#1f2329", height=100)
        self.barraSuperior.pack(side=tk.TOP, fill='x')

        self.menuLateral = tk.Frame(self, bg="#2a3138", width=190)
        self.menuLateral.pack(side=tk.LEFT, fill='x')
        self.menuLateral.pack_forget()

        self.botInicio = tk.Button(self.menuLateral, text="Inicio", font=("Helvetica", 14), bg="#2a3138", fg="gray", width=15, cursor="hand2", command=self.clickInicio)
        self.botInicio.pack(side=tk.TOP)

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
        
        self.frameFechasRegistros = tk.Frame(self.frameRegistros, bg="#fff8e6")
        self.frameFechasRegistros.pack(side=tk.TOP, pady=5)
        
        self.frameFechaRegistros = tk.Frame(self.frameFechasRegistros, bg="#fff8e6")
        self.frameFechaRegistros.grid(row=0, column=0, sticky="W", padx=5)
        
        self.lblFecha1 = tk.Label(self.frameFechaRegistros, text="Fecha inicio:", bg="#fff8e6", fg="black", font=("Helvetica", 10))
        self.lblFecha1.grid(sticky="W")
        
        self.fecha_var = tk.StringVar()
        self.fecha = tk.Entry(self.frameFechaRegistros, width=30, bg="#fff8e6", fg="black", font=("Helvetica", 10), textvariable=self.fecha_var)
        self.fecha.grid(sticky="W")
        self.fecha.bind('<KeyRelease>', self.validar_fecha)

        self.frameFechaRegistros2 = tk.Frame(self.frameFechasRegistros, bg="#fff8e6")
        self.frameFechaRegistros2.grid(row=0, column=1, sticky="W", padx=5)

        self.lblFecha2 = tk.Label(self.frameFechaRegistros2, text="Fecha final:", bg="#fff8e6", fg="black", font=("Helvetica", 10))
        self.lblFecha2.grid(sticky="W")
        
        self.fecha_var2 = tk.StringVar()
        self.fecha2 = tk.Entry(self.frameFechaRegistros2, width=30, bg="#fff8e6", fg="black", font=("Helvetica", 10), textvariable=self.fecha_var2)
        self.fecha2.grid(sticky="W")
        self.fecha2.bind('<KeyRelease>', self.validar_fecha2)

        self.lblValidFecha = tk.Label(self.frameRegistros, text="El formato de fecha requerido DD/MM/AAAA.", bg="#fff8e6", fg="#707070", font=("Helvetica", 7))
        self.lblValidFecha.pack(side=tk.TOP, pady=5)

        self.frameBotRegistros = tk.Frame(self.frameRegistros, bg="#fff8e6")
        self.frameBotRegistros.pack(side=tk.TOP, pady=5)

        boton = tk.Button(self.frameBotRegistros, text="Exportar a Excel", cursor="hand2", bg="green", fg="#fff8e6", command=self.exportar_excel)
        boton.grid(row=0, column=0, sticky="W", padx=5)

        boton = tk.Button(self.frameBotRegistros, text="Buscar", cursor="hand2", bg="blue", fg="#fff8e6", command=self.registros)
        boton.grid(row=0, column=1, sticky="W", padx=5)

        boton2 = tk.Button(self.frameBotRegistros, text="Eliminar registros", cursor="hand2", bg="red", fg="#fff8e6", command=self.borrar_registros)
        boton2.grid(row=0, column=2, sticky="W", padx=5)

        self.tree = ttk.Treeview(self.frameRegistros, columns=("Fecha", "Lugar", "Imagen"), height=self.alto, show='headings')
        self.tree.heading("Fecha", text="Fecha")
        self.tree.heading("Lugar", text="Lugar")
        self.tree.heading("Imagen", text="Imagen")

        # Crear la Scrollbar vertical
        vsb = ttk.Scrollbar(self.frameRegistros, orient="vertical", command=self.tree.yview)
        vsb.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side='left', fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.open_image)

        self.frameRegistros.pack_forget()
        
        self.frameDatos = tk.Frame(self.cuerpoPrincipal, bg="#fff8e6")
        self.frameDatos.pack(fill=tk.BOTH, pady=10)
        
        
        self.lblLinea = tk.Label(self.frameDatos, text="Linea de detección:", bg="#fff8e6", fg="black", font=("Helvetica", 10))
        self.lblLinea.pack(expand=True, anchor="center")

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

        vcmd = (self.register(self.validate_input), '%P')
        self.linea = ttk.Combobox(self.frameDatos, width=33, style="TCombobox", validate='key', validatecommand=vcmd)
        self.linea['values'] = ('10','50','100','150','200','250','300','350','400')
        self.linea.current(4) 
        self.linea.pack(expand=True, anchor="center", pady=10)

        self.frameBotDatos = tk.Frame(self.frameDatos, bg="#fff8e6")
        self.frameBotDatos.pack(expand=True, anchor="center")

        self.botonVideo = tk.Button(self.frameBotDatos, text="Iniciar camara", cursor="hand2", bg="blue", fg="#fff8e6", command=self.validar_persona)
        self.botonVideo.grid(row=0, column=1, sticky="W", padx=10)
        
        self.botonCerrarVideo = tk.Button(self.frameBotDatos, text="Cerrar camara", cursor="hand2", bg="red", fg="#fff8e6", command=self.cerrar_video)
        self.botonCerrarVideo.grid(row=0, column=2, sticky="W", padx=10)

        self.foto = tk.Label(self.frameDatos, image=self.img, width=self.anchoVideo, height=self.altoVideo, borderwidth=2, relief="groove")
        self.foto.pack(expand=True, anchor="center", pady=10)

    def validate_input(self,value):
        # Verificar si el nuevo valor es un número y tiene una longitud máxima de 9 caracteres
        return (value.isdigit() and len(value) <= 9) or (len(value) == 0)
    
    def clickInicio(self):
        self.botInicio.config(fg="gray")
        self.botRegistros.config(fg="white")
        self.frameDatos.pack(side=tk.TOP, pady=10)
        self.frameRegistros.pack_forget()

    def clickRegistros(self):
        self.botInicio.config(fg="white")
        self.botRegistros.config(fg="gray")
        self.frameRegistros.pack(fill=tk.BOTH)
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

    def limpiar_foto(self):
        self.img = ImageTk.PhotoImage(Image.open("img/imagen.png"))
        self.foto.config(image=self.img)

    def cerrar_video(self):
        if self.cargar_video != 0 and self.cargar_video != 1:
            self.cargar_video = 10

    def validar_persona(self): 
        if self.cargar_video == 1:
            self.notificaciones('Se esta cargando el video, espere por favor.','#df2626')
            return False

        if self.cargar_video == 0:
            global cap
            print('Cargando el video')
            self.botonVideo.configure(state="disabled")
            self.cargar_video = 1
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                self.botonVideo.configure(state="normal")
                self.cargar_video = 2
                print('cargo el video')
            else:
                self.botonVideo.configure(state="normal")
                self.cargar_video = 0
                self.notificaciones('Ocurrio un error al cargar el video, revise la camara por favor.','#df2626')
        else:
            ret, frame = cap.read()
            if ret:
                try:
                    self.botonVideo.configure(state="disabled")
                    
                    if self.linea.get() == 0 or self.linea.get() == '': linea_deteccion = '200'
                    else: linea_deteccion = self.linea.get()
                    if self.fecha_hora == '': self.fecha_hora = datetime.now().strftime('%d/%m/%Y %H:%M')
                    if self.insert == 0 or self.insert > 15: 
                        self.insert = 0
                        detections = self.detect_people(frame)
                        for (box, confidence) in detections:
                            x, y, w, h = box
                            # cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            if y < int(linea_deteccion) < y + h:
                                id = datetime.now().strftime('%Y%m%d%H%M')
                                path = f'img/log/{id}_foto.png'
                                if not os.path.exists(os.path.dirname(path)): os.makedirs(os.path.dirname(path))
                                cv2.imwrite(path, cv2.resize(frame, (self.anchoVideo, self.altoVideo)))
                                self.insertar_registro(path)
                                self.insert = 1
                                self.count += 1
                        cv2.line(frame, (0, int(linea_deteccion)), (frame.shape[1], int(linea_deteccion)), (0, 0, 255), 2)
                    else:    
                        self.insert += 1
                        cv2.line(frame, (0, int(linea_deteccion)), (frame.shape[1], int(linea_deteccion)), (0, 255, 0), 2)

                    cv2.putText(frame, f'Cantidad desde {self.fecha_hora}: {self.count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.resize(frame, (self.anchoVideo, self.altoVideo))
                    self.img = ImageTk.PhotoImage(Image.fromarray(frame))
                    self.foto.config(image=self.img)
                    if self.cargar_video == 10:
                        self.cargar_video = 2
                        cv2.destroyAllWindows()
                        self.botonVideo.configure(state="normal")
                        self.img = ImageTk.PhotoImage(Image.open("img/imagen.png"))
                        self.foto.config(image=self.img)
                    else:
                        return self.after(10, self.validar_persona)
                except Exception as e:
                    self.botonVideo.configure(state="normal")
                    cv2.destroyAllWindows()
                    self.img = ImageTk.PhotoImage(Image.open("img/imagen.png"))
                    self.foto.config(image=self.img)
                    print(f"Ocurrió un error: {e}")
            else:
                self.cargar_video = 1
                self.botonVideo.configure(state="disabled")
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    self.botonVideo.configure(state="normal")
                    self.cargar_video = 2
                    print('cargo el video')
                else:
                    self.botonVideo.configure(state="normal")
                    self.cargar_video = 0
                    self.notificaciones('Ocurrio un error al cargar el video, revise la camara por favor.','#df2626')

    def __del__(self):
        if cap:
            cap.release()

if __name__ == "__main__":
    app2 = VentanaPrincipal()
    app2.mainloop()

