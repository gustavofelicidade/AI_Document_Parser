import streamlit as st

from interface.app import Main

st.set_page_config(layout="wide",
                   initial_sidebar_state="expanded",
                   page_icon="👁️"
                   )

# ================================
# START THE AI VISION APPLICATION
# ================================


if __name__ == "__main__":
    main_app = Main()
    main_app.main()
