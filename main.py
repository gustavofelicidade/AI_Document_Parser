import streamlit as st

from interface import app

st.set_page_config(layout="wide",
                   initial_sidebar_state="expanded",
                   page_icon="👁️"
                   )

import subprocess
#================================
# START THE DASHBOARD APPLICATION
#================================

#ok
if __name__=='__main__':


   app.Main().main()



