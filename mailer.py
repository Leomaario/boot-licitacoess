import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

class Mailer:
    def __init__(self):
        # Puxa as configurações do seu arquivo .env
        self.email_remetente = os.getenv("EMAIL_REMETENTE")
        self.senha_remetente = os.getenv("EMAIL_SENHA_APP")  # As 16 letras do Google
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def enviar_alerta(self, email_destino, nome_usuario, licitacoes_por_categoria):
        """
        Envia um e-mail formatado em HTML com as novas licitações encontradas.
        licitacoes_por_categoria: Dicionário {'Categoria': [lista_de_objetos]}
        """
        if not licitacoes_por_categoria:
            logging.info(f"Sem licitações para enviar para {email_destino}")
            return

        # Configuração da estrutura da mensagem
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🚀 Novas Licitações Encontradas - Licitabahia"
        msg["From"] = f"Licitabahia Alertas <{self.email_remetente}>"
        msg["To"] = email_destino

        # --- CONSTRUÇÃO DO CORPO HTML (Estilo SaaS) ---
        html_content = f"""
        <html>
        <body style="font-family: sans-serif; color: #333; line-height: 1.6; margin: 0; padding: 20px; background-color: #f4f4f7;">
            <div style="max-width: 600px; margin: auto; background: #ffffff; padding: 30px; border-radius: 12px; border: 1px solid #e5e7eb;">
                <h2 style="color: #111827; margin-top: 0;">Olá, {nome_usuario}! 👋</h2>
                <p style="font-size: 16px; color: #4b5563;">O seu robô acaba de encontrar novas oportunidades que batem com o seu perfil:</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 25px 0;">
        """

        # Adiciona as licitações agrupadas por categoria no e-mail
        for categoria, licitacoes in licitacoes_por_categoria.items():
            html_content += f"""
                <div style="margin-bottom: 30px;">
                    <h3 style="background: #eff6ff; color: #1e40af; padding: 8px 12px; border-radius: 6px; display: inline-block; margin-bottom: 15px;">
                        📂 {categoria}
                    </h3>
            """
            
            for lic in licitacoes:
                titulo = lic.get('titulo', 'Licitação sem título')
                orgao = lic.get('orgao', 'Órgão não informado')
                link = lic.get('link_edital', '#')
                
                html_content += f"""
                    <div style="margin-bottom: 15px; padding-left: 10px; border-left: 3px solid #2563eb;">
                        <p style="margin: 0; font-weight: bold; color: #111827;">{titulo}</p>
                        <p style="margin: 2px 0; font-size: 14px; color: #6b7280;">🏛️ {orgao}</p>
                        <a href="{link}" style="color: #2563eb; text-decoration: none; font-size: 14px; font-weight: 600;">Ver detalhes no Portal →</a>
                    </div>
                """
            html_content += "</div>"

        # Rodapé do e-mail
        html_content += """
                <hr style="border: 0; border-top: 1px solid #eee; margin: 25px 0;">
                <p style="font-size: 12px; color: #9ca3af; text-align: center;">
                    Este é um alerta automático do seu sistema Licitabahia.<br>
                    Para gerenciar seus alertas, acesse sua conta.
                </p>
            </div>
        </body>
        </html>
        """

        # Anexa o HTML à mensagem
        parte_html = MIMEText(html_content, "html")
        msg.attach(parte_html)

        try:
            # Conexão segura com o servidor SMTP do Google
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Ativa a criptografia
            server.login(self.email_remetente, self.senha_remetente)
            server.sendmail(self.email_remetente, email_destino, msg.as_string())
            server.quit()
            logging.info(f"✅ E-mail enviado com sucesso para: {email_destino}")
        except Exception as e:
            logging.error(f"❌ Falha ao disparar e-mail para {email_destino}: {e}")