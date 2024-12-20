import cv2
import numpy as np

# Cargar el modelo preentrenado (por ejemplo, un modelo YOLO)
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

# Cargar las clases
with open("coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

# Capturar video
cap = cv2.VideoCapture(0)
print('Cargando el video')

if cap.isOpened():
    print('Cargo el video')
else:
    print('Ocurrio un error al cargar el video')

while True:
    ret, frame = cap.read()
    if not ret:
        break

    height, width, channels = frame.shape

    # Detectar objetos
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    # Mostrar información en la pantalla
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5 and classes[class_id] == "cell phone":
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                # Coordenadas del rectángulo
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                # Dibujar el rectángulo
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, "Cell Phone", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    cv2.imshow("Image", frame)
    key = cv2.waitKey(1)
    if key == 27:  # Presiona 'ESC' para salir
        break

cap.release()
cv2.destroyAllWindows()
