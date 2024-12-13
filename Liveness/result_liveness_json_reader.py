import json
import base64
from PIL import Image
import io
import os

def read_liveness_result(json_path):
    # Lê o arquivo JSON
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extrair informações básicas do Liveness
    session_id = data.get("SessionId", None)
    status = data.get("Status", None)
    confidence = data.get("Confidence", None)

    print(f"SessionId: {session_id}")
    print(f"Status: {status}")
    print(f"Confidence: {confidence}")

    # Caso queira extrair a imagem de referência como PNG:
    if "ReferenceImage" in data and "Bytes" in data["ReferenceImage"]:
        image_base64 = data["ReferenceImage"]["Bytes"]
        image_data = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_data))
        output_filename = "reference_image.png"
        image.save(output_filename, "PNG")
        print(f"Imagem de referência salva como {output_filename}")

    # Caso precise retornar as informações em um dicionário
    return {
        "SessionId": session_id,
        "Status": status,
        "Confidence": confidence
    }

if __name__ == "__main__":
    # Caminho do JSON de exemplo
    json_file = r"C:\Users\Dell\Documents\SDLabs\AI_Document_Parser\AI_Vision\Liveness\sample01.json"
    result = read_liveness_result(json_file)
    # result agora contém SessionId, Status e Confidence
