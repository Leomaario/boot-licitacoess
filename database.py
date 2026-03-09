from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import logging

class Database:

    def __init__(self):
        self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logging.info("Conectado ao Supabase")

    def salvar_licitacoes(self, licitacoes):

        if not licitacoes:
            return

        try:
            self.client.table("licitacoes").upsert(
                licitacoes,
                on_conflict="numero"
            ).execute()

            logging.info(f"{len(licitacoes)} licitações salvas")

        except Exception as e:
            logging.error(f"Erro ao salvar no banco: {e}")

    def buscar_usuarios_com_alerta(self):
        try:
            # Puxa apenas quem tem o email_alerts como TRUE
            resposta = self.client.table("profiles").select("email, full_name, categorias_alerta").eq("email_alerts", True).execute()
            return resposta.data
        except Exception as e:
            logging.error(f"Erro ao buscar usuários para alerta: {e}")
            return []