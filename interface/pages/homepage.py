from interface.utils.misc import save_image, analyze_uploaded_document
import os
import json
import time

import streamlit as st
import pandas as pd
import yaml
import importlib.resources as pkg_resources
from datetime import datetime
from yaml.loader import SafeLoader
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import DocumentAnalysisFeature, AnalyzeDocumentRequest

import resources.database as db
from Vision.face_recognition import detect_faces
from PIL import Image
import tempfile
# Processamento de Imagem
from Vision.image_processing import evaluate_image_quality, assess_image_quality
from Vision.image_processing import metric_translation, result_translation, create_quality_dataframe


class Homepage:
    def __init__(self):
        st.title("Análise de Documentos com Azure")
        self.upload_documents()

    def upload_documents(self):
        document_type = st.selectbox("Selecione o tipo de documento", ["CNH", "RG"])

        if document_type == "CNH":
            self.upload_cnh()
        elif document_type == "RG":
            self.upload_rg()

    def upload_cnh(self):
        st.write("Upload Imagem CNH Frente...")
        col1, col2 = st.columns(2)
        with col1:
            front_image = st.file_uploader("Upload Imagem CNH Frente...", type=["jpg", "jpeg", "png"], key="front")
        if front_image:
            with col1:
                st.image(front_image, caption="CNH Front Image", width=300)

            file_path = save_image(front_image)
            st.success(f"Imagem salva em: {file_path}")

            st.write("Analisando documento da frente...")
            df_front = analyze_uploaded_document(front_image, "CNH", side="front")

            if df_front is not None and not df_front.empty:
                with col2:
                    st.write("Upload Imagem CNH Verso...")
                    back_image = st.file_uploader("Upload Imagem CNH Verso...", type=["jpg", "jpeg", "png"], key="back")

                    if back_image:
                        st.image(back_image, caption="CNH Back Image", width=300)

                        file_path = save_image(back_image)
                        st.success(f"Imagem salva em: {file_path}")

                        st.write("Analisando documento do verso...")
                        df_back = analyze_uploaded_document(back_image, "CNH", side="back")

                        if df_back is not None and not df_back.empty:
                            st.write("CNH Front Data")
                            st.write(df_front)
                            st.write("CNH Back Data")
                            st.write(df_back)

                            nome_completo = \
                            df_front[df_front['Nome do Campo'] == 'Nome Completo']['Valor/Conteúdo'].values[0]

                            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                                img = Image.open(front_image)
                                img.save(tmp.name)
                                tmp_path = tmp.name

                            st.write("Detectando rosto...")
                            face_path = detect_faces(tmp_path, nome_completo)
                            time.sleep(2.5)  # Pequeno delay para aguardar o processamento completo

                            if face_path:
                                st.image(face_path, caption=f"Rosto de {nome_completo}", width=200)
                                st.success(f"Rosto de {nome_completo} detectado e salvo.")

                                with open(face_path, "rb") as face_file:
                                    db.upload_image_to_blob(f"{nome_completo}_face.jpg", face_file.read())

                            # Avaliar a qualidade da frente e do verso da imagem
                            quality_metrics_front = evaluate_image_quality(tmp_path)
                            quality_report_front = assess_image_quality(quality_metrics_front)

                            # Avaliação do verso da CNH
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_back:
                                img_back = Image.open(back_image)
                                img_back.save(tmp_back.name)
                                tmp_back_path = tmp_back.name

                            quality_metrics_back = evaluate_image_quality(tmp_back_path)
                            quality_report_back = assess_image_quality(quality_metrics_back)

                            # Exibir a qualidade da frente e do verso em um DataFrame
                            st.write("Relatório de Qualidade da Imagem")
                            quality_df = create_quality_dataframe(quality_metrics_front, quality_report_front,
                                                                  quality_metrics_back, quality_report_back)
                            st.dataframe(quality_df)

                        else:
                            st.error("Documento de CNH (verso) não identificado corretamente.")
                    else:
                        st.warning("Por favor, insira a imagem do verso da CNH.")
            else:
                st.error("Documento de CNH (frente) não identificado corretamente.")
        else:
            st.warning("Por favor, insira a imagem da frente da CNH.")

    def upload_rg(self):
        st.write("Upload Imagem RG Frente...")
        col1, col2 = st.columns(2)
        with col1:
            front_image = st.file_uploader("Upload Imagem RG Frente...", type=["jpg", "jpeg", "png"], key="front_rg")
        if front_image:
            with col1:
                st.image(front_image, caption="RG Front Image", width=300)

            file_path = save_image(front_image)
            st.success(f"Imagem salva em: {file_path}")

            with col2:
                st.write("Upload Imagem RG Verso...")
                back_image = st.file_uploader("Upload Imagem RG Verso...", type=["jpg", "jpeg", "png"], key="back_rg")
                if back_image:
                    st.image(back_image, caption="RG Back Image", width=300)

                    file_path = save_image(back_image)
                    st.success(f"Imagem salva em: {file_path}")

                    st.write("Analisando documento do verso...")
                    df_back = analyze_uploaded_document(back_image, "RG_Verso")

                    if df_back is not None and not df_back.empty:
                        st.write("Dados do RG (Verso)")
                        st.write(df_back)

                        nome_completo = df_back[df_back['Nome do Campo'] == 'Nome Completo']['Valor/Conteúdo'].values[0]

                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                            img = Image.open(front_image)

                            if img.mode == 'RGBA':
                                img = img.convert('RGB')

                            img.save(tmp.name)
                            tmp_path = tmp.name

                        st.write("Detectando rosto...")
                        face_path = detect_faces(tmp_path, nome_completo)

                        if face_path:
                            st.image(face_path, caption=f"Rosto de {nome_completo}", width=200)
                            st.success(f"Rosto de {nome_completo} detectado e salvo.")

                            with open(face_path, "rb") as face_file:
                                db.upload_image_to_blob(f"{nome_completo}_face.jpg", face_file.read())

                        # Avaliação da qualidade da frente e do verso
                        quality_metrics_front = evaluate_image_quality(tmp_path)
                        quality_report_front = assess_image_quality(quality_metrics_front)

                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_back:
                            img_back = Image.open(back_image)
                            img_back.save(tmp_back.name)
                            tmp_back_path = tmp_back.name

                        quality_metrics_back = evaluate_image_quality(tmp_back_path)
                        quality_report_back = assess_image_quality(quality_metrics_back)

                        st.write("Relatório de Qualidade da Imagem")
                        quality_df = create_quality_dataframe(quality_metrics_front, quality_report_front,
                                                              quality_metrics_back, quality_report_back)
                        st.dataframe(quality_df)

                    else:
                        st.error("Documento de RG (verso) não identificado corretamente.")
                else:
                    st.warning("Por favor, insira a imagem do verso do RG.")
        else:
            st.warning("Por favor, insira a imagem da frente do RG.")