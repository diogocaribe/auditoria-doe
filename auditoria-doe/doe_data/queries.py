from sqlalchemy import text
from doe_data.acesso_bd import get_engine
import streamlit as st

def get_publicacoes_por_auditoria(status, tipo_ato_id=None):
    """Retornar as publicações com o status de auditoria informado.

    Args:
        status: True para corretas, False para erradas e None para não avaliadas.
        tipo_ato_id: id em dominio.tipo_ato; quando informado, só retorna as
            publicações que têm ao menos um ato desse tipo.
    """
    query = text("""
                    SELECT p.link, p.id, p.conteudo_link, p.nro_edicao, p.dt_edicao
                    FROM vw_publicacao p
                    WHERE p.auditoria IS NOT DISTINCT FROM CAST(:status AS boolean)
                      AND (
                        CAST(:tipo_ato_id AS integer) IS NULL
                        OR EXISTS (
                            SELECT 1
                            FROM processing.ato a
                            JOIN processing.ato_tipo_ato ata ON ata.ato_id = a.id
                            WHERE a.publicacao_id = p.id
                              AND ata.tipo_ato_id = CAST(:tipo_ato_id AS integer)
                        )
                      )
                    ORDER BY p.id;
                    """)
    with get_engine().connect() as conn:
        result = conn.execute(query, {"status": status, "tipo_ato_id": tipo_ato_id})
        return result.fetchall()

def get_tipos_ato():
    """Retornar os tipos de ato (id, nome, sigla) cadastrados em dominio.tipo_ato."""
    query = text("""
                    SELECT id, nome, nullif(sigla, '') AS sigla
                    FROM dominio.tipo_ato
                    ORDER BY nome;
                    """)
    with get_engine().connect() as conn:
        result = conn.execute(query)
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
    """Retornar os atos da publicação com seus tipos.

    Cada linha traz (conteudo_ato, tipos, nomes_tipo, siglas_tipo):
    - tipos: texto "Nome (SIGLA)" de cada tipo, separados por "; ", ou None
      quando o ato não foi classificado. Um ato pode ter mais de um tipo.
    - nomes_tipo e siglas_tipo: listas com o nome e a sigla de cada tipo
      (vazias quando não classificado), usadas para destacar o tipo no texto.
    """
    query = text ("""
                    SELECT
                        a.conteudo_ato,
                        string_agg(
                            t.nome || coalesce(' (' || nullif(t.sigla, '') || ')', ''),
                            '; ' ORDER BY t.id
                        ) AS tipos,
                        coalesce(
                            array_agg(t.nome ORDER BY t.id) FILTER (WHERE t.id IS NOT NULL),
                            '{}'
                        ) AS nomes_tipo,
                        coalesce(
                            array_agg(nullif(t.sigla, '') ORDER BY t.id) FILTER (WHERE t.id IS NOT NULL),
                            '{}'
                        ) AS siglas_tipo
                    FROM processing.ato a
                    LEFT JOIN processing.ato_tipo_ato ata ON ata.ato_id = a.id
                    LEFT JOIN dominio.tipo_ato t ON t.id = ata.tipo_ato_id
                    WHERE a.publicacao_id = :id
                    GROUP BY a.id, a.conteudo_ato
                    ORDER BY a.id
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