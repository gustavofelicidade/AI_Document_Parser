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
from Vision.face_recognition import detect_faces, has_face
from PIL import Image
import tempfile
# Processamento de Imagem
from Vision.image_processing import evaluate_image_quality, assess_image_quality
from Vision.image_processing import metric_translation, result_translation, create_quality_dataframe


# Carregar variáveis de ambiente
load_dotenv()

# Carregar as credenciais do .env
ENDPOINT = os.getenv("ENDPOINT")
API_KEY = os.getenv("API_KEY")
print(f"ENDPOINT: {ENDPOINT} \n  API_KEY: {API_KEY}")

field_name_mapping = {
    "FirstName": "Nome",
    "LastName": "Sobrenome",
    "DocumentNumber": "Número de Registro",
    "DateOfBirth": "Data de Nascimento",
    "DateOfExpiration": "Data de Expiração",
    "Sex": "Sexo",
    "Address": "Endereço",
    "CountryRegion": "País/Região",
    "Region": "Região",
    "CPF": "CPF",
    "Filiacao": "Filiação",
    "Validade": "Validade",
    "Habilitacao": "1° Habilitação",
    "CatHab": "Categoria de Habilitação",
    "orgEmissor_UF": "Orgão Emissor/UF",
    "Data_Emissao": "Data de Emissão",
    "Local": "Local",
    "Doc_Identidade": "Documento de Identidade",
    "ASSINATURA DO EMISSOR": "Assinatura do Emissor"
}

field_name_mapping_rg = {
    "Registro_Geral": "Registro Geral",
    "Nome": "Nome Completo",
    "Data_De_Expedicao": "Data de Expedição",
    "Naturalidade": "Naturalidade",
    "Filiacao": "Filiação",
    "DocOrigem": "Documento de Origem",
    "CPF": "CPF",
    "Assinatura_Do_Diretor": "Assinatura do Diretor"
}


# Carregar a lista de nomes comuns do JSON
with pkg_resources.open_text('resources', 'lista-de-nomes.json') as file:
    nome_data = json.load(file)

common_last_names = {name.upper() for name in nome_data["common_last_names"]}


def save_image(uploaded_file):
    """Salva a imagem do documento e insere no Blob Storage."""
    # Redefinir o cursor antes de ler
    uploaded_file.seek(0)
    file_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded_file.name}"

    # Obter os dados do arquivo como bytes
    file_data = uploaded_file.read()

    # Fazer o upload da imagem para o Blob Storage
    db.upload_image_to_blob(file_name, file_data)

    return file_name


def separate_filiacao(filiacao):
    # Verifica se o campo 'filiacao' está vazio
    if not filiacao:
        return "", ""

    # Divide a ‘string’ de 'filiacao' em linhas, removendo espaços em branco
    lines = [line.strip() for line in filiacao.split('\n') if line.strip()]
    print(f"Lines: \n {lines}")

    # Caso 1: Apenas uma linha
    if len(lines) == 1:
        # Divide a linha em nomes separados por espaços
        names = lines[0].split()
        # Calcula o ponto médio da lista de nomes
        half = len(names) // 2
        # A primeira metade dos nomes é atribuída ao pai
        father_name = " ".join(names[:half])
        # A segunda metade dos nomes é atribuída à mãe
        mother_name = " ".join(names[half:])

    # Caso 2: Duas linhas
    elif len(lines) == 2:
        # A primeira linha é o nome do pai
        father_name = lines[0].strip()
        # A segunda linha é o nome da mãe
        mother_name = lines[1].strip()

    # Caso 3: Três linhas
    elif len(lines) == 3:
        # Verifica se a segunda linha é um sobrenome comum
        if lines[1].upper() in common_last_names:
            # Se for, a primeira e segunda linhas juntas formam o nome do pai
            father_name = lines[0].strip() + " " + lines[1].strip()
            # A terceira linha é o nome da mãe
            mother_name = lines[2].strip()
        else:
            # Caso contrário, a primeira linha é o nome do pai
            father_name = lines[0].strip()
            # E as duas últimas linhas formam o nome da mãe
            mother_name = " ".join(lines[1:]).strip()

    # Caso 4: Mais de três linhas
    else:
        # Verifica se a segunda ou terceira linha é um sobrenome comum
        if lines[1].upper() in common_last_names or lines[2].upper() in common_last_names:
            # Se for, as duas primeiras linhas formam o nome do pai
            father_name = " ".join(lines[:2]).strip()
            # E as duas últimas linhas formam o nome da mãe
            mother_name = " ".join(lines[2:]).strip()
        else:
            # Caso contrário, a primeira linha é o nome do pai
            father_name = lines[0].strip()
            # E o restante das linhas formam o nome da mãe
            mother_name = " ".join(lines[1:]).strip()

    # Retorna os nomes do pai e da mãe
    return father_name, mother_name


def cnh_process(result, side):
    data = []
    missing_fields_count = 0  # Contador de campos ausentes
    required_fields_count = 4  # Número máximo de campos ausentes permitidos
    field_list = []
    first_name = ""
    last_name = ""
    if result.documents:
        # print(f"Result Documents Values : {result.items}")
        # print(f"Result Documents Pages : {result.pages}")
        for doc in result.documents:
            if side == "front":
                fields_of_interest = ["FirstName", "LastName", "DocumentNumber", "DateOfBirth", "DateOfExpiration",
                                      "Sex", "Address", "CountryRegion", "Region", "CPF", "Filiacao", "Validade",
                                      "Habilitacao", "CatHab", "orgEmissor_UF", "Data_Emissao", "Local",
                                      "Doc_Identidade"]
            else:
                fields_of_interest = ["Local", "ASSINATURA DO EMISSOR", "Data_Emissao", "Validade"]


            # Laço para verificar e processar os campos de interesse do doc.fields
            for field_name in fields_of_interest:
                field = doc.fields.get(field_name)
                if field:
                    field_list.append(field.content)
                    # print(f"Field Name: {field.content}")

                    if field_name == "Filiacao":
                        father_name, mother_name = separate_filiacao(
                            field.content if hasattr(field, 'content') else field.value_string)
                        data.append({
                            "Nome do Campo": "Nome do Pai",
                            "Valor/Conteúdo": father_name,
                            "Confiança": field.confidence
                        })
                        data.append({
                            "Nome do Campo": "Nome da Mãe",
                            "Valor/Conteúdo": mother_name,
                            "Confiança": field.confidence
                        })
                    elif field_name in ["FirstName", "LastName"]:
                        # Armazena o nome e sobrenome
                        if field_name == "FirstName":
                            first_name = field.content if hasattr(field, 'content') else field.value_string
                        else:
                            last_name = field.content if hasattr(field, 'content') else field.value_string
                        # Vamos combiná-los depois
                    else:
                        data.append({
                            "Nome do Campo": field_name_mapping.get(field_name, field_name),
                            "Valor/Conteúdo": field.content if hasattr(field, 'content') else field.value_string,
                            "Confiança": field.confidence
                        })

            # Após processar todos os campos, combine o nome e o sobrenome
            full_name = f"{first_name} {last_name}".strip()
            if full_name:
                data.insert(0, {  # Insere no início
                    "Nome do Campo": "Nome Completo",
                    "Valor/Conteúdo": full_name,
                    "Confiança": min(
                        field.confidence for field_name in ["FirstName", "LastName"]
                        if (field := doc.fields.get(field_name))
                    )
                })

            # Contar quantos campos estão ausentes (None) na field_list
            missing_fields_count = field_list.count(None)
            if missing_fields_count >= required_fields_count:
                st.error("Documento de CNH não identificado, por favor tente novamente.")
                st.error(f"Campos ausentes: {missing_fields_count}")
                return None  # Retorna nada

            print(f"Field List: {field_list}")
    return pd.DataFrame(data)


def rg_process(result):
    data = []
    missing_fields_count = 0  # Contador de campos ausentes
    required_fields_count = 4  # Número máximo de campos ausentes permitidos
    field_list = []  # Lista para armazenar os campos encontrados
    first_name = ""
    last_name = ""

    if result.documents:
        for doc in result.documents:
            fields_of_interest = ["Registro_Geral", "Nome", "Data_De_Expedicao", "Data_De_Nascimento", "Naturalidade",
                                  "Filiacao", "DocOrigem", "CPF", "Assinatura_Do_Diretor"]

            # Laço para verificar e processar os campos de interesse
            for field_name in fields_of_interest:
                field = doc.fields.get(field_name)
                if field:
                    field_list.append(field.content)
                    if field_name == "Filiacao":
                        father_name, mother_name = separate_filiacao(
                            field.content if hasattr(field, 'content') else field.value_string)
                        data.append({
                            "Nome do Campo": "Nome do Pai",
                            "Valor/Conteúdo": father_name,
                            "Confiança": field.confidence
                        })
                        data.append({
                            "Nome do Campo": "Nome da Mãe",
                            "Valor/Conteúdo": mother_name,
                            "Confiança": field.confidence
                        })
                    # elif field_name in ["FirstName", "LastName"]:
                    #     if field_name == "FirstName":
                    #         first_name = field.content if hasattr(field, 'content') else field.value_string
                    #     else:
                    #         last_name = field.content if hasattr(field, 'content') else field.value_string
                    else:
                        data.append({
                            "Nome do Campo": field_name_mapping_rg.get(field_name, field_name),
                            "Valor/Conteúdo": field.content if hasattr(field, 'content') else field.value_string,
                            "Confiança": field.confidence
                        })
                        print(f"field_name {field_name}")
                else:
                    field_list.append(None)  # Adiciona None se o campo estiver ausente

            # # Após processar todos os campos, combine nome e sobrenome se ambos existirem
            # full_name = f"{first_name} {last_name}".strip() if first_name or last_name else None
            # if full_name:
            #     data.insert(0, {  # Inserir no início da lista
            #         "Nome do Campo": "Nome",
            #         "Valor/Conteúdo": full_name,
            #         "Confiança": min(
            #             field.confidence for field_name in ["FirstName", "LastName"]
            #             if (field := doc.fields.get(field_name))
            #         )
            #     })
            #
            # elif doc.fields.get("Nome") and not full_name:
            #     # Se somente o campo "Nome" estiver presente, use esse
            #     field = doc.fields.get("Nome")
            #     data.insert(0, {
            #         "Nome do Campo": "Nome",
            #         "Valor/Conteúdo": field.content if hasattr(field, 'content') else field.value_string,
            #         "Confiança": field.confidence
            #     })

            # Contar quantos campos estão ausentes (None) na field_list
            missing_fields_count = field_list.count(None)
            if missing_fields_count >= required_fields_count:
                st.error(f"Documento de RG não identificado. Campos ausentes: {missing_fields_count}")
                st.error(f"Por favor, insira o Documento de RG novamente.")
                return None  # Retorna nada para indicar que o documento não foi identificado corretamente

            print(f"Field List: {field_list}")

    return pd.DataFrame(data)


def analyze_uploaded_document(uploaded_file, document_type, side=None):
    client = DocumentIntelligenceClient(endpoint=ENDPOINT, credential=AzureKeyCredential(API_KEY))

    # Redefinir o cursor antes de ler
    uploaded_file.seek(0)
    document = uploaded_file.read()

    # Definição da Lista de Parametros da Requisição conforme o tipo de documento
    #######################################################################################################
    if document_type.startswith("CNH"):
        if side == "front":
            query_fields = ["CPF", "Filiacao", "Validade", "Habilitacao", "CatHab", "orgEmissor_UF", "Data_Emissao",
                            "Local", "Doc_Identidade", "FirstName", "LastName", "DateOfBirth", "DocumentNumber"]
        else:
            query_fields = ["Local", "Data_Emissao", "Filiacao", "Validade"]

    elif document_type.startswith("RG"):
        query_fields = ["Registro_Geral", "Nome", "Data_De_Expedicao", "Naturalidade", "Filiacao",
                        "DocOrigem", "CPF", "Assinatura_Do_Diretor"]

    #######################################################################################################

    # Modelo da Requisição
    poller = client.begin_analyze_document(
        model_id="prebuilt-idDocument",
        analyze_request=AnalyzeDocumentRequest(bytes_source=document),
        features=[DocumentAnalysisFeature.QUERY_FIELDS],
        query_fields=query_fields
    )

    # Resultado da Requisição
    result = poller.result()

    # Avaliar conforme o document_type
    if document_type.startswith("CNH"):
        return cnh_process(result, side)
    elif document_type.startswith("RG"):
        return rg_process(result)
    else:
        data = []
        for page in result.pages:
            for line in page.lines:
                data.append({"Content": line.content})
        return pd.DataFrame(data)


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

                        # Verificar se a imagem do verso contém uma face
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_back:
                            img_back = Image.open(back_image)
                            img_back.save(tmp_back.name)
                            tmp_back_path = tmp_back.name

                        # Depois de usar back_image, redefina o cursor
                        back_image.seek(0)

                        # Usar a função has_face para detectar face na imagem do verso
                        if has_face(tmp_back_path):
                            st.error(
                                "A imagem do verso da CNH parece conter a frente do documento ou a CNH aberta. Por favor, envie apenas a imagem do verso da CNH.")
                            return  # Interrompe o processamento
                        else:
                            # Redefina o cursor antes de salvar a imagem
                            back_image.seek(0)
                            # Salvar a imagem e continuar o processamento
                            file_path = save_image(back_image)
                            st.success(f"Imagem salva em: {file_path}")

                            st.write("Analisando documento do verso...")
                            # Redefina o cursor antes de ler novamente
                            back_image.seek(0)
                            df_back = analyze_uploaded_document(back_image, "CNH", side="back")

                            if df_back is not None and not df_back.empty:
                                st.write("Dados da CNH (Frente)")
                                st.write(df_front)
                                st.write("Dados da CNH (Verso)")
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


class Main:
    def __init__(self):
        with open('config.yaml') as file:
            self.config = yaml.load(file, Loader=SafeLoader)

    def main(self):
        # Main Page Layout
        col1, col2 = st.columns([10, 4])
        with col2:
            st.markdown("# Document Intelligence")

        with col1:
            st.markdown("# AI Vision 👁️")
            st.write("Siga os próximos passos para extrair dados dos documentos:")

        st.warning("Insira a imagem do Documento para processar", icon="⚠️")

        # Sidebar: Menu Lateral
        global name
        name = "Client"
        st.sidebar.title(f"Welcome {name}")

        button = st.sidebar.button("Logout")
        if button:
            self.logout()

        option = st.sidebar.radio(
            'Página Home definida',
            ('Home', 'Dashboard'),
            key="main_option"
        )

        if option == 'Home':
            Homepage()
            st.markdown("""Footer""")

            # Hide Streamlit Style
            hide_st_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                </style>
            """
            st.markdown(hide_st_style, unsafe_allow_html=True)

        st.sidebar.markdown("# AI Document Parser")
