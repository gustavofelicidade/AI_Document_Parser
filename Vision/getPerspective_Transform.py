import cv2
import numpy as np
import os
import uuid  # Para gerar identificadores únicos para os nomes dos arquivos

def order_points(pts):
    # Ordena os pontos no sentido horário começando do topo-esquerda
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)

    rect[0] = pts[np.argmin(s)]     # Topo-esquerda
    rect[2] = pts[np.argmax(s)]     # Inferior-direita
    rect[1] = pts[np.argmin(diff)]  # Topo-direita
    rect[3] = pts[np.argmax(diff)]  # Inferior-esquerda

    return rect


def four_point_transform(image, pts):
    # Obtém os pontos ordenados
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Calcula a largura da nova imagem
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = max(int(widthA), int(widthB))

    # Calcula a altura da nova imagem
    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = max(int(heightA), int(heightB))

    # Define os pontos de destino para a transformação
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    # Calcula a matriz de transformação e aplica a perspectiva
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

    return warped


def load_image_to_transform(image):
    # Verifica se a imagem foi carregada corretamente
    if image is None:
        print("Imagem inválida.")
        return None

    # Redimensiona a imagem para facilitar o processamento
    orig = image.copy()
    ratio = image.shape[0] / 500.0
    image = cv2.resize(image, (int(image.shape[1] / ratio), 500))

    # Converte para escala de cinza
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Aplica uma filtragem bilateral para suavizar a imagem enquanto preserva as bordas
    gray = cv2.bilateralFilter(gray, 11, 17, 17)

    # Aplica detecção de bordas
    edged = cv2.Canny(gray, 30, 200)

    # Aplica operações morfológicas para fechar pequenas lacunas nas bordas
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)

    # Encontra os contornos na imagem
    cnts, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

    # Inicializa a variável de contorno
    screenCnt = None

    # Loop pelos contornos encontrados
    for c in cnts:
        # Aproxima o contorno para uma forma de menos vértices
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        # Se o contorno tiver quatro pontos, assumimos que encontramos o documento
        if len(approx) == 4:
            screenCnt = approx
            break

    # Verifica se o documento foi encontrado
    if screenCnt is None:
        print("Não foi possível encontrar o documento na imagem.")
        return None
    else:
        # Aplica a transformação de perspectiva na imagem original
        warped = four_point_transform(orig, screenCnt.reshape(4, 2) * ratio)

        # Retorna a imagem colorida transformada
        return warped


def save_transformed_image(transformed_image, output_dir="output", filename=None):
    if transformed_image is not None:
        # Cria o diretório de saída se não existir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Se um nome de arquivo não for fornecido, gera um nome único
        if filename is None:
            filename = f"transformed_{uuid.uuid4().hex[:8]}.jpg"

        output_path = os.path.join(output_dir, filename)

        # Salva a imagem transformada
        cv2.imwrite(output_path, transformed_image)
        print(f"Imagem transformada salva em: {output_path}")

        # Opcional: Mostra a imagem transformada
        # cv2.imshow("Documento Transformado", transformed_image)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        # Retorna o caminho do arquivo salvo
        return output_path
    else:
        print("Falha ao salvar a imagem transformada.")
        return None


if __name__ == "__main__":
    # Exemplo de uso
    # image_path = "test.jpg"  # Substitua pelo caminho da sua imagem
    image_path = r"C:\Users\Dell\Downloads\CNH Database\WhatsApp Image 2024-10-03 at 12.50.53_ab40f1c0.jpg"

    # Carrega a imagem
    image = cv2.imread(image_path)

    # Transforma a imagem
    transformed_image = load_image_to_transform(image)

    # Salva a imagem transformada
    save_transformed_image(transformed_image)
