#!/bin/bash

# Stop the script if any command fails
set -e

# Streamlit-specific setup
mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
" > ~/.streamlit/config.toml

echo "Setup completed."
