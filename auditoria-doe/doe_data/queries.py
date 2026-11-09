from sqlalchemy import text
from doe_data.acesso_bd import get_engine
import streamlit as st

def get_publicacoes_por_auditoria(status):
    """Retornar as publicações com o status de auditoria informado.

    Args:
        status: True para corretas, False para erradas e None para não avaliadas.
    """
    query = text("""
                    SELECT link, id, conteudo_link, nro_edicao, dt_edicao
                    FROM vw_publicacao
                    WHERE auditoria IS NOT DISTINCT FROM CAST(:status AS boolean)
                    ORDER BY id;
                    """)
    with get_engine().connect() as conn:
        result = conn.execute(query, {"status": status})
        return result.fetchall()

def get_qtd_publicacoes():
    """Retornar a quantidade de publicações na tabela vw_publicacao

    Returns:
        _type_: _description_
    """
    query = text("SELECT count(id) FROM vw_publicacao;")
    with get_engine().connect() as conn:
        result = conn.execute(query)
        return result.fetchone()

def get_qtd_publicacoes_correta():
    """Retornar a quantidade de publicações na tabela vw_publicacao

    Returns:
        _type_: _description_
    """
    query = text("SELECT count(id) FROM vw_publicacao where auditoria is true;")
    with get_engine().connect() as conn:
        result = conn.execute(query)
        return result.fetchone()

def get_qtd_publicacoes_errada():
    """Retornar a quantidade de publicações na tabela vw_publicacao

    Returns:
        _type_: _description_
    """
    query = text("SELECT count(id) FROM vw_publicacao where auditoria is false;")
    with get_engine().connect() as conn:
        result = conn.execute(query)
        return result.fetchone()

def get_atos(publicacao_id):
    query = text ("""
                    SELECT conteudo_ato
                    FROM processing.ato
                    WHERE publicacao_id = :id
                    """)
    with get_engine().connect() as conn:
        result = conn.execute(query, {"id": publicacao_id})
        return result.fetchall()
    

# Função para atualizar o campo booleano
def update_publicacao_auditoria(publicacao_id, status):
    try:
        query = text("""UPDATE processing.publicacao SET auditoria = :status WHERE id = :id""")
        with get_engine().connect() as conn:
            conn.execute(query, {"status": status, "id": publicacao_id})
            conn.commit()
        st.success(f"Auditoria atualizada para {status}")
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")