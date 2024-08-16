from fastapi import FastAPI, File, UploadFile, HTTPException
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import DocumentAnalysisFeature, AnalyzeDocumentRequest
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Carregar as credenciais do .env
ENDPOINT = os.getenv("ENDPOINT")
API_KEY = os.getenv("API_KEY")

field_name_mapping = {
    "LastName": "Nome",
    "FirstName": "Sobrenome",
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
    "Nome": "Nome",
    "Data_De_Expedicao": "Data de Expedição",
    "Naturalidade": "Naturalidade",
    "Filiacao": "Filiação",
    "DocOrigem": "Documento de Origem",
    "CPF": "CPF",
    "Assinatura_Do_Diretor": "Assinatura do Diretor"
}

common_last_names = {"SILVA", "SOUZA", "COSTA", "PEREIRA", "OLIVEIRA"}

def separate_filiacao(filiacao):
    if not filiacao:
        return "", ""

    lines = [line.strip() for line in filiacao.split('\n') if line.strip()]

    if len(lines) == 1:
        names = lines[0].split()
        half = len(names) // 2
        father_name = " ".join(names[:half])
        mother_name = " ".join(names[half:])
    elif len(lines) == 2:
        father_name = lines[0].strip()
        mother_name = lines[1].strip()
    elif len(lines) == 3:
        if lines[1].upper() in common_last_names:
            father_name = lines[0].strip() + " " + lines[1].strip()
            mother_name = lines[2].strip()
        else:
            father_name = lines[0].strip()
            mother_name = " ".join(lines[1:]).strip()
    else:
        if lines[1].upper() in common_last_names or lines[2].upper() in common_last_names:
            father_name = " ".join(lines[:2]).strip()
            mother_name = " ".join(lines[2:]).strip()
        else:
            father_name = lines[0].strip()
            mother_name = " ".join(lines[1:]).strip()

    return father_name, mother_name

def cnh_process(result, side):
    data = []
    if result.documents:
        for doc in result.documents:
            if side == "front":
                fields_of_interest = ["LastName", "FirstName", "DocumentNumber", "DateOfBirth", "DateOfExpiration",
                                      "Sex", "Address", "CountryRegion", "Region", "CPF", "Filiacao", "Validade",
                                      "Habilitacao", "CatHab", "orgEmissor_UF", "Data_Emissao", "Local",
                                      "Doc_Identidade"]
            else:
                fields_of_interest = ["Local", "Data_Emissao", "Filiacao", "Validade"]

            for field_name in fields_of_interest:
                field = doc.fields.get(field_name)
                if field:
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
                    else:
                        data.append({
                            "Nome do Campo": field_name_mapping.get(field_name, field_name),
                            "Valor/Conteúdo": field.content if hasattr(field, 'content') else field.value_string,
                            "Confiança": field.confidence
                        })
    return pd.DataFrame(data)

def rg_process(result):
    data = []
    if result.documents:
        for doc in result.documents:
            fields_of_interest = ["Registro_Geral", "Nome", "Data_De_Expedicao", "Data_De_Nascimento", "Naturalidade",
                                  "Filiacao", "DocOrigem", "CPF", "Assinatura_Do_Diretor"]

            for field_name in fields_of_interest:
                field = doc.fields.get(field_name)
                if field:
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
                    else:
                        data.append({
                            "Nome do Campo": field_name_mapping_rg.get(field_name, field_name),
                            "Valor/Conteúdo": field.content if hasattr(field, 'content') else field.value_string,
                            "Confiança": field.confidence
                        })
    return pd.DataFrame(data)

@app.post("/process_cnh/")
async def process_cnh(front_image: UploadFile = File(...), back_image: UploadFile = File(...)):
    client = DocumentIntelligenceClient(endpoint=ENDPOINT, credential=AzureKeyCredential(API_KEY))
    try:
        front_doc = await front_image.read()
        back_doc = await back_image.read()

        poller_front = client.begin_analyze_document(
            model_id="prebuilt-idDocument",
            analyze_request=AnalyzeDocumentRequest(bytes_source=front_doc),
            features=[DocumentAnalysisFeature.QUERY_FIELDS],
            query_fields=["CPF", "Filiacao", "Validade", "Habilitacao", "CatHab", "orgEmissor_UF", "Data_Emissao",
                          "Local", "Doc_Identidade", "FirstName", "LastName", "DateOfBirth", "DocumentNumber"]
        )
        result_front = poller_front.result()

        poller_back = client.begin_analyze_document(
            model_id="prebuilt-idDocument",
            analyze_request=AnalyzeDocumentRequest(bytes_source=back_doc),
            features=[DocumentAnalysisFeature.QUERY_FIELDS],
            query_fields=["Local", "Data_Emissao", "Filiacao", "Validade"]
        )
        result_back = poller_back.result()

        df_front = cnh_process(result_front, side="front")
        df_back = cnh_process(result_back, side="back")

        return {
            "CNH Front": df_front.to_dict(orient="records"),
            "CNH Back": df_back.to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process_rg/")
async def process_rg(front_image: UploadFile = File(...), back_image: UploadFile = File(...)):
    client = DocumentIntelligenceClient(endpoint=ENDPOINT, credential=AzureKeyCredential(API_KEY))
    try:
        front_doc = await front_image.read()
        back_doc = await back_image.read()

        poller_front = client.begin_analyze_document(
            model_id="prebuilt-idDocument",
            analyze_request=AnalyzeDocumentRequest(bytes_source=front_doc),
            features=[DocumentAnalysisFeature.QUERY_FIELDS],
            query_fields=["Registro_Geral", "Nome", "Data_De_Expedicao", "Naturalidade", "Filiacao",
                          "DocOrigem", "CPF", "Assinatura_Do_Diretor"]
        )
        result_front = poller_front.result()

        poller_back = client.begin_analyze_document(
            model_id="prebuilt-idDocument",
            analyze_request=AnalyzeDocumentRequest(bytes_source=back_doc),
            features=[DocumentAnalysisFeature.QUERY_FIELDS],
            query_fields=["Registro_Geral", "Nome", "Data_De_Expedicao", "Naturalidade", "Filiacao",
                          "DocOrigem", "CPF", "Assinatura_Do_Diretor"]
        )
        result_back = poller_back.result()

        df_front = rg_process(result_front)
        df_back = rg_process(result_back)

        return {
            "RG Front": df_front.to_dict(orient="records"),
            "RG Back": df_back.to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
