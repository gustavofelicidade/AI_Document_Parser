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
from yaml.loader import SafeLoader



dotenv.load_dotenv()



def main_page():
    # ---- MAINPAGE ----

    col1, col2 = st.columns([10, 4])
    with col2:
        st.markdown("# Getting Start")
        st.subheader('Know how to Scrap')
        ...
    with col1:
        st.markdown("# SNB 🚀")
        # st.subheader('URL Manager ')
        st.write("Follow the next steps to URL process:")

    st.markdown("## URL's")
    st.warning(
        """ \n Insert the URL \n
                Click add url \n
            Select the URL in Checkbox \n
            Click Run Selected ( 1 per time ) \n
            Expand the Dataframe to see""",
        icon="⚠️",
    )


    st.markdown("""---""")


    st.markdown("## URL Elements")
    st.text('All content available')
    # st.text('Select the element and click to hide  rows with empty cells')

    # selected_elements = display_all_elements()
    #
    # st.dataframe(selected_elements)

    st.text("Select elements by tag name")
    # st.dataframe(tag_name)
    st.markdown("""---""")



    st.markdown("""Generate Post""")

    # ===========================================================
    # Section to append data to Google Sheets
    # ===========================================================
    st.markdown("### Post Data to Google Sheets")
    if st.button('Post to Google Sheets'):
        # try:



        # Add prompts to openai before append



        st.success("Data posted successfully to Google Sheets.")
        # except gspread.exceptions.APIError as e:
        #     if e.response.status_code == 429:
        #         st.error("Quota limit reached for Google Sheets API. Please input less content.")
        #     else:
        #         st.error(f"Failed to post data to Google Sheets. Error: {e}")

    # ===========================================================

    st.markdown("""---""")

    # ===========================================================
    # Section to post data to WordPress
    # ===========================================================
    st.markdown("### Post Data to WordPress")
    wordpress_url = st.text_input("WordPress Website URL:", key="wordpress_url")
    content_cell = st.text_input("Cell Coordinate for Content (e.g., 'A1', 'D23'):", key="content_cell")
    if st.button('Submit to WordPress'):
        # Here you would include the logic to post data to WordPress
        # For example, you might retrieve the content from Google Sheets using the content_cell coordinate
        # and then use the WordPress API to post the content to the wordpress_url
        st.success("Content submitted to WordPress.")
    st.markdown("""---""")


    st.markdown("## URL's Sitemap")
    st.text("URL's in this site")


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
