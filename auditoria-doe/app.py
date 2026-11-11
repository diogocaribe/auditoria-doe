import streamlit as st
from doe_data.queries import (
    get_publicacoes_por_auditoria,
    get_atos,
    get_tipos_ato,
    update_publicacao_auditoria,
    get_qtd_publicacoes,
    get_qtd_publicacoes_correta,
    get_qtd_publicacoes_errada
)
from utils import destacar_tipo_ato, destacar_trechos, remover_hifen_lista
import plotly.graph_objects as go
import httpx
import re

st.set_page_config(
    layout="wide",
    initial_sidebar_state="collapsed",  # Opções: "expanded", "collapsed", "auto"
)



# Adicionar o header
st.markdown("""
    <div style='background-color: #0e1117; padding: 0.5rem; border-radius: 5px; margin-bottom: 1rem'>
        <h1 style='color: white; text-align: center; margin: 0; font-size: 1.5rem'>
            📝 Auditoria DOE
        </h1>
        <p style='color: #9e9e9e; text-align: center; margin: 0.2rem 0 0 0; font-size: 0.9rem'>
            Sistema de Auditoria de Publicações do Diário Oficial do Estado
        </p>
    </div>
""", unsafe_allow_html=True)


FILTROS_AUDITORIA = {"Não avaliadas": None, "Corretas": True, "Erradas": False}
ICONES_FILTRO = {"Não avaliadas": "⚪", "Corretas": "✅", "Erradas": "❌"}

# Contagens lidas antes da barra de filtros, que mostra o total de cada status
qtd_total = (get_qtd_publicacoes() or [0])[0]
qtd_corretas = (get_qtd_publicacoes_correta() or [0])[0]
qtd_erradas = (get_qtd_publicacoes_errada() or [0])[0]
qtd_nao_avaliadas = qtd_total - (qtd_corretas + qtd_erradas)
QTD_POR_FILTRO = {
    "Não avaliadas": qtd_nao_avaliadas,
    "Corretas": qtd_corretas,
    "Erradas": qtd_erradas,
}

if "filtro_auditoria" not in st.session_state:
    st.session_state.filtro_auditoria = "Não avaliadas"
if "filtro_anterior" not in st.session_state:
    st.session_state.filtro_anterior = st.session_state.filtro_auditoria


def mudar_filtro():
    # O segmented_control permite desmarcar a opção atual; nesse caso a
    # seleção anterior é mantida para que sempre haja um filtro ativo
    if st.session_state.filtro_auditoria is None:
        st.session_state.filtro_auditoria = st.session_state.filtro_anterior
        return
    st.session_state.filtro_anterior = st.session_state.filtro_auditoria
    st.session_state.index = 0


def mudar_filtro_tipo_ato():
    st.session_state.index = 0


# Rótulo de cada tipo de ato no seletor, indexado pelo id; None mostra todas
TIPOS_ATO = {
    tipo_id: f"{nome} ({sigla})" if sigla else nome
    for tipo_id, nome, sigla in get_tipos_ato()
}


# A barra vem antes da consulta para que a lista já reflita a opção escolhida.
# As contagens ficam fora dos rótulos das opções: o id do widget inclui os
# rótulos, e mudar as contagens faria o filtro voltar ao padrão.
with st.container(border=True):
    col_filtro, col_tipo_ato, col_indicador = st.columns(
        [1, 2, 4], vertical_alignment="center"
    )
    with col_filtro:
        # Rótulo em duas linhas fora do selectbox, cujo rótulo não quebra linha
        st.markdown(
            "<div style='text-align: center; font-size: 0.875rem'>"
            "Auditoria<br>Transformação/Separação Atos</div>",
            unsafe_allow_html=True,
        )
        filtro_auditoria = st.selectbox(
            "Auditoria Transformação/Separação Atos",
            label_visibility="collapsed",
            options=list(FILTROS_AUDITORIA),
            format_func=lambda op: f"{ICONES_FILTRO[op]} {op}",
            key="filtro_auditoria",
            on_change=mudar_filtro,
        )
    with col_tipo_ato:
        st.markdown(
            "<div style='text-align: center; font-size: 0.875rem'>"
            "Tipo de ato<br>Publicações que possuem o ato</div>",
            unsafe_allow_html=True,
        )
        filtro_tipo_ato = st.selectbox(
            "Tipo de ato",
            label_visibility="collapsed",
            options=[None, *TIPOS_ATO],
            format_func=lambda op: "Todos os tipos" if op is None else TIPOS_ATO[op],
            key="filtro_tipo_ato",
            on_change=mudar_filtro_tipo_ato,
        )

status_auditoria = FILTROS_AUDITORIA[filtro_auditoria]
somente_leitura = status_auditoria is not None

publicacoes = get_publicacoes_por_auditoria(status_auditoria, filtro_tipo_ato)
links = [row[0] for row in publicacoes]
ids = [row[1] for row in publicacoes]
conteudos_link = [row[2] for row in publicacoes]
nro_edicao = [row[3] for row in publicacoes]
dt_edicao = [row[4] for row in publicacoes]


if "index" not in st.session_state:
    st.session_state.index = 0

# A fila encolhe conforme as publicações são avaliadas
st.session_state.index = min(st.session_state.index, max(len(links) - 1, 0))

if qtd_total:
    st.sidebar.markdown(f"""
        **Publicações:** \n
            Total: {qtd_total}
            Corretas: {qtd_corretas}
            Erradas: {qtd_erradas}
            Não Avaliadas: {qtd_nao_avaliadas}
    """)

    # Criar dados para o gráfico
    labels = ['Corretas', 'Erradas', 'Não Avaliadas']
    values = [qtd_corretas, qtd_erradas, qtd_nao_avaliadas]
    colors = ['#00FF00', '#FF0000', "#B9B9B9"]  # Verde, Vermelho, Cinza

    # Criar gráfico de pizza
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.3,  # Faz um donut chart
        marker_colors=colors
    )])

    # Atualizar layout
    fig.update_layout(
        title="Status Auditoria",
        title_x=0,  # Centraliza o título
        showlegend=True,
        width=400,
        height=400,
        legend=dict(
            orientation="h",  # Orientação horizontal
            yanchor="top",   # Âncora no topo
            y=-0.2,         # Posição Y (negativo para ficar abaixo do gráfico)
            xanchor="center", # Âncora no centro
            x=0.5,          # Posição X centralizada
        )
    )

    # Mostrar o gráfico na sidebar
    with st.sidebar:
        st.markdown("---")  # Adiciona uma linha divisória
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")  # Adiciona uma linha divisória

# Botão para voltar e avançar
with st.container():
    st.markdown("""
        <style>
        .stHorizontalBlock {
            display: flex;
            align-items: middle;
            justify-content: center;
        }
        .stButton>button {
            width: 100%;
            margin: 0 auto;
        }
        .avaliacao-box {
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ddd;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
        }
        </style>
    """, unsafe_allow_html=True)
    col4, col5, col3 = st.columns([1, 1, 1])
    with col4:
        if st.button("Anterior") and st.session_state.index > 0:
            st.session_state.index -= 1
    with col5:
        if st.button("Próximo") and st.session_state.index < len(links) - 1:
            st.session_state.index += 1
        with col3:            
            # st.markdown("<div class='avaliacao-box'>", unsafe_allow_html=True)
            col4, col5 = st.columns([1, 1])
            i = st.session_state.index
            publicacao_id = ids[i] if ids else None

            # A gravação fica em on_click para rodar antes de o script recarregar
            # a fila. O item avaliado sai da fila e o próximo assume o mesmo
            # índice, por isso o índice não é incrementado aqui.
            with col4:
                st.button(
                    "✅ Correta",
                    key="btn_correta",
                    disabled=publicacao_id is None or somente_leitura,
                    on_click=update_publicacao_auditoria,
                    args=(publicacao_id, True),
                )

            with col5:
                st.button(
                    "❌ Errada",
                    key="btn_errada",
                    disabled=publicacao_id is None or somente_leitura,
                    on_click=update_publicacao_auditoria,
                    args=(publicacao_id, False),
                )
            st.markdown("</div>", unsafe_allow_html=True)


with st.container():
    if links:
        i = st.session_state.index
        st.write(f"Edicao nº **{nro_edicao[i]}** ({dt_edicao[i]}): {links[i]}")
        col_ato, col_publicacao, col_link = st.columns([2, 2, 2])

        with col_ato:
            st.markdown("##### ATOS")
            atos = get_atos(ids[i])
            if atos:
                for j, ato in enumerate(atos, start=0):
                    texto_ato = remover_hifen_lista(ato[0])
                    # Verifica se o texto termina com alguma das assinaturas esperadas
                    termina_corretamente = any(
                        texto_ato.strip().endswith(assinatura) 
                        for assinatura in [
                            "Geral",
                            "Geral.",
                            "Diretor Geral",
                            "Diretor Geral."
                            "Diretora Geral",
                            "Diretora Geral.",
                            "Diretora Geral do INEMA",
                            "Diretoria Geral",
                            "Diretoria Geral.",
                            "Secretário",
                            "Presidente",
                            "GOZO",
                            "contrário."
                        ]
                    )
                    
                    background_color = "#f9f9f9" if termina_corretamente else "#fdd1d8"  # cor normal ou rosa claro

                    tipos_ato = ato[1] or "Tipo não classificado"
                    # O destaque vem depois da checagem de assinatura, que
                    # precisa do texto sem as marcações HTML
                    texto_ato_destacado = destacar_tipo_ato(texto_ato, ato[2], ato[3])

                    st.markdown(
                        f"""
                        <div style='margin:10px 0 -10px 0; font-weight:bold; font-size:0.9rem;'>
                        🏷️ {tipos_ato}
                        </div>
                        <div
                            style='border:1px solid #ccc; 
                            padding:10px;
                            margin:10px 0;
                            text-align: justify;
                            background-color:{background_color};'>
                        {texto_ato_destacado}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("Nenhum conteúdo relacionado")
        with col_publicacao:
            st.markdown("##### PUBLICAÇÃO")

            texto_publicacao = remover_hifen_lista(conteudos_link[i])

            # Extrair só o texto dos atos (supondo que ato[0] seja o texto)
            lista_atos = [remover_hifen_lista(ato[0]) for ato in atos] if atos else []

            texto_destacado = destacar_trechos(texto_publicacao, lista_atos)

            st.markdown(
                f"""
                <div
                    style='border:1px solid #ccc; 
                    padding:10px;
                    margin:10px;
                    text-align: justify;
                    background-color:#f0f0f0;'
                >
                    {texto_destacado}
                """,
                unsafe_allow_html=True,
            )

        with col_link:
            st.markdown("#### LINK")
            try:
                with httpx.Client(verify=False) as client:
                    response = client.get(links[i])
                    response.raise_for_status()
                    st.markdown(
                        f"""
                        <div 
                            style='border:1px solid #ccc; 
                            padding:10px;
                            margin:10px;
                            text-align: justify;
                            background-color:#f9f9f9;'>
                        {response.text}
                        """,
                        unsafe_allow_html=True,
                    )
            except Exception as e:
                st.error(f"Erro ao carregar o link: {e}")
    else:
        st.warning("Nenhum dado encontrado")
