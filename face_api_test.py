import requests
from PIL import Image, ImageDraw
from io import BytesIO
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials

KEY = "77e7c2bb59e44c8da77cf38e71ef000b"
ENDPOINT = "https://face-api-qsti-dev-01.cognitiveservices.azure.com/"

# URL da imagem que contém um único rosto
single_face_image_url = 'https://raw.githubusercontent.com/Microsoft/Cognitive-Face-Windows/master/Data/detection1.jpg'

# Criação do cliente autenticado FaceClient
face_client = FaceClient(ENDPOINT, CognitiveServicesCredentials(KEY))

# Detecta um rosto em uma imagem que contém um único rosto
detected_faces = face_client.face.detect_with_url(url=single_face_image_url)
if not detected_faces:
    raise Exception('No face detected from image {}'.format(single_face_image_url))

# Baixa a imagem da URL
response = requests.get(single_face_image_url)
img = Image.open(BytesIO(response.content))

# Para cada face detectada, desenha um retângulo vermelho ao redor
print('Desenhando um retângulo ao redor do rosto... veja o popup para os resultados.')
draw = ImageDraw.Draw(img)
for face in detected_faces:
    draw.rectangle([(face.face_rectangle.left, face.face_rectangle.top),
                    (face.face_rectangle.left + face.face_rectangle.width,
                     face.face_rectangle.top + face.face_rectangle.height)], outline='red')

# Mostra a imagem no visualizador padrão de imagens do usuário
img.show()
