import requests
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
from PIL import Image, ImageDraw

# Chave e endpoint
KEY = "ba3d7342468c402a8ee5392f25775f92"
ENDPOINT = "https://faceidcomputacional.cognitiveservices.azure.com/"

# Criar um cliente Face autenticado
face_client = FaceClient(ENDPOINT, CognitiveServicesCredentials(KEY))

# Caminho para a imagem (pode ser um caminho local ou URL)
image_path = r"C:\Users\Dell\Downloads\eduardo.jpg"  # Atualize este caminho conforme necessário


# Detectar rosto na imagem
def detect_face(image_path):
    with open(image_path, 'rb') as image:
        detected_faces = face_client.face.detect_with_stream(image, detection_model='detection_03')

    if not detected_faces:
        raise Exception("Nenhum rosto detectado.")

    return detected_faces


# Salvar a face detectada em um novo arquivo
def save_detected_face(image_path, detected_faces):
    with Image.open(image_path) as img:
        draw = ImageDraw.Draw(img)
        for face in detected_faces:
            rect = face.face_rectangle
            left, top, right, bottom = rect.left, rect.top, rect.left + rect.width, rect.top + rect.height
            draw.rectangle(((left, top), (right, bottom)), outline="red", width=5)
        img.save("/mnt/data/face_detectada.jpg")


# Processo de detecção e salvamento
try:
    detected_faces = detect_face(image_path)
    save_detected_face(image_path, detected_faces)
    print("Face detectada e salva com sucesso em 'face_detectada.jpg'")
except Exception as e:
    print(f"Erro: {e}")

