import os
import time
import dotenv
import streamlit as st
import pandas as pd
import yaml
from openai import OpenAI
from yaml.loader import SafeLoader

from identity_document import analyze_document, main as analyze_folder, ENDPOINT, API_KEY
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient

# Load the OPENAI_API_KEY from your environment variables
api_key = "OPENAI_API_KEY"

# Instantiate the OpenAI client with your API key
client = OpenAI(api_key=api_key)

dotenv.load_dotenv()


def analyze_uploaded_document(uploaded_file):
    client = DocumentAnalysisClient(endpoint=ENDPOINT, credential=AzureKeyCredential(API_KEY))
    document = uploaded_file.read()
    poller = client.begin_analyze_document("prebuilt-idDocument", document)
    result = poller.result()
    print(f"result: {result}")
    data = []
    for doc in result.documents:
        for field in doc.fields.values():
            data.append({
                "Field": field,

            })
    print(pd.DataFrame(data))
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
            # st.subheader('...')

        with col1:
            st.markdown("# AI Vision 👁️")
            # st.subheader('URL Manager ')
            st.write("Follow the next steps extract data from the documents:")

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

        c = ['Home', 'Dashboard', 'Chat', 'Communication']

        option = st.sidebar.radio(
            'Navigate through various features of the app!',
            # ('Home', 'Dashboard', 'Communication', 'Chat'),
            ('Home', 'Dashboard'),
            key="main_option"
        )

        if option == 'Home':
            st.title("Document Analysis with Azure")
            uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png", "pdf"])
            folder_path = st.text_input("Or enter a folder path to analyze all documents in it:")

            if uploaded_file is not None:
                st.write("Analyzing uploaded document...")
                df = analyze_uploaded_document(uploaded_file)
                st.write(df)

            if folder_path:
                st.write("Analyzing documents in folder...")
                analyze_folder(folder_path)


            # pass
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
