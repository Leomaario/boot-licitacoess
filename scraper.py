from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
import logging

from config import *
from parser import extrair_valor
from utils import retry


class Scraper:

    def __init__(self):

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=HEADLESS
        )

        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0"
        )

        self.page = self.context.new_page()

    def abrir_formulario(self):

        self.page.goto(URL_FORMULARIO, timeout=TIMEOUT)

        self.page.wait_for_load_state("networkidle")

        iframe = self.page.frame(name="iframe-system")

        return iframe if iframe else self.page

    def buscar_categoria(self, nome, codigo):

        logging.info(f"Buscando categoria {nome}")

        contexto = self.abrir_formulario()

        contexto.select_option("#selSitLicitacao", value="2")
        contexto.select_option("#selGrupo", value=codigo)

        contexto.evaluate(
            f"document.querySelector('#txtDataAberturaInicial').value='01/01/2025'"
        )

        contexto.evaluate(
            f"document.querySelector('#txtDataAberturaFinal').value='{datetime.now().strftime('%d/%m/%Y')}'"
        )

        contexto.click("#btnPesquisarAcompanhamentos")

        contexto.wait_for_selector("#tblListaAcompanhamento")

        return contexto.content()

    def fechar(self):

        self.browser.close()
        self.playwright.stop()