import cv2
import os
from PIL import Image, ImageStat
import numpy as np
import pandas as pd

# Mapeamento de métricas e resultados para PT-BR
metric_translation = {
    'Sharpness': 'Nitidez',
    'Brightness': 'Brilho',
    'Contrast': 'Contraste',
    'Width': 'Largura',
    'Height': 'Altura',
    'Ratio': 'Proporção',
    'ContainsFace': 'ContémFace',
}

result_translation = {
    'Good': 'Boa',
    'Poor': 'Ruim',
}


# Função para criar DataFrame de qualidade em PT-BR
def create_quality_dataframe(metrics_front, report_front, metrics_back=None, report_back=None):
    data = []

    for metric, translated_metric in metric_translation.items():
        front_value = metrics_front.get(metric, '-')
        front_result = result_translation.get(report_front.get(metric, 'Ruim'), 'Ruim')

        back_value = metrics_back.get(metric, '-') if metrics_back else '-'
        back_result = result_translation.get(report_back.get(metric, 'Ruim'), 'Ruim') if report_back else '-'

        data.append({
            'Métrica': translated_metric,
            'Frente Valor': front_value,
            'Verso Valor': back_value,
            'Frente Resultado': front_result,
            'Verso Resultado': back_result
        })

    return pd.DataFrame(data)


# Função para verificar a nitidez da imagem (usando variância do Laplaciano)
def evaluate_sharpness(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    variance = cv2.Laplacian(image, cv2.CV_64F).var()
    return variance


# Função para verificar o brilho da imagem (usando PIL)
def evaluate_brightness(image_path):
    image = Image.open(image_path)
    stat = ImageStat.Stat(image)
    brightness = sum(stat.mean) / len(stat.mean)  # Média do brilho dos canais
    return brightness


# Função para verificar o contraste da imagem
def evaluate_contrast(image_path):
    image = Image.open(image_path)
    stat = ImageStat.Stat(image)
    contrast = max(stat.stddev)  # Desvio padrão como proxy para contraste
    return contrast


# Função para verificar as dimensões da imagem (largura e altura)
def evaluate_dimensions(image_path):
    image = Image.open(image_path)
    width, height = image.size
    return width, height


# Função para verificar a proporção da imagem
def evaluate_ratio(width, height):
    return width / height


# Função para verificar se a imagem contém um rosto (usando OpenCV)
def evaluate_contains_face(image_path):
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    return len(faces) > 0  # Retorna True se algum rosto for detectado


# Função para avaliar a qualidade da imagem
def evaluate_image_quality(image_path):
    results = {}

    # Avaliar nitidez
    sharpness = evaluate_sharpness(image_path)
    results['Sharpness'] = sharpness

    # Avaliar brilho
    brightness = evaluate_brightness(image_path)
    results['Brightness'] = brightness

    # Avaliar contraste
    contrast = evaluate_contrast(image_path)
    results['Contrast'] = contrast

    # Avaliar dimensões
    width, height = evaluate_dimensions(image_path)
    results['Width'] = width
    results['Height'] = height

    # Avaliar proporção
    ratio = evaluate_ratio(width, height)
    results['Ratio'] = ratio

    # Verificar se contém rosto
    contains_face = evaluate_contains_face(image_path)
    results['ContainsFace'] = contains_face

    return results


def assess_image_quality(quality_metrics):
    # Critérios de avaliação
    thresholds = {
        'Sharpness': 1000,
        'Brightness': (100, 200),
        'Contrast': 50,
        'MinWidth': 600,
        'MinHeight': 400,
        'Ratio': (1.3, 1.7),
        'ContainsFace': True
    }

    quality_report = {}

    # Avaliação de Nitidez
    quality_report['Sharpness'] = "Good" if quality_metrics['Sharpness'] > thresholds['Sharpness'] else "Poor"

    # Avaliação de Brilho
    brightness = quality_metrics['Brightness']
    if thresholds['Brightness'][0] <= brightness <= thresholds['Brightness'][1]:
        quality_report['Brightness'] = "Good"
    else:
        quality_report['Brightness'] = "Poor"

    # Avaliação de Contraste
    quality_report['Contrast'] = "Good" if quality_metrics['Contrast'] > thresholds['Contrast'] else "Poor"

    # Avaliação das Dimensões
    if quality_metrics['Width'] >= thresholds['MinWidth'] and quality_metrics['Height'] >= thresholds['MinHeight']:
        quality_report['Dimensions'] = "Good"
    else:
        quality_report['Dimensions'] = "Poor"

    # Avaliação da Proporção
    ratio = quality_metrics['Ratio']
    if thresholds['Ratio'][0] <= ratio <= thresholds['Ratio'][1]:
        quality_report['Ratio'] = "Good"
    else:
        quality_report['Ratio'] = "Poor"

    # Avaliação da presença de rosto
    quality_report['ContainsFace'] = "Good" if quality_metrics['ContainsFace'] == thresholds['ContainsFace'] else "Poor"

    # Avaliação final
    overall_quality = "Good" if all(value == "Good" for value in quality_report.values()) else "Poor"
    quality_report['OverallQuality'] = overall_quality

    return quality_report


# Exemplo de uso com os dados fornecidos
quality_metrics = {
    'Sharpness': 1671.1710127547833,
    'Brightness': 126.31613516773184,
    'Contrast': 56.606450648709675,
    'Width': 1019,
    'Height': 722,
    'Ratio': 1.4113573407202216,
    'ContainsFace': True
}

# quality_report = assess_image_quality(quality_metrics)
# print(quality_report)


# Exemplo de uso
# if __name__ == "__main__":
#     image_path = r"C:/Users/Dell/Downloads/CNH Database/eduardocortadafrente.jpg"
#     quality_metrics = evaluate_image_quality(image_path)
#     print(quality_metrics)
#
#     quality_report = assess_image_quality(quality_metrics)
#     print(quality_report)