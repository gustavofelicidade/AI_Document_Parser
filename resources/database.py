import streamlit as st
import psycopg2
import os
from dotenv import load_dotenv

# Initialize connection using hardcoded credentials
# def init_connection():
#     return psycopg2.connect(
#         host="localhost",
#         port="5432",
#         dbname="vision",
#         user="postgres",
#         password="123",
#     )

# conn = init_connection()



# Carregar variáveis de ambiente
load_dotenv()

# Função para inicializar a conexão com o banco de dados
# def init_connection():
#     return psycopg2.connect(
#         host=os.getenv("DB_HOST"),
#         port=os.getenv("DB_PORT"),
#         dbname=os.getenv("DB_NAME"),
#         user=os.getenv("DB_USER"),
#         password=os.getenv("DB_PASSWORD"),
#     )


# conn = init_connection()
# cur = conn.cursor()
#
# # Função para inserir o caminho e os dados da imagem no banco de dados
# def insert_image(file_path, file_data):
#     cur.execute("""
#         INSERT INTO public.users (file_path, file_data)
#         VALUES (%s, %s)
#     """, (file_path, psycopg2.Binary(file_data)))
#     conn.commit()


# RAILWAY Postgres Database
# Função para inicializar a conexão com o banco de dados usando a URL completa
def init_connection():
    return psycopg2.connect("postgresql://postgres:NpSHCrCCkaRwweKqRGEVgpYyoGdIPUAn@viaduct.proxy.rlwy.net:57554/railway")

conn = init_connection()
cur = conn.cursor()

# Função para inserir o caminho e os dados da imagem no banco de dados
def insert_image(file_path, file_data):
    cur.execute("""
        INSERT INTO public.users (file_path, file_data) 
        VALUES (%s, %s)
    """, (file_path, psycopg2.Binary(file_data)))
    conn.commit()