import re


def destacar_trechos(texto, trechos_para_destacar):
    for trecho in trechos_para_destacar:
        if trecho in texto:
            texto = texto.replace(
                trecho,
                f"<span style='background-color: #FFE4C4; color: black;'>{trecho}</span> ┃",
            )
    return texto


ESTILO_DESTAQUE_TIPO = (
    "background-color: #FFF176; color: black; font-weight: bold; "
    "border-radius: 3px; padding: 0 2px;"
)


# O texto do DOE varia a preposição em relação ao nome do tipo, por exemplo
# "Autorização para Supressão da Vegetação" para o tipo "Autorização de
# Supressão de Vegetação". Por isso qualquer uma delas casa com qualquer outra.
PREPOSICOES = {"de", "da", "do", "das", "dos", "para", "pela", "pelo"}
PADRAO_PREPOSICAO = r"(?:" + "|".join(sorted(PREPOSICOES, key=len, reverse=True)) + ")"


# Expressões que o texto do DOE usa para um tipo sem citar o nome dele,
# indexadas pelo nome ou pela sigla do tipo em dominio.tipo_ato. Elas seguem as mesmas
# regras do nome: sem diferenciar maiúsculas, com qualquer espaço entre as
# palavras e com as preposições intercambiáveis. A palavra XX marca uma parte
# que varia, como o prazo em "por 02 (dois) anos", e casa com qualquer trecho
# curto sem vírgula, ponto ou ponto e vírgula.
CORINGA = "XX"
PADRAO_CORINGA = r"[^,.;]{1,40}?"

EXPRESSOES_TIPO = {
    "Outorga de Direito de Uso de Recurso Hídrico": [
        "Autorizar o direito de uso dos recursos hídricos",
    ],
    "ROUT": [
        "Autorizar a renovação do direito de uso dos recursos hídricos",
    ],
    "AMOUT": [
        "Autorizar a ampliação da outorga do direito de uso dos recursos hídricos",
    ],
    "AOUT": [
        "Autorizar a alteração da outorga do direito de uso dos recursos hídricos",
    ],
    "PPV/OUT": [
        "Prorrogação do Prazo de Validade, por XX anos a partir da data do "
        "vencimento, da Outorga de direito de uso da água",
    ],
}


def destacar_tipo_ato(texto, nomes_tipo, siglas_tipo):
    """Destacar no texto do ato os trechos que correspondem aos seus tipos.

    O banco não guarda o trecho que levou à classificação, então o destaque é
    feito por busca. O nome do tipo é procurado sem diferenciar maiúsculas e
    aceitando qualquer espaço em branco entre as palavras, já que o texto do
    DOE quebra linhas no meio das expressões. A sigla é procurada em caixa
    alta e como palavra isolada, para não casar com pedaços de outras palavras
    (ela costuma aparecer no número do processo, como "TEC/AIMU-0642").
    """
    nomes_tipo = list(nomes_tipo or [])
    siglas_tipo = list(siglas_tipo or [])
    # As listas vêm alinhadas por tipo, então nome e sigla de cada um ficam juntos
    tipos = zip(nomes_tipo, siglas_tipo + [None] * (len(nomes_tipo) - len(siglas_tipo)))
    padroes = []
    for nome, sigla in tipos:
        extras = [*EXPRESSOES_TIPO.get(nome, []), *EXPRESSOES_TIPO.get(sigla, [])]
        for expressao in filter(None, [nome, *extras]):
            palavras = [
                PADRAO_CORINGA if p == CORINGA
                else PADRAO_PREPOSICAO if p.lower() in PREPOSICOES
                else re.escape(p)
                for p in expressao.split()
            ]
            padroes.append(r"(?i:\b" + r"\s+".join(palavras) + r"\b)")
    for sigla in filter(None, siglas_tipo):
        padroes.append(r"(?<![\w/])" + re.escape(sigla) + r"(?![\w/])")
    if not padroes:
        return texto

    # Os padrões mais longos vêm primeiro para que "Renovação de Licença de
    # Operação" tenha prioridade sobre "Licença de Operação" no mesmo trecho.
    padroes.sort(key=len, reverse=True)
    regex = re.compile("|".join(padroes))
    return regex.sub(
        lambda m: f"<mark style='{ESTILO_DESTAQUE_TIPO}'>{m.group(0)}</mark>",
        texto,
    )


def remover_hifen_lista(texto):
    # Remove hífen no início de linha seguido por espaço
    texto = re.sub(r"(?m)^-\s+", "", texto)
    # Substitui o caractere corrompido '' (U+F0B0) por 'º' (U+00BA)
    texto = texto.replace("", "º")
    return texto