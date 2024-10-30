import streamlit as st
from streamlit_drawable_canvas import st_canvas
import cv2
import numpy as np
from PIL import Image

def four_point_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # Calcula a largura e a altura da nova imagem
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = max(int(heightA), int(heightB))

    # Define os pontos de destino
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    # Calcula a matriz de transformação e aplica
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

    return warped

def order_points(pts):
    # Ordena os pontos no sentido horário começando do topo-esquerdo
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)

    rect[0] = pts[np.argmin(s)]     # Topo-esquerdo
    rect[2] = pts[np.argmax(s)]     # Inferior-direito
    rect[1] = pts[np.argmin(diff)]  # Topo-direito
    rect[3] = pts[np.argmax(diff)]  # Inferior-esquerdo

    return rect

# st.title("Seleção Manual de Pontos para Correção de Perspectiva")

# Carrega a imagem
# uploaded_file = st.file_uploader("Carregue uma imagem do documento", type=["jpg", "jpeg", "png"])

# if uploaded_file is not None:
#     image = Image.open(uploaded_file)
#     orig_image = image.copy()
#     image_np = np.array(image)
#
#     st.write("Ajuste o quadrilátero para marcar os 4 cantos do documento.")
#
#     # Define o tamanho máximo para a imagem exibida
#     max_width = 700  # Ajuste conforme necessário
#
#     # Redimensiona a imagem se for maior que a largura máxima
#     if image.width > max_width:
#         ratio = max_width / image.width
#         new_width = int(image.width * ratio)
#         new_height = int(image.height * ratio)
#         image = image.resize((new_width, new_height))
#         image_np = np.array(image)
#     else:
#         ratio = 1.0
#         new_width = image.width
#         new_height = image.height
#
#     # Cria um polígono inicial (quadrilátero) que cobre a imagem com propriedades personalizadas
#     initial_polygon = {
#         "version": "4.4.0",
#         "objects": [
#             {
#                 "type": "polygon",
#                 "version": "4.4.0",
#                 "originX": "left",
#                 "originY": "top",
#                 "left": 50,
#                 "top": 50,
#                 "width": new_width - 100,
#                 "height": new_height - 100,
#                 "fill": "rgba(255, 165, 0, 0.3)",  # Cor de preenchimento com transparência
#                 "stroke": "red",
#                 "strokeWidth": 3,
#                 "scaleX": 1,
#                 "scaleY": 1,
#                 "angle": 0,
#                 "flipX": False,
#                 "flipY": False,
#                 "opacity": 1,
#                 "skewX": 0,
#                 "skewY": 0,
#                 "selectable": True,
#                 "evented": True,
#                 "objectCaching": True,
#                 "name": "document_polygon",
#                 "points": [
#                     {"x": 0, "y": 0},
#                     {"x": new_width - 100, "y": 0},
#                     {"x": new_width - 100, "y": new_height - 100},
#                     {"x": 0, "y": new_height - 100},
#                 ],
#                 "cornerStyle": "circle",
#                 "cornerSize": 12,
#                 "cornerColor": "red",
#                 "cornerStrokeColor": "red",
#             }
#         ]
#     }
#
#     # Cria o componente canvas
#     canvas_result = st_canvas(
#         fill_color="rgba(255, 165, 0, 0.3)",
#         stroke_width=3,
#         stroke_color="red",
#         background_image=image,
#         initial_drawing=initial_polygon,
#         update_streamlit=True,
#         height=new_height,
#         width=new_width,
#         drawing_mode="transform",
#         display_toolbar=True,
#         key="canvas",
#     )
#
#     # Processa o resultado do canvas
#     if canvas_result.json_data is not None:
#         # Procura pelo objeto com o nome "document_polygon"
#         for obj in canvas_result.json_data["objects"]:
#             if obj.get("name") == "document_polygon":
#                 # Obtém os pontos do polígono
#                 points = obj["path"] if "path" in obj else obj["points"]
#                 if len(points) == 4:
#                     pts = []
#                     for point in points:
#                         if isinstance(point, list):
#                             x = point[1][0]
#                             y = point[1][1]
#                         else:
#                             x = point["x"] * obj["scaleX"] + obj["left"]
#                             y = point["y"] * obj["scaleY"] + obj["top"]
#                         pts.append([x, y])
#                     pts = np.array(pts, dtype="float32")
#
#                     # Ajusta as coordenadas dos pontos para o tamanho original da imagem
#                     pts_original = pts * (1 / ratio)
#
#                     # Aplica a transformação de perspectiva usando a imagem original
#                     warped = four_point_transform(np.array(orig_image), pts_original)
#
#                     st.image(warped, caption="Imagem Transformada", use_column_width=True)
#
#                     # Integração com OCR ou outras funcionalidades
#                     if st.button("Extrair Dados com OCR"):
#                         st.write("Processando OCR...")
#                         # Seu código de OCR aqui
#
#                 else:
#                     st.warning("O polígono deve ter exatamente 4 pontos.")
#                 break  # Não precisamos continuar o loop após encontrar o objeto
#     else:
#         st.write("Ajuste o quadrilátero para selecionar o documento.")
# else:
#     st.write("Por favor, carregue uma imagem para continuar.")
