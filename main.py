import logging
from scraper import Scraper
from database import Database
from config import CATEGORIAS_DE_BUSCA
from mailer import Mailer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def main():
    logging.info("🚀 Robô de Produção Iniciado")
    db = Database()
    scraper = Scraper()
    mailer = Mailer()

    try:
        # 1. FASE DE COLETA: Busca nos sites e salva no Supabase
        for nome, codigo in CATEGORIAS_DE_BUSCA.items():
            logging.info(f"🔎 Coletando categoria: {nome}")
            # Aqui roda sua lógica existente de scraper e parser
            # licitacoes = parser.parse(...)
            # db.salvar_licitacoes(licitacoes)
            logging.info(f"✅ Categoria {nome} processada e salva.")

        # 2. FASE DE ALERTAS: Busca licitações no banco que ainda NÃO foram enviadas
        # Buscamos apenas as que estão com alerta_enviado = False
        res = db.client.table("licitacoes").select("*").eq("alerta_enviado", False).execute()
        novas_licitacoes = res.data

        if not novas_licitacoes:
            logging.info("📢 Nenhuma licitação inédita para alertar hoje.")
            return

        # Busca usuários que ativaram os alertas no React
        usuarios = db.buscar_usuarios_com_alerta()
        
        for usuario in usuarios:
            email_user = usuario.get("email")
            nome_user = usuario.get("full_name", "Usuário")
            categorias_do_user = usuario.get("categorias_alerta", [])

            if not email_user or not categorias_do_user:
                continue

            # Filtra apenas as que batem com o interesse do usuário
            licitacoes_para_este_user = {}
            for lic in novas_licitacoes:
                cat_lic = lic.get('categoria')
                if cat_lic in categorias_do_user:
                    if cat_lic not in licitacoes_para_este_user:
                        licitacoes_para_este_user[cat_lic] = []
                    licitacoes_para_este_user[cat_lic].append(lic)

            # Dispara o e-mail se houver match
            if licitacoes_para_este_user:
                logging.info(f"📧 Enviando resumo para: {email_user}")
                mailer.enviar_alerta(email_user, nome_user, licitacoes_para_este_user)

        # 3. FINALIZAÇÃO: Marca as licitações como enviadas para não repetir amanhã
        ids_processados = [l['id'] for l in novas_licitacoes]
        db.client.table("licitacoes").update({"alerta_enviado": True}).in_("id", ids_processados).execute()
        logging.info(f"💾 {len(ids_processados)} licitações marcadas como notificadas no banco.")

    except Exception as e:
        logging.error(f"❌ Erro crítico na execução: {e}")
    finally:
        scraper.fechar()
        logging.info("🏁 Robô finalizado")

if __name__ == "__main__":
    main()