import os
import time
import dotenv
import streamlit as st
import streamlit_authenticator as stauth

from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json
from collections import defaultdict
import yaml
from openai import OpenAI
from yaml.loader import SafeLoader

# Load the OPENAI_API_KEY from your environment variables
api_key = os.getenv("OPENAI_API_KEY")

# Instantiate the OpenAI client with your API key
client = OpenAI(api_key=api_key)

dotenv.load_dotenv()



def main_page():
    # ---- MAINPAGE ----

    col1, col2 = st.columns([10, 4])
    with col2:
        st.markdown("# Document Intelligence")
        st.subheader('...')
        ...
    with col1:
        st.markdown("# AI Vision 👁️")
        # st.subheader('URL Manager ')
        st.write("Follow the next steps extract data from the documents:")


    st.warning(
        """ \n Insert the URL \n
                Click add url \n
            Select the URL in Checkbox \n
            Click Run Selected ( 1 per time ) \n
            Expand the Dataframe to see""",
        icon="⚠️",
    )


    st.markdown("""---""")



    st.markdown("""---""")




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


class Main:

    def __init__(self):

        with open('config.yaml') as file:
            self.config = yaml.load(file, Loader=SafeLoader)

        ...



    def main(self):

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
            main_page()
            # pass

        st.sidebar.markdown("# AI Document Parser")
