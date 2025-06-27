import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
from io import BytesIO
import cv2 # opencv-python==4.9.0.80
import numpy as np # numpy==1.26.3
import face_recognition as fr # dlib-19.24.99-cp312-cp312-win_amd64.whl luego install face_recognition
import os
import time
from datetime import datetime
import locale
import threading
import requests
import base64
import configparser
import uuid

# Crear entorno virtualenv -p python3 mientorno
# PARA EXE: pyinstaller --onefile --windowed --add-data "libs/shape_predictor_68_face_landmarks.dat;face_recognition_models/models" --add-data "libs/dlib_face_recognition_resnet_model_v1.dat;face_recognition_models/models" --add-data "libs/shape_predictor_5_face_landmarks.dat;face_recognition_models/models" --add-data "libs/mmod_human_face_detector.dat;face_recognition_models/models" main.py
# ejecutar para actualizar dependencias  pip install --upgrade setuptools
class VentanaPrincipal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fichador facial 3.0")
        self.ancho = 780
        self.alto = 580
        self.x = (self.winfo_screenwidth() // 2) - (self.ancho // 2)
        self.y = (self.winfo_screenheight() // 2) - (self.alto // 2) - 60
        self.geometry(f'{self.ancho}x{self.alto}+{self.x}+{self.y}')
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
        self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
        self.menu = ImageTk.PhotoImage(file="img/menu.png")
        self.crear_widgets()
        self.imgFrame = None
        self.menu_desplegado = False
        if os.path.exists('config.ini'):
            config = configparser.ConfigParser()
            config.read('config.ini')
            self.api = config['CONFIG']['API_URL']
        else:
            self.api = ''
        self.foto_api = None
        self.nombre_agente = ''
        self.verificar_api()
        self.predictor = ''
        self.validar_vida = 0
        self.nueva_ventana = None
        self.okk = 0
        self.nombre_local = 'Local 1'
        self.mensaje_api = ''
        self.update_clock()
        threading.Thread(target=self.agregar_dispositivo).start()
        self.animar_texto()
        threading.Thread(target=self.validar_fichado).start()

    def agregar_dispositivo(self):
        try:
            self.mensaje_api = ''
            mac = uuid.getnode()
            if mac != '':
                data = {
                    'tipo': 'AGREGAR_DISPOSITIVO',
                    'dispositivo': mac
                }
                response = requests.post(self.api, data=data)
                print(response.json())
                if response.json()['status'] == 'success':
                    self.nombre_local = response.json()['local']
                    self.mensaje_api = response.json()['mensaje']
                else:
                    print('Error al intentar conectar con la API, intente mas tarde.')
            else:
                print('Error al intentar conectar con la API, intente mas tarde.')
        except requests.exceptions.RequestException as e:
            print('Error al intentar conectar con la API, intente mas tarde.')
        
        self.nom_dispositivo.configure(text=f'Dispositivo: {mac}')        
        self.TituloLugar.configure(text=f'Bienvenido a {self.nombre_local}')
        return self.after(60000, self.agregar_dispositivo)
            
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

    def insertar_registro(self, documento, archivo):
        cruce = ''
        observacion = ''
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
            'lugar': self.nombre_local.strip(),
            'foto': base64_image
        }
        try:
            response = requests.post(self.api, data=data)
            
            if response.json()['status'] == 'success':
                if 'ENTRADA' in response.json()['message']:
                    self.notificaciones(response.json()['message'],'#35c82b')
                else:    
                    self.notificaciones(response.json()['message'],'#4c91d9')
            elif response.json()['status'] == 'error':
                self.notificaciones(response.json()['message'],'#df2626')
            else:
                self.notificaciones(response.json()['message'],'#df2626')

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error de sistema", "Error al intentar conectar con la API, intente mas tarde.")

        os.remove(archivo)
    
    def animar_texto(self, pos=0):    
        texto = self.mensaje_api
        ancho = 0
        if texto == '':
            self.mensajeAPI.config(bg="#fff8e6")
        else:
            ancho = len(texto)
            self.mensajeAPI.config(bg="#b2f8c4")            
        texto_expandido = texto + "   " + texto
        visible = texto_expandido[pos:pos + ancho]
        self.mensajeAPI.config(text=visible)
        self.after(150, lambda: self.animar_texto((pos + 1) % len(texto_expandido)))

    def crear_widgets(self):
        locale.setlocale(locale.LC_TIME, 'es_ES')

        self.barraSuperior = tk.Frame(self, bg="#1f2329", height=100)
        self.barraSuperior.pack(side=tk.TOP, fill='x')

        self.cuerpoPrincipal = tk.Frame(self, bg="#fff8e6")
        self.cuerpoPrincipal.pack(side=tk.RIGHT, fill='both', expand=True)

        self.nom_dispositivo = tk.Label(self.cuerpoPrincipal, text="")
        self.nom_dispositivo.place(relx=1.0, rely=1.0, anchor='se')
        
        self.frameLugar = tk.Frame(self.barraSuperior, bg="#1f2329")
        self.frameLugar.pack(side=tk.LEFT)
        
        self.TituloLugar = tk.Label(self.frameLugar, text="Bienvenido a SIN NOMBRE", bg="#1f2329", fg="white", font=("Comic Sans MS", 25))
        self.TituloLugar.grid(sticky="W", pady=10)

        self.frameFecha = tk.Frame(self.barraSuperior, bg="#1f2329")
        self.frameFecha.pack(side=tk.RIGHT)

        self.lblHs = tk.Label(self.frameFecha, text='', bg="#1f2329", fg="white", font=("Helvetica", 30))
        self.lblHs.grid(sticky="W")

        self.lblFecha = tk.Label(self.frameFecha, text='', bg="#1f2329", fg="white", font=("Helvetica", 15))
        self.lblFecha.grid()

        self.frameDatos = tk.Frame(self.cuerpoPrincipal, bg="#fff8e6")
        self.frameDatos.pack(side=tk.TOP, pady=10)
        
        self.mensajeAPI = tk.Label(self.frameDatos, text="", bg="#b2f8c4", fg="#707070", anchor="w", font=("Helvetica", 12))
        self.mensajeAPI.grid(sticky="W")

        self.lblDoc = tk.Label(self.frameDatos, text="Documento:", bg="#fff8e6", fg="black", font=("Helvetica", 10))
        self.lblDoc.grid(sticky="W")
        
        vcmd = (self.register(self.validate_input), '%P')
        self.documento = tk.Entry(self.frameDatos, width=30, bg="#fff8e6", fg="black", font=("Helvetica", 10), state="disabled", validate='key', validatecommand=vcmd)
        self.documento.grid(sticky="W")
        self.documento.bind('<Return>', self.enter)

        self.lblDoc = tk.Label(self.frameDatos, text="Presione Enter para fichar.", bg="#fff8e6", fg="#707070", font=("Helvetica", 10))
        self.lblDoc.grid(sticky="W")

        self.foto = tk.Label(self.frameDatos, image=self.img, width=self.anchoVideo, height=self.altoVideo, borderwidth=2, relief="groove")
        self.foto.grid(sticky="W")

    
    def validate_input(self,value):
        # Verificar si el nuevo valor es un número y tiene una longitud máxima de 9 caracteres
        return (value.isdigit() and len(value) <= 9) or (len(value) == 0)

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
        self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
        self.foto.config(image=self.img)

    def notificaciones(self,texto,color):
        if self.notificacion:
            self.notificacion = False
            self.nueva_ventana = tk.Toplevel()
            self.nueva_ventana.title("Notificacion")
            x = (self.winfo_screenwidth() // 2) - (600 // 2)
            # y = (self.winfo_screenheight() // 2) - (40 // 2) - 100
            y = int(self.winfo_screenheight() - (self.winfo_screenheight() * 0.30))
            self.nueva_ventana.geometry(f'{600}x{60}+{x}+{y}')
            self.notPrincipal = tk.Frame(self.nueva_ventana, bg=color)
            self.notPrincipal.pack(side=tk.RIGHT, fill='both', expand=True)
            self.lblNot = tk.Label(self.notPrincipal, text=texto, bg=color, fg="white", font=("Helvetica", 20))
            self.lblNot.pack(side="top", pady=10)
            threading.Thread(target=self.eliminarNotificacion).start()
     
    def calidad_imagen(self,frame):
        imagen_gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        laplacian_var = cv2.Laplacian(imagen_gris, cv2.CV_64F).var()
        histograma = cv2.calcHist([imagen_gris], [0], None, [256], [0, 256])
        if int(np.mean(histograma)) > 100 and int(laplacian_var) > 50:
            self.cara = frame

    def video_molde(self,frame,texto = ''):
        # invierte la imagen
        frame = cv2.flip(frame, 1)
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
        frame = cv2.resize(frame, (self.anchoVideo, self.altoVideo))
        frame_image = Image.fromarray(frame)
        molde_imagen = Image.open("img/face.png").convert("RGBA")
        molde_imagen = molde_imagen.resize((250, 230), Image.Resampling.LANCZOS)
        frame_image.paste(molde_imagen, (int((self.anchoVideo-250)/2), int((self.altoVideo-280)/2)), molde_imagen) 
        self.imgFrame = ImageTk.PhotoImage(frame_image)
        self.foto_rec.config(image=self.imgFrame)

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
            ret, frame = cap.read()
            if ret:
                if self.okk == 0 or self.okk == 1:
                    self.video_molde(frame)
                    if self.okk == 0: 
                        self.okk = 1
                    else: 
                        self.okk = 2
                    return self.after(10, self.validar_fichado)

                key = cv2.waitKey(1) & 0xFF
                if key == 27 or not self.nueva_ventana.winfo_exists():
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
                            # self.cara = frame
                            self.okk = 5
                            self.video_molde(frame)
                        else:
                            self.video_molde(frame,'Estamos haciendo el reconocimiento.')
                    else:
                        self.video_molde(frame,'Coloque su cara dentro del marco.')
                if encontro_face < 1:
                    self.video_molde(frame,'Coloque su cara dentro del marco.')
                
                # print(self.okk)
                if (self.intentosFacial >= 3):
                    self.okk = 0
                    self.intentosFacial = 0
                    self.documento.delete(0, tk.END)
                    self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
                    self.foto.config(image=self.img)
                    self.nueva_ventana.destroy()
                    self.notificaciones('No encontramos coincidencias con su rostro.','#df2626')
                    cv2.destroyAllWindows()
                elif self.okk == 10:
                    self.okk = 0
                    self.intentosFacial = 0
                    self.documento.delete(0, tk.END)
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
                        decodFoto = BytesIO(self.foto_api)
                        foto = fr.load_image_file(decodFoto)

                    # self.cara = cv2.resize(self.cara, (self.anchoVideo, self.altoVideo))
                    face_locations = fr.face_locations(cv2.cvtColor(self.cara, cv2.COLOR_BGR2GRAY))
                    face_encodings = fr.face_encodings(self.cara, face_locations)

                    # foto = cv2.resize(foto, (self.anchoVideo, self.altoVideo))
                    # Encontrar los rostros en la imagen
                    face_locations2 = fr.face_locations(cv2.cvtColor(foto, cv2.COLOR_BGR2GRAY))
                    face_encodings2 = fr.face_encodings(foto, face_locations2)
                    # for face_encoding in face_encodings:
                    if len(face_encodings) > 0 and len(face_encodings2) > 0:
                        matches = fr.compare_faces([face_encodings2[0]], face_encodings[0])
                        # distance = fr.face_distance([face_encodings2[0]], face_encodings[0])
                        # Si se encuentra una coincidencia 
                        if True in matches:
                            cv2.destroyAllWindows()
                            self.intentosFacial = 0
                            if self.foto_api is None or self.foto_api == '':
                                imagen_pil = Image.fromarray(cv2.cvtColor(foto, cv2.COLOR_BGR2RGB))
                                imagen_pil = imagen_pil.resize((self.anchoVideo, self.altoVideo), Image.Resampling.LANCZOS)
                                self.img = ImageTk.PhotoImage(imagen_pil)
                                self.foto.config(image=self.img)
                                imagen_pil.close()
                            else:
                                imagen_pil = Image.open(decodFoto)
                                imagen_pil = imagen_pil.resize((self.anchoVideo, self.altoVideo), Image.Resampling.LANCZOS)
                                self.img = ImageTk.PhotoImage(imagen_pil)
                                self.foto.config(image=self.img)
                                imagen_pil.close()
                                decodFoto.close()
                            documento = self.documento.get()

                            self.nueva_ventana.destroy()

                            id = datetime.now().strftime('%Y%m%d%H%M')
                            path = f'img/log/{id}_{documento}.png'
                            if not os.path.exists(os.path.dirname(path)): os.makedirs(os.path.dirname(path))
                            cv2.imwrite(path, cv2.resize(self.cara, (self.anchoVideo, self.altoVideo)))
                            self.cara = None
                            if self.api != '':
                                self.insertar_registro(documento, path)
                            else:
                                print('Registrado correctamente.')             
                            self.documento.delete(0, tk.END)
                        else:
                            self.intentosFacial = self.intentosFacial + 1
                            if self.intentosFacial == 1:
                                texto = f"Rostro desconocido {self.intentosFacial} intento."
                            else:
                                texto = f"Rostro desconocido {self.intentosFacial} intentos."
                            self.video_molde(self.cara,texto)
                            print(f"Rostro detectado: Desconocido intentos: {self.intentosFacial}")
                            return self.after(60, self.validar_fichado)
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
        documento = self.documento.get()
        self.foto_api = None
        self.cara = None
        self.intentosFacial = 0
        if documento.strip() == '':
            self.documento.delete(0, tk.END)
            self.img = ImageTk.PhotoImage(Image.open("img/foto.jpeg"))
            self.foto.config(image=self.img)
            return self.notificaciones('Ingrese el numero de documento.','#df2626')
        else:
            if self.api == '':
                return self.validar_fichado()

        data = {
            'tipo': 'VALIDAR AGENTE',
            'documento': documento
        }

        try:
            response = requests.post(self.api, data=data)
            if response.status_code == 200:
                if response.json()['status'] == 'error':
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
                    if response.json()['data'][0]['foto'] != '':
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

