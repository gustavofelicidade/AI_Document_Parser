import os

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.ai.documentintelligence.models import DocumentAnalysisFeature, AnalyzeDocumentRequest

# Configurações de endpoint e chave da API
endpoint = "https://visiondocument01.cognitiveservices.azure.com/"
key = "e30f60769b204e79ade3cd9ac8d1f389"

# Gustavo personal document
form_path = r"C:\Users\Dell\Documents\SDLabs\AI_Document_Parser\AI_Vision\Document_data_sample\BID Sample Dataset\CNH_Aberta\00000002_in.jpg"

document_analysis_client = DocumentIntelligenceClient(
    endpoint=endpoint, credential=AzureKeyCredential(key)
)

# Ler o conteúdo do arquivo
with open(form_path, "rb") as file:
    form_data = file.read()

# Chamar a função de análise
poller = document_analysis_client.begin_analyze_document(
    model_id="prebuilt-idDocument",
    analyze_request=AnalyzeDocumentRequest(bytes_source=form_data),

    features=[DocumentAnalysisFeature.QUERY_FIELDS],  # Adicionar a capacidade de QUERY_FIELDS
    query_fields=[
        "CPF",
        "Filiacao",
        "Validade",
        "Habilitacao",
        "CatHab",
        "orgEmissor_UF",
        "Data_Emissao",
        "Local",
        "Doc_Identidade"
    ]
)

id_documents = poller.result()

for idx, id_document in enumerate(id_documents.documents):
    print("--------Recognizing ID document #{}--------".format(idx + 1))
    first_name = id_document.fields.get("FirstName")
    if first_name:
        print(
            "First Name: {} has confidence: {}".format(
                first_name.value_string, first_name.confidence
            )
        )
    last_name = id_document.fields.get("LastName")
    if last_name:
        print(
            "Last Name: {} has confidence: {}".format(
                last_name.value_string, last_name.confidence
            )
        )
    document_number = id_document.fields.get("DocumentNumber")
    if document_number:
        print(
            "Document Number: {} has confidence: {}".format(
                document_number.value_string, document_number.confidence
            )
        )
    dob = id_document.fields.get("DateOfBirth")
    if dob:
        print(
            "Date of Birth: {} has confidence: {}".format(dob.content, dob.confidence)
        )
    doe = id_document.fields.get("DateOfExpiration")
    if doe:
        print(
            "Date of Expiration: {} has confidence: {}".format(
                doe.content, doe.confidence
            )
        )
    sex = id_document.fields.get("Sex")
    if sex:
        print("Sex: {} has confidence: {}".format(sex.content, sex.confidence))
    address = id_document.fields.get("Address")
    if address:
        print(
            "Address: {} has confidence: {}".format(
                address.value_string, address.confidence
            )
        )
    country_region = id_document.fields.get("CountryRegion")
    if country_region:
        print(
            "Country/Region: {} has confidence: {}".format(
                country_region.value_string, country_region.confidence
            )
        )
    region = id_document.fields.get("Region")
    if region:
        print(
            "Region: {} has confidence: {}".format(region.value_string, region.confidence)
        )

    CPF = id_document.fields.get("CPF")
    if CPF:
        print(
            "CPF: {} has confidence: {}".format(CPF.value_string, CPF.confidence)
        )
    filiacao = id_document.fields.get("Filiacao")
    if filiacao:
        print(
            "Filiacao: {} has confidence: {}".format(filiacao.value_string, filiacao.confidence)
        )
    validade = id_document.fields.get("Validade")
    if validade:
        print(
            "Validade: {} has confidence: {}".format(validade.value_string, validade.confidence)
        )
    habilitacao = id_document.fields.get("Habilitacao")
    if habilitacao:
        print(
            "Habilitacao: {} has confidence: {}".format(habilitacao.content, habilitacao.confidence)
        )
    cathab = id_document.fields.get("CatHab")
    if cathab:
        print(
            "CatHab: {} has confidence: {}".format(cathab.value_string, cathab.confidence)
        )
    orgemissor_uf = id_document.fields.get("orgEmissor_UF")
    if orgemissor_uf:
        print(
            "orgEmissor_UF: {} has confidence: {}".format(orgemissor_uf.value_string, orgemissor_uf.confidence)
        )
    data_emissao = id_document.fields.get("Data_Emissao")
    if data_emissao:
        print(
            "Data_Emissao: {} has confidence: {}".format(data_emissao.content, data_emissao.confidence)
        )
    local = id_document.fields.get("Local")
    if local:
        print(
            "Local: {} has confidence: {}".format(local.value_string, local.confidence)
        )
    doc_identidade = id_document.fields.get("Doc_Identidade")
    if doc_identidade:
        print(
            "Doc_Identidade: {} has confidence: {}".format(doc_identidade.value_string, doc_identidade.confidence)
        )
