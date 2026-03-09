import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

URL_FORMULARIO = "http://comprasnet.ba.gov.br/inter/system/Licitacao/FormularioConsultaAcompanhamento.asp"
URL_BASE_DETALHES = "https://comprasnet3.ba.gov.br/Licitacao/"
URL_BASE_EDITAL = "https://comprasnet3.ba.gov.br/"

CATEGORIAS_DE_BUSCA = {
    "Alimentos": "89",
    "Equipamentos de TI": "70",
    "Equipamentos Médicos": "65",
    "Obras e Construções": "07",
    "Materiais de Construção": "56"
}

DATA_INICIO_FILTRO = datetime.strptime("01/01/2025", "%d/%m/%Y")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADLESS = True
TIMEOUT = 60000