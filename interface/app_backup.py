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

field_name_mapping_rg = {
    "Registro_Geral": "Registro_Geral",
    "Nome": "Nome",
    "Data_De_Expedição": "Data_De_Expedição",
    "Naturalidade": "Naturalidade",
    "Filiação": "Filiação",
    "DocOrigem": "DocOrigem",
    "CPF": "CPF",
    "Assinatura_Do_Diretor": "Assinatura_Do_Diretor",

}


def cnh_process(result):
    data = []
    if result.documents:
        for doc in result.documents:
            fields_of_interest = ["LastName", "FirstName", "DocumentNumber", "DateOfBirth", "DateOfExpiration", "Sex",
                                  "Address", "CountryRegion", "Region", "CPF", "Filiacao", "Validade", "Habilitacao",
                                  "CatHab", "orgEmissor_UF", "Data_Emissao", "Local", "Doc_Identidade"]
            for field_name in fields_of_interest:
                field = doc.fields.get(field_name)
                if field:
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
            fields_of_interest = ["Registro_Geral", "Nome", "Data_De_Expedição", "Data_De_Nascimento", "Naturalidade",
                                  "Filiação",
                                  "DocOrigem", "CPF", "Assinatura_Do_Diretor"]
            for field_name in fields_of_interest:
                field = doc.fields.get(field_name)
                if field:
                    data.append({
                        "Nome do Campo": field_name_mapping_rg.get(field_name, field_name),
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
        query_fields=["CPF", "Filiacao", "Validade", "Habilitacao", "CatHab", "orgEmissor_UF", "Data_Emissao", "Local",
                      "Doc_Identidade", "FirstName", "LastName", "DateOfBirth", "DocumentNumber"]
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
            st.image(front_image, caption="CNH Front Image", width=600)
            with col2:
                st.write("Upload Imagem CNH Verso...")
                back_image = st.file_uploader("Upload Imagem CNH Verso...", type=["jpg", "jpeg", "png"], key="back")
                if back_image:
                    st.image(back_image, caption="CNH Back Image", width=300)
                    st.write("Analyzing uploaded documents...")
                    df_front = analyze_uploaded_document(front_image, "CNH_Frente")
                    df_back = analyze_uploaded_document(back_image, "CNH_Verso")
                    st.write("CNH Front Data")
                    st.write(df_front)
                    st.write("CNH Back Data")
                    st.write(df_back)
                else:
                    st.warning("Please upload a Imagem do Verso da CNH.")
                    st.image("example_cnh_back.jpg", caption="Examplo de imagem CNH Verso correta", width=300)
        else:
            st.warning("Please upload the CNH front image.")
            st.image("example_cnh_front.jpg", caption="Example of correct CNH front image", width=300)

    def upload_rg(self):
        rg_image = st.file_uploader("Upload RG Image...", type=["jpg", "jpeg", "png"])
        if rg_image:
            st.image(rg_image, caption="RG Image", width=400)
            st.write("Analyzing uploaded document...")
            df = analyze_uploaded_document(rg_image, "RG_Aberto")
            st.write("RG Data")
            st.write(df)
        else:
            st.warning("Please upload the RG image.")
            st.image("example_rg.jpg", caption="Examplo de imagem RG correta", width=400)


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

        st.warning("Insira a imagem do Documento para processar", icon="⚠️")

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
