import streamlit as st
import psycopg2
import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar a conexão com o Azurite
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
# Criar um cliente BlobService
blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

# Nome do container de Blob
CONTAINER_NAME = "imagens"

# Criar o container se ele não existir
container_client = blob_service_client.get_container_client(CONTAINER_NAME)
try:
    container_client.create_container()
except Exception as e:
    print(f"Container already exists: {e}")

# Função para inserir a imagem no Blob Storage
def upload_image_to_blob(file_name, file_data):
    # Criar um BlobClient para interagir com o blob
    blob_client = container_client.get_blob_client(blob=file_name)

    # Certifique-se de que o file_data seja do tipo bytes
    if isinstance(file_data, memoryview):  # memoryview é o tipo retornado por getbuffer()
        file_data = file_data.tobytes()  # Converte memoryview para bytes

    # Upload da imagem para o Blob Storage
    try:
        blob_client.upload_blob(file_data, overwrite=True)
        print(f"Imagem '{file_name}' enviada para o Blob Storage.")
    except Exception as e:
        print(f"Erro ao enviar a imagem para o Blob Storage: {e}")

