# carregando as funções em outros arquivos .py
import resources.database as db
import streamlit as st
import hashlib


def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()


def check_hashes(password,hashed_text):

    if make_hashes(password) == hashed_text:
        return hashed_text

    return False


conn = db.init_connection()
cur = conn.cursor()

# função para inserir registros no banco de dados
def insert(nome, idade, profissao):
    # Incluir registros no banco de dados
    cur.execute("""
            INSERT into rocket_kitches.item_analysis (nome, idade, profissao) 
            values('%s', '%s', '%s')
    """ % (nome, idade, profissao))
    conn.commit()

# função para excluir registros no banco de dados
def delete(id):
    # excluir registros no  banco de dados
    cur.execute("""
            DELETE FROM clientes WHERE id = '%s'
    """ % (id))
    conn.commit()

# função para alterar registros no banco de dados
def update(nome, idade, profissao, id):
    # alterar registros no banco de dados
    cur.execute("""
            UPDATE clientes SET (nome, idade, profissao) = ('%s', '%s', '%s')  WHERE id = '%s'
    """ % (nome, idade, profissao, id))
    conn.commit()

# função para selecionar todos os registros no banco de dados
def select():
    # selecionar registros no banco de dados
    cur.execute("""SELECT * FROM vision.users;""")
    recset = cur.fetchall()
    rows = []
    for rec in recset:
        rows.append(rec)
    return rows

# função para selecionar apenas um registros no banco de dados
def select_id(id):
    cur.execute("""
            SELECT * FROM vision.users WHERE id = '%s'
    """ % (id))
    recset = cur.fetchall()
    rows = []
    for rec in recset:
        rows.append(rec)
    return rows



# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def run_query(query):
    with cur:
        # cur.execute("SET search_path TO rocket_kitchens")
        cur.execute(query)
        return cur.fetchall()


# https://blog.jcharistech.com/2020/05/30/how-to-add-a-login-section-to-streamlit-blog-app/
# # DB Management
# import sqlite3
# conn = sqlite3.connect('data.db')
# c = conn.cursor()
def create_usertable():
    cur.execute("""CREATE TABLE IF NOT EXISTS vision.users(username TEXT,password TEXT)""")


def add_userdata(username, password):
    cur.execute("""INSERT into vision.users(username,password) VALUES ('%s', '%s')""" % (username, password))
    conn.commit()


def login_user(username, password):
    cur.execute("""SELECT * FROM vision.users WHERE username = '%s' AND password = '%s' """ % (username, password))
    data = cur.fetchall()
    return data


def view_all_users():
    cur.execute('SELECT * FROM vision.users')
    data = cur.fetchall()
    return data