from bs4 import BeautifulSoup
import re

def extrair_valor(valor_str):

    if not valor_str or valor_str == "-":
        return None

    valor_limpo = re.sub(r"[R$\s\.]", "", valor_str).replace(",", ".")

    try:
        return float(valor_limpo)
    except:
        return None


def parse_lista_licitacoes(html):

    soup = BeautifulSoup(html, "html.parser")
    tabela = soup.find("table", id="tblListaAcompanhamento")

    resultados = []

    if not tabela:
        return resultados

    linhas = tabela.find("tbody").find_all("tr")

    for linha in linhas:
        resultados.append(str(linha))

    return resultados