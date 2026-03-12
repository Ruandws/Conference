import pandas as pd
from playwright.sync_api import sync_playwright
import os
import tkinter as tk
from tkinter import messagebox

# --- CONFIGURAÇÕES DE CAMINHO ---
CAMINHO_PLANILHA = r"C:\Automacoes\planilha1.xlsx"
CAMINHO_SAIDA = r"C:\Automacoes\resultados\planilha2.xlsx"
URL_LOGIN = "https://servicosti.ebserh.gov.br/#/login"

class AutomacaoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Agente de Automação EBSERH")
        self.root.geometry("450x350")
        
        # Interface - Login e Senha
        tk.Label(root, text="Login:", font=("Arial", 10, "bold")).pack(pady=5)
        self.ent_usuario = tk.Entry(root, width=35)
        self.ent_usuario.pack()

        tk.Label(root, text="Senha:", font=("Arial", 10, "bold")).pack(pady=5)
        self.ent_senha = tk.Entry(root, width=35, show="*")
        self.ent_senha.pack()

        # Checkboxes de Opções (Visualização)
        tk.Label(root, text="Opções de Visualização:", font=("Arial", 10, "italic")).pack(pady=10)
        
        self.var_aberto = tk.BooleanVar(value=False)
        self.chk_aberto = tk.Checkbutton(root, text="Visualização da automação com navegador aberto", variable=self.var_aberto)
        self.chk_aberto.pack(anchor="w", padx=40)

        self.var_terminal = tk.BooleanVar(value=False)
        self.chk_terminal = tk.Checkbutton(root, text="Exibir progresso no terminal", variable=self.var_terminal)
        self.chk_terminal.pack(anchor="w", padx=40)

        # Botão Iniciar
        self.btn_iniciar = tk.Button(root, text="INICIAR AUTOMAÇÃO", bg="#006400", fg="white", 
                                     font=("Arial", 10, "bold"), height=2, width=25, command=self.validar_e_rodar)
        self.btn_iniciar.pack(pady=25)

    def log(self, mensagem):
        """Imprime no terminal apenas se a opção estiver marcada."""
        if self.var_terminal.get():
            print(f"[LOG]: {mensagem}")

    def validar_e_rodar(self):
        usuario = self.ent_usuario.get()
        senha = self.ent_senha.get()

        # Validação de campos vazios
        if not usuario or not senha:
        messagebox.showwarning("Atenção", "Por favor, preencha usuário e senha!")
            return

        # Validação de visualização: Se ambas estiverem falsas, avisa e NÃO fecha a aplicação
        if not self.var_aberto.get() and not self.var_terminal.get():
            messagebox.showwarning("Opção de Visualização", "Escolha pelo menos uma opção de visualização para continuar!")
            return # Apenas interrompe esta função, mantendo a janela aberta

        # Se passou, esconde a janela e processa
        self.root.withdraw() 
        self.executar_logica(usuario, senha)
        self.root.destroy()

    def executar_logica(self, usuario, senha):
        self.log("Iniciando processo...")
        
        if not os.path.exists(CAMINHO_PLANILHA):
            messagebox.showerror("Erro", f"Arquivo não encontrado em: {CAMINHO_PLANILHA}")
            return

        try:
            df = pd.read_excel(CAMINHO_PLANILHA, dtype=str)
        except Exception as e:
            messagebox.showerror("Erro na Planilha", f"Não foi possível ler a planilha: {e}")
            return

        resultados = []

        with sync_playwright() as p:
            # Lógica: Se marcado "Aberto", headless é Falso.
            mostrar_navegador = self.var_aberto.get()
            browser = p.chromium.launch(headless=not mostrar_navegador)
            page = browser.new_page()

            try:
                self.log("Acessando portal EBSERH...")
                page.goto(URL_LOGIN)
                page.fill("input[ng-model='email']", usuario)
                page.fill("input[type='password']", senha)
                page.click("button.btn-success")

                # Aguarda carregamento do menu principal
                selector_menu = "div.widget-title:has-text('Pesquisa de usuário')"
                page.wait_for_selector(selector_menu, state="visible", timeout=15000)
                page.locator(selector_menu).click()
                
                self.log("Login OK. Iniciando Varredura.")

                for index, row in df.iterrows():
                    # Garante que a coluna CPF existe
                    cpf_original = str(row.get("CPF", ""))
                    cpf_limpo = "".join(filter(str.isdigit, cpf_original))
                    
                    if not cpf_limpo:
                        continue

                    self.log(f"Consultando [{index + 1}/{len(df)}]: {cpf_limpo}")
                    
                    campo = page.locator("input.form-control").first
                    campo.fill(cpf_limpo)
                    page.locator("button.btn-primary").click()

                    try:
                        # Espera curta para verificar se o resultado apareceu
                        page.wait_for_selector("tr[ng-repeat*='usuario']", timeout=3000)
                        login_res = page.locator("tr[ng-repeat*='usuario']").first.locator("td").nth(4).inner_text().strip()
                    except:
                        login_res = "Não encontrado"

                    resultados.append({"CPF": cpf_limpo, "login": login_res})
                    campo.fill("") # Limpa para a próxima consulta

            except Exception as e:
                self.log(f"Erro: {e}")
                messagebox.showerror("Erro na Automação", f"Ocorreu um problema: {e}")
            finally:
                browser.close()

        # Exportação Final
        if resultados:
            df_saida = pd.DataFrame(resultados)
            os.makedirs(os.path.dirname(CAMINHO_SAIDA), exist_ok=True)
            df_saida.to_excel(CAMINHO_SAIDA, index=False)
            messagebox.showinfo("Sucesso", f"Processamento concluído!\nSalvo em: {CAMINHO_SAIDA}")
        else:
            messagebox.showwarning("Fim", "Nenhum dado foi processado.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomacaoApp(root)
    root.mainloop()