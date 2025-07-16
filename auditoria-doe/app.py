import streamlit as st
from doe_data.queries import (
    get_publicacoes_auditoria_not_null,
    get_atos,
    update_publicacao_auditoria,
    get_qtd_publicacoes,
    get_qtd_publicacoes_correta,
    get_qtd_publicacoes_errada
)
from utils import destacar_trechos, remover_hifen_lista
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


publicacoes = get_publicacoes_auditoria_not_null()
links = [row[0] for row in publicacoes]
ids = [row[1] for row in publicacoes]
conteudos_link = [row[2] for row in publicacoes]
nro_edicao = [row[3] for row in publicacoes]
dt_edicao = [row[4] for row in publicacoes]


if "index" not in st.session_state:
    st.session_state.index = 0

qtd_publicacoes = get_qtd_publicacoes()
qtd_publicacoes_correta = get_qtd_publicacoes_correta()
qtd_publicacoes_errada = get_qtd_publicacoes_errada()
if qtd_publicacoes:
    st.sidebar.markdown(f"""
        **Publicações:** \n
            Total: {qtd_publicacoes[0]}
            Corretas: {qtd_publicacoes_correta[0]}
            Erradas: {qtd_publicacoes_errada[0]}
            Não Avaliadas: {qtd_publicacoes[0] - (qtd_publicacoes_correta[0] + qtd_publicacoes_errada[0])}
    """)

    # Criar dados para o gráfico
    labels = ['Corretas', 'Erradas', 'Não Avaliadas']
    values = [
        qtd_publicacoes_correta[0],
        qtd_publicacoes_errada[0],
        qtd_publicacoes[0] - (qtd_publicacoes_correta[0] + qtd_publicacoes_errada[0])
    ]
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

            with col4:
                if st.button("✅ Correta", key="btn_correta"):
                    update_publicacao_auditoria(ids[i], True)
                    if st.session_state.index < len(links) - 1:
                        st.session_state.index += 1

            with col5:
                if st.button("❌ Errada", key="btn_errada"):
                    update_publicacao_auditoria(ids[i], False)
                    if st.session_state.index < len(links) - 1:
                        st.session_state.index += 1
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
                    
                    st.markdown(
                        f"""
                        <div 
                            style='border:1px solid #ccc; 
                            padding:10px;
                            margin:10px 0;
                            text-align: justify;
                            background-color:{background_color};'>
                        {texto_ato}
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
