import os
import re
import dotenv
import streamlit as st
import pandas as pd
import yaml
from openai import OpenAI
from yaml.loader import SafeLoader
from dotenv import load_dotenv
from identity_document import analyze_document, main as analyze_folder, ENDPOINT, API_KEY
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE")

# Certifique-se de que as credenciais estão sendo lidas corretamente
if not api_key or not api_base:
    raise ValueError("API key or base URL not found. Please check your .env file.")

# Instantiate the OpenAI client with your API key
client = OpenAI(api_key=api_key)

def cnh_process(result):
    cnh_header = [
        "Nome",
        "Doc. Identidade / Órg. Emissor / UF",
        "CPF",
        "Data de Nascimento",
        "Filiação",
        "Cat. Hab.",
        "N° de Registro",
        "Validade",
        "1° Habilitação"
    ]


    cnh_dict_patterns = {
        "Nome": r"VALIS ([A-Z ]+)",
        "Doc. Identidade / Órg. Emissor / UF": r"IDENTIDADE / ÓRG\. EMISSOR / UF ([0-9A-Z]+)",
        "CPF": r"CPF[ -·]DATA NASCIMENTO ([0-9\.\-]+)",
        "Data de Nascimento": r"DATA NASCIMENTO [0-9\.\-]+ ([0-9/]+)",
        "Filiação": r"FILIAÇÃO[ -]+([A-Z ]+ [A-Z ]+)",
        "Cat. Hab.": r"CAT\.? HAB\.? ([A-Z]+)",
        "N° de Registro": r"Nº REGISTRO --- - ([0-9]+)",
        "Validade": r"VALIDADE ([0-9/]+)",
        "1° Habilitação": r"1[ª°] HABILITAÇÃO ([0-9/]+)",
        "Data Emissão": r"DATA EMISSÃO ([0-9/]+)"
    }

    data = {key: "" for key in cnh_header}

    for page in result.pages:
        page_content = " ".join([line.content for line in page.lines])
        print("========================================================================================")
        print("page_content: \n", page_content)
        print("type: \n", type(page_content))
        print("========================================================================================")
        for key, pattern in cnh_dict_patterns.items():
            match = re.search(pattern, page_content)
            if match:
                data[key] = match.group(1).strip()
    print("========================================================================================")
    print("DATAFRAME: \n", pd.DataFrame([data]).T)
    print("========================================================================================")
    return pd.DataFrame([data])


def rg_process(result):
    cnh_header = [
        "Nome",
        "Doc. Identidade / Órg. Emissor / UF",
        "CPF",
        "Data de Nascimento",
        "Filiação",
        "Cat. Hab.",
        "N° de Registro",
        "Validade",
        "1° Habilitação"
    ]


    cnh_dict_patterns = {
        "Nome": r"VALIS ([A-Z ]+)",
        "Doc. Identidade / Órg. Emissor / UF": r"IDENTIDADE / ÓRG\. EMISSOR / UF ([0-9A-Z]+)",
        "CPF": r"CPF[ -·]DATA NASCIMENTO ([0-9\.\-]+)",
        "Data de Nascimento": r"DATA NASCIMENTO [0-9\.\-]+ ([0-9/]+)",
        "Filiação": r"FILIAÇÃO[ -]+([A-Z ]+ [A-Z ]+)",
        "Cat. Hab.": r"CAT\.? HAB\.? ([A-Z]+)",
        "N° de Registro": r"Nº REGISTRO --- - ([0-9]+)",
        "Validade": r"VALIDADE ([0-9/]+)",
        "1° Habilitação": r"1[ª°] HABILITAÇÃO ([0-9/]+)",
        "Data Emissão": r"DATA EMISSÃO ([0-9/]+)"
    }

    data = {key: "" for key in cnh_header}

    for page in result.pages:
        page_content = " ".join([line.content for line in page.lines])
        print("========================================================================================")
        print("page_content: \n", page_content)
        print("type: \n", type(page_content))
        print("========================================================================================")
        for key, pattern in cnh_dict_patterns.items():
            match = re.search(pattern, page_content)
            if match:
                data[key] = match.group(1).strip()
    print("========================================================================================")
    print("DATAFRAME: \n", pd.DataFrame([data]).T)
    print("========================================================================================")
    return pd.DataFrame([data])


def passaporte_process(result):
    cnh_header = [
        "Nome",
        "Doc. Identidade / Órg. Emissor / UF",
        "CPF",
        "Data de Nascimento",
        "Filiação",
        "Cat. Hab.",
        "N° de Registro",
        "Validade",
        "1° Habilitação"
    ]


    cnh_dict_patterns = {
        "Nome": r"VALIS ([A-Z ]+)",
        "Doc. Identidade / Órg. Emissor / UF": r"IDENTIDADE / ÓRG\. EMISSOR / UF ([0-9A-Z]+)",
        "CPF": r"CPF[ -·]DATA NASCIMENTO ([0-9\.\-]+)",
        "Data de Nascimento": r"DATA NASCIMENTO [0-9\.\-]+ ([0-9/]+)",
        "Filiação": r"FILIAÇÃO[ -]+([A-Z ]+ [A-Z ]+)",
        "Cat. Hab.": r"CAT\.? HAB\.? ([A-Z]+)",
        "N° de Registro": r"Nº REGISTRO --- - ([0-9]+)",
        "Validade": r"VALIDADE ([0-9/]+)",
        "1° Habilitação": r"1[ª°] HABILITAÇÃO ([0-9/]+)",
        "Data Emissão": r"DATA EMISSÃO ([0-9/]+)"
    }

    data = {key: "" for key in cnh_header}

    for page in result.pages:
        page_content = " ".join([line.content for line in page.lines])
        print("========================================================================================")
        print("page_content: \n", page_content)
        print("type: \n", type(page_content))
        print("========================================================================================")
        for key, pattern in cnh_dict_patterns.items():
            match = re.search(pattern, page_content)
            if match:
                data[key] = match.group(1).strip()
    print("========================================================================================")
    print("DATAFRAME: \n", pd.DataFrame([data]).T)
    print("========================================================================================")
    return pd.DataFrame([data])


def analyze_uploaded_document(uploaded_file, document_type):
    client = DocumentAnalysisClient(endpoint=ENDPOINT, credential=AzureKeyCredential(API_KEY))
    document = uploaded_file.read()
    poller = client.begin_analyze_document("prebuilt-idDocument", document)
    result = poller.result()
    print(f"result: {result}")

    if document_type in ["CNH_Verso", "CNH_Aberta", "CNH_Frente"]:
        return cnh_process(result)
    else:
        data = []
        for page in result.pages:
            for line in page.lines:
                data.append({
                    "Content": line.content
                })
        return pd.DataFrame(data)

class Main:

    def __init__(self):
        with open('config.yaml') as file:
            self.config = yaml.load(file, Loader=SafeLoader)

    def main(self):
        # ---- MAINPAGE ----
        col1, col2 = st.columns([10, 4])
        with col2:
            st.markdown("# Document Intelligence")

        with col1:
            st.markdown("# AI Vision 👁️")
            st.write("Follow the next steps to extract data from the documents:")

        st.warning(
            """ \n Insert Image to process \n
                    """,
            icon="⚠️",
        )

        # ---- SIDEBAR ----
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
            st.title("Document Analysis with Azure")
            document_type = st.selectbox("Select document type",
                                         ["CNH_Verso", "CNH_Aberta", "CNH_Frente", "CPF_Frente", "CPF_Verso",
                                          "RG_Aberto", "RG_Frente", "RG_Verso"])
            uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png", "pdf"])
            folder_path = st.text_input("Or enter a folder path to analyze all documents in it:")

            if uploaded_file is not None:
                st.write("Analyzing uploaded document...")
                df = analyze_uploaded_document(uploaded_file, document_type)
                st.write(df)

            if folder_path:
                st.write("Analyzing documents in folder...")
                analyze_folder(folder_path)

            st.markdown("""Footer""")

            # ---- HIDE STREAMLIT STYLE ----
            hide_st_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                </style>
            """
            st.markdown(hide_st_style, unsafe_allow_html=True)

        st.sidebar.markdown("# AI Document Parser")

