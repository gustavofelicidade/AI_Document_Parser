import streamlit as st

from interface.app import Main

st.set_page_config(layout="wide",
                   initial_sidebar_state="expanded",
                   page_icon="👁️"
                   )

import subprocess

# ================================
# START THE DASHBOARD APPLICATION
# ================================

# ok
if __name__ == '__main__':
    Main().main()
