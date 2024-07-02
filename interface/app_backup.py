
import streamlit as st
import pandas as pd
import yaml

from yaml.loader import SafeLoader
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import DocumentAnalysisFeature, AnalyzeDocumentRequest

# Carregar variáveis de ambiente
load_dotenv()

ENDPOINT = "https://visiondocument01.cognitiveservices.azure.com/"
API_KEY = "e30f60769b204e79ade3cd9ac8d1f389"


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
# Mapeamento dos campos em inglês para português

def cnh_process(result):
    data = []
    if result.documents:
        for doc in result.documents:
            fields_of_interest = ["LastName", "FirstName", "DocumentNumber", "DateOfBirth", "DateOfExpiration", "Sex", "Address", "CountryRegion", "Region", "CPF", "Filiacao", "Validade", "Habilitacao", "CatHab", "orgEmissor_UF", "Data_Emissao", "Local", "Doc_Identidade"]
            for field_name in fields_of_interest:
                field = doc.fields.get(field_name)
                if field:
                    data.append({
                        "Nome do Campo": field_name_mapping.get(field_name, field_name),
                        "Valor/Conteúdo": field.content if hasattr(field, 'content') else field.value_string,
                        "Confiança": field.confidence
                    })
    return pd.DataFrame(data)


def analyze_uploaded_document(uploaded_file, document_type):
    client = DocumentIntelligenceClient(endpoint=ENDPOINT, credential=AzureKeyCredential(API_KEY))
    document = uploaded_file.read()

    poller = client.begin_analyze_document(
        model_id="prebuilt-idDocument",
        analyze_request=AnalyzeDocumentRequest(bytes_source=document),

        features=[DocumentAnalysisFeature.QUERY_FIELDS],
        query_fields=["CPF", "Filiacao", "Validade", "Habilitacao", "CatHab", "orgEmissor_UF", "Data_Emissao", "Local", "Doc_Identidade", "FirstName", "LastName", "DateOfBirth", "DocumentNumber"]
    )

    result = poller.result()

    if document_type in ["CNH_Verso", "CNH_Aberta", "CNH_Frente"]:
        return cnh_process(result)
    else:
        data = []
        for page in result.pages:
            for line in page.lines:
                data.append({"Content": line.content})
        return pd.DataFrame(data)


class Homepage:
    def __init__(self):
        st.title("Document Analysis with Azure")
        document_type = st.selectbox("Select document type", ["CNH_Verso", "CNH_Aberta", "CNH_Frente", "CPF_Frente", "CPF_Verso", "RG_Aberto", "RG_Frente", "RG_Verso"])
        uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png", "pdf"])

        if uploaded_file is not None:
            st.write("Analyzing uploaded document...")
            df = analyze_uploaded_document(uploaded_file, document_type)
            st.write(df)


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
            st.write("Follow the next steps to extract data from the documents:")

        st.warning("Insert Image to process", icon="⚠️")

        # Sidebar
        global name
        name = "Client"
        st.sidebar.title(f"Welcome {name}")

        button = st.sidebar.button("Logout")
        if button:
            self.logout()

        option = st.sidebar.radio(
            'Navigate through various features of the app!',
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

