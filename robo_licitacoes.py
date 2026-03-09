from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from datetime import datetime
import time
from supabase import create_client, Client
from urllib.parse import urljoin
import re

# --- CONFIGURAÇÃO ---
URL_FORMULARIO = "http://comprasnet.ba.gov.br/inter/system/Licitacao/FormularioConsultaAcompanhamento.asp"
URL_BASE_DETALHES = "https://comprasnet3.ba.gov.br/Licitacao/"
URL_BASE_EDITAL = "https://comprasnet3.ba.gov.br/"
CATEGORIAS_DE_BUSCA = {
    "Alimentos": "89", "Equipamentos de TI": "70", "Equipamentos Médicos": "65",
    "Obras e Construções": "07", "Materiais de Construção": "56"
}
DATA_INICIO_FILTRO = datetime.strptime("01/01/2025", '%d/%m/%Y')
SUPABASE_URL = "https://uibrejozhiqixjekkjdj.supabase.co" 
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVpYnJlam96aGlxaXhqZWtramRqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM0NTUwNiwiZXhwIjoyMDgzOTIxNTA2fQ.h1pwa1FmVQ92NCj_HAiknrQTuRHKDdTrKh5z0JLdlq0"
# --------------------

print("✅ Robô Conquistador Resiliente (v37.0) iniciado!")
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Conexão com Supabase estabelecida.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for nome_categoria, codigo_categoria in CATEGORIAS_DE_BUSCA.items():
            print(f"\n{'='*50}\n🔎 CONQUISTANDO CATEGORIA: '{nome_categoria}'\n{'='*50}")
            licitacoes_para_investigar_html = []
            
            try:
                page.goto(URL_FORMULARIO, timeout=90000)
                page.wait_for_load_state("networkidle")
                iframe_principal = page.frame(name='iframe-system')

                if iframe_principal:
                    print("🧩 Iframe principal encontrado. Trabalhando dentro dele.")
                    contexto = iframe_principal
                else:
                    print("⚠️ Iframe não encontrado. Trabalhando direto na página.")
                    contexto = page

                
                contexto.select_option("#selSitLicitacao", value="2")
                contexto.select_option("#selGrupo", value=codigo_categoria)
                data_inicio_str = "01/01/2025"
                data_fim_str = datetime.now().strftime('%d/%m/%Y')
                iframe_principal.evaluate(f"document.querySelector('#txtDataAberturaInicial').value = '{data_inicio_str}'")
                iframe_principal.evaluate(f"document.querySelector('#txtDataAberturaFinal').value = '{data_fim_str}'")
                iframe_principal.click("#btnPesquisarAcompanhamentos")
                print("Botão 'Pesquisar' clicado. Coletando links de todas as páginas...")

                pagina_atual = 1
                html_pagina_anterior = ""
                
                while True:
                    print(f"  -> Lendo página de resultados nº {pagina_atual}...")
                    iframe_resultados = None
                    try:
                        iframe_principal.wait_for_selector("#tblListaAcompanhamento", state="visible", timeout=30000)
                        iframe_resultados = iframe_principal
                    except PlaywrightTimeoutError:
                        iframe_aninhado_handle = iframe_principal.wait_for_selector("iframe", state="attached", timeout=60000)
                        iframe_resultados = iframe_aninhado_handle.content_frame()
                        iframe_resultados.wait_for_selector("#tblListaAcompanhamento", state="visible", timeout=60000)
                    
                    html_atual = iframe_resultados.content()
                    if html_atual == html_pagina_anterior:
                        print("  -> Conteúdo da página é idêntico ao anterior. Fim do loop.")
                        break
                    html_pagina_anterior = html_atual

                    site_atual = BeautifulSoup(html_atual, 'html.parser')
                    tabela_atual = site_atual.find('table', id='tblListaAcompanhamento')
                    if tabela_atual:
                        linhas = tabela_atual.find('tbody').find_all('tr')
                        for linha in linhas:
                            licitacoes_para_investigar_html.append(str(linha))
                    
                    botao_proximo = iframe_resultados.locator('a:has-text("Próximo")')
                    if botao_proximo.count() > 0 and not botao_proximo.is_disabled():
                        print("  -> Encontrado botão 'Próximo', navegando...")
                        botao_proximo.click()
                        iframe_resultados.wait_for_load_state('networkidle', timeout=60000)
                        pagina_atual += 1
                    else:
                        print("  -> Fim da paginação.")
                        break
            
            except PlaywrightTimeoutError as e:
                print(f"🟡 TIMEOUT na fase de conquista da categoria '{nome_categoria}'. Pulando. Detalhes: {e}")
                continue
            
            if licitacoes_para_investigar_html:
                print(f"\n✅ Conquista finalizada. {len(licitacoes_para_investigar_html)} licitações brutas encontradas.")
                
                licitacoes_unicas = {}
                for html_linha in licitacoes_para_investigar_html:
                    soup_linha = BeautifulSoup(html_linha, 'html.parser')
                    colunas = soup_linha.find_all('td')
                    if len(colunas) >= 1:
                        numero_licitacao = colunas[0].get_text(strip=True)
                        if numero_licitacao not in licitacoes_unicas:
                            licitacoes_unicas[numero_licitacao] = html_linha
                
                print(f"Iniciando investigação detalhada de {len(licitacoes_unicas)} licitações ÚNICAS...")
                
                licitacoes_finais_para_db = []
                for numero_licitacao, html_linha in licitacoes_unicas.items():
                    try:
                        print(f"    -> Investigando {numero_licitacao}...")
                        soup_linha = BeautifulSoup(html_linha, 'html.parser')
                        colunas = soup_linha.find_all('td')
                        
                        data_abertura_str = colunas[3].get_text(strip=True)
                        data_abertura_dt = datetime.strptime(data_abertura_str, '%d/%m/%Y')
                        if data_abertura_dt < DATA_INICIO_FILTRO: continue
                        
                        link_tag = colunas[0].find('a')
                        if not (link_tag and link_tag.has_attr('href')): continue
                        link_detalhes = URL_BASE_DETALHES + link_tag['href']
                        
                        page_detalhes = context.new_page()
                        page_detalhes.goto(link_detalhes, timeout=60000)
                        html_detalhes = page_detalhes.content()
                        soup_detalhes = BeautifulSoup(html_detalhes, 'html.parser')
                        
                        dados_detalhados = {}
                        tabela_detalhes = soup_detalhes.find('table', id='ConteudoPrint')
                        if tabela_detalhes:
                            for th in tabela_detalhes.find_all('th'):
                                chave = th.get_text(strip=True).replace(':', '')
                                valor_tag = th.find_next_sibling('th')
                                if valor_tag:
                                    valor = valor_tag.get_text(strip=True)
                                    dados_detalhados[chave] = valor
                        
                        link_pdf = None
                        botao_edital = soup_detalhes.find('a', id='btnBaixarEdital')
                        if botao_edital and botao_edital.has_attr('href'):
                            link_parcial_pdf = botao_edital['href']
                            link_pdf = urljoin(URL_BASE_EDITAL, link_parcial_pdf)
                        
                        page_detalhes.close()
                        
                        valor_str = colunas[7].get_text(strip=True) if len(colunas) > 7 else None
                        valor_num = None
                        if valor_str and valor_str != '-':
                            valor_limpo = re.sub(r'[R$\s\.]', '', valor_str).replace(',', '.')
                            try:
                                valor_num = float(valor_limpo)
                            except ValueError:
                                valor_num = None

                        licitacao_final = {
                            'categoria': nome_categoria, 'numero': numero_licitacao,
                            'orgao': colunas[1].get_text(strip=True), 'unidade': colunas[2].get_text(strip=True),
                            'modalidade': colunas[4].get_text(strip=True),
                            'data_encerramento': data_abertura_str, 'situacao': colunas[5].get_text(strip=True),
                            'titulo': colunas[6].get_text(strip=True),
                            'valor_estimado': valor_str,
                            'valor_numerico': valor_num,
                            'link_edital': link_detalhes, 'link_pdf_edital': link_pdf,
                            'tipo_preco': dados_detalhados.get('Tipo'),
                            'local_realizacao': dados_detalhados.get('Local da Realização'),
                            'processo_numero': dados_detalhados.get('Processo Nº'),
                            'dotacao_orcamentaria': dados_detalhados.get('Dotação Orçamentária'),
                            'data_publicacao_doe': dados_detalhados.get('Data de Publicação no D.O.E.'),
                            'numero_licitacao_eletronica': dados_detalhados.get('Nº Licitação Eletrônica')
                        }
                        licitacoes_finais_para_db.append(licitacao_final)

                    except Exception as e:
                        print(f"      🟡 AVISO: Falha ao processar {numero_licitacao}. Erro: {e}. Pulando.")
                        if 'page_detalhes' in locals() and not page_detalhes.is_closed():
                            page_detalhes.close()
                        continue

                if licitacoes_finais_para_db:
                    print(f"\nSalvando {len(licitacoes_finais_para_db)} licitações detalhadas no banco de dados...")
                    supabase.table('licitacoes').upsert(licitacoes_finais_para_db, on_conflict='numero').execute()
                    print(f"✅ Categoria '{nome_categoria}' totalmente processada e salva!")
        
        browser.close()

except Exception as e:
    print(f"❌ Ocorreu um erro inesperado e fatal: {e}")