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
    "Doc_Identidade": "Documento de Identidade"
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
    file_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded_file.name}"

    # Obter os dados do arquivo como bytes
    file_data = uploaded_file.getbuffer()

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
        for doc in result.documents:
            if side == "front":
                fields_of_interest = ["FirstName", "LastName", "DocumentNumber", "DateOfBirth", "DateOfExpiration",
                                      "Sex", "Address", "CountryRegion", "Region", "CPF", "Filiacao", "Validade",
                                      "Habilitacao", "CatHab", "orgEmissor_UF", "Data_Emissao", "Local",
                                      "Doc_Identidade"]
            else:
                fields_of_interest = ["Local", "Data_Emissao", "Validade"]

            # Laço para verificar e processar os campos de interesse do doc.fields
            for field_name in fields_of_interest:
                field = doc.fields.get(field_name)
                if field:
                    field_list.append(field.content)
                    print(f"Field Name: {field.content}")

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

