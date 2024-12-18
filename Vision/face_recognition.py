import cv2
import os
from ultralytics import YOLO
import time
from dotenv import load_dotenv

# Definir caminho de saída para salvar fotos dos rostos detectados
output_dir = "C:/Users/Dell/Documents/SDLabs/AI_Document_Parser/AI_Vision/Vision/faces"
os.makedirs(output_dir, exist_ok=True)

# Carregar variáveis de ambiente (se necessário)
load_dotenv()

def has_face(image_path):
    """Verifica se há rostos na imagem usando YOLO."""
    model = YOLO("yolov8n-face.pt")  # Use um modelo pré-treinado para detecção de faces
    results = model(image_path)

    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])  # Classe do objeto detectado
            if cls == 0:  # Classe 0 corresponde a 'face' no modelo de detecção de faces
                return True
    return False


def save_face(image, bbox, name):
    """Salva as imagens dos rostos detectados com base no nome da pessoa."""
    x1, y1, x2, y2 = map(int, bbox)
    face = image[y1:y2, x1:x2]

    face_path = os.path.join(output_dir, f"{name}.jpg")

    # Garantir que a imagem foi processada antes de salvar
    if face is not None and face.size > 0:  # Certificar-se de que o rosto foi extraído corretamente
        cv2.imwrite(face_path, face)
        print(f"Rosto salvo em: {face_path}")
        return face_path
    else:
        print("Erro ao salvar o rosto: A imagem do rosto está vazia ou inválida.")
    return None


def detect_faces(image_path, full_name):
    """Detecta rostos numa imagem usando YOLO e salva o rosto extraído."""
    model = YOLO("yolov8n-face.pt")  # Use um modelo pré-treinado para detecção de faces
    results = model(image_path)

    # Carregar a imagem usando OpenCV para manipulação
    image = cv2.imread(image_path)

    # Iterar pelos resultados de detecção
    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])  # Classe do objeto detectado
            if cls == 0:  # Classe 0 corresponde a 'face' no modelo de detecção de faces
                bbox = box.xyxy[0].numpy()  # Coordenadas do bounding box
                face_path = save_face(image, bbox, full_name)

                # Aguardar brevemente para garantir o processamento do rosto
                time.sleep(0.5)  # Delay de meio segundo para garantir que o rosto seja salvo corretamente

                return face_path  # Retornar o caminho do rosto extraído
    return None
