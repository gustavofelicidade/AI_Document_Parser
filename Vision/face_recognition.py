import cv2
import os
from ultralytics import YOLO

# Definir caminho de saída para salvar fotos dos rostos detectados
output_dir = "C:/Users/Dell/Documents/SDLabs/AI_Document_Parser/AI_Vision/Vision/faces"
os.makedirs(output_dir, exist_ok=True)


def save_face(image, bbox, name):
    """Salva as imagens dos rostos detectados com base no nome da pessoa."""
    x1, y1, x2, y2 = map(int, bbox)
    face = image[y1:y2, x1:x2]
    face_path = os.path.join(output_dir, f"{name}.jpg")
    cv2.imwrite(face_path, face)
    print(f"Rosto salvo em: {face_path}")
    return face_path


def detect_faces(image_path, full_name):
    """Detecta rostos numa imagem usando YOLO e salva o rosto extraído."""
    model = YOLO("yolov8n.pt")  # Substitua com o modelo apropriado, se necessário
    results = model(image_path)

    # Carregar a imagem usando OpenCV para manipulação
    image = cv2.imread(image_path)

    # Iterar pelos resultados de detecção
    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])  # Classe do objeto detectado
            if cls == 0:  # Assumindo que a classe 0 seja "pessoa/rosto"
                bbox = box.xyxy[0].numpy()  # Coordenadas do bounding box
                face_path = save_face(image, bbox, full_name)
                return face_path  # Retornar o caminho do rosto extraído
    return None



