import re
from playwright.sync_api import Playwright, sync_playwright, expect
import tkinter as tk
import tkinter.font as tkFont
from tkinter import filedialog, messagebox
from datetime import datetime

URL_LOGIN = "https://servicosti.ebserh.gov.br/#/login"

#Funções auxiliares
def validar_data(data_str: str) -> bool:
    #"""Valida formato DD/MM/AAAA, data real e obrigatoriamente futura."""
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", data_str):
        messagebox.showerror("Data ou Formáto Inválido", " Use DD/MM/AAAA.")
        return False
    
    # Tenta converter a string para datetime
    try:
        data = datetime.strptime(data_str, "%d/%m/%Y")
        if data <= datetime.today():
            messagebox.showwarning("Data inválida", "A data de expiração deve ser futura.")
            return False
        return True
    except ValueError:
            messagebox.showerror("Data inválida", "Data inexistente (ex: 31/02/2025 não existe).")
            return False

#Interface 
def painel_inicial():
    """Janela única para caminhos e credenciais com um único botão para iniciar a automação."""
    dados = {}

    #Formatação da janela do programa
    root = tk.Tk()
    root.title("Automação EBSERH")
    root.geometry("500x360")
    root.resizable(False, False)
    root.eval('tk::PlaceWindow . center')
    root.configure(bg="#2596be")

    # --- Container Superior: Informações do usuário alvo ---
    frame_info = tk.Frame(root, bg="#2596be")
    frame_info.pack(fill="x", padx=20, pady=(10,10))

    tk.Label(frame_info, text="CPF a pesquisar:", bg="#2596be", fg="white").pack(anchor="w", pady=(5,0))
    cpf_entry = tk.Entry(frame_info)
    cpf_entry.pack(pady=3)

    tk.Label(frame_info, text="Nova data de Expiração:", bg="#2596be", fg="white").pack(anchor="w", pady=(5,0))
    novadata_entry = tk.Entry(frame_info, fg="gray")
    novadata_entry.insert(0, "DD/MM/AAAA")

    def limpar_placeholder(event):
        if novadata_entry.get() == "DD/MM/AAAA":
            novadata_entry.delete(0, tk.END)
            novadata_entry.config(fg="black")

    def restaurar_placeholder(event):
        if not novadata_entry.get():
            novadata_entry.insert(0, "DD/MM/AAAA")
            novadata_entry.config(fg="gray")

    def formatar_data(event):
        tecla = event.keysym
        if tecla in ("BackSpace", "Delete", "Left", "Right", "Tab"):
            return

        if novadata_entry.get() == "DD/MM/AAAA":
            novadata_entry.delete(0, tk.END)
            novadata_entry.config(fg="black")

        # Bloqueia qualquer caractere não-dígito
        if not event.char.isdigit():
            return "break"

        # Impede digitação além de 10 chars (DD/MM/AAAA)
        if len(novadata_entry.get()) >= 10:
            return "break"

        pos = len(novadata_entry.get())

        # Injeta '/' automaticamente nas posições 2 e 5
        if pos in (2, 5):
            novadata_entry.insert(tk.END, "/")
            
    novadata_entry.pack(pady=3)
    novadata_entry.bind("<Key>", formatar_data)

    # --- Container: Credenciais --
    frame_cred = tk.Frame(root, bg="#2596be")
    frame_cred.pack(fill="x", padx=20, pady=(10,10))

    tk.Label(frame_cred, text="Usuário:", bg="#2596be", fg="white").pack(anchor="w", pady=(5,0))
    usuario_entry = tk.Entry(frame_cred)
    usuario_entry.pack(pady=3)

    tk.Label(frame_cred, text="Senha:", bg="#2596be", fg="white").pack(anchor="w", pady=(5,0))
    senha_entry = tk.Entry(frame_cred, show="*")
    senha_entry.pack(pady=3)

    # Fonte do botão
    fonte_base = tkFont.nametofont("TkDefaultFont")
    tamanho_novo = int(fonte_base.cget("size") * 1.8)
    fonte_botao = (fonte_base.cget("family"), tamanho_novo, "bold")

    # Ativo pelo botão de "Iniciar Automação"
    def iniciar_automacao():
         # ── Validações de campos obrigatórios ────────────
        usuario = usuario_entry.get().strip()
        senha = senha_entry.get().strip()
        cpf = cpf_entry.get().strip()
        novadata = novadata_entry.get().strip()

        if not usuario and not senha and not cpf and (not novadata or novadata == "DD/MM/AAAA"):
            messagebox.showwarning("Aviso", "Preencha todos os campos!")
            return

        if not usuario:
            messagebox.showwarning("Aviso", "Preencha o usuário!")
            return
        if not senha:
            messagebox.showwarning("Aviso", "Preencha a senha!")
            return
        if not cpf:
            messagebox.showwarning("Aviso", "Preencha o CPF ou usuário alvo!")
            return
        if not novadata or novadata == "DD/MM/AAAA":                         # ← novadata obrigatório
            messagebox.showwarning("Aviso", "Preencha a nova data de expiração!")
            return
        #Validação de formato da nova data (dd/mm/aaaa) e lógica de data válida
        if not validar_data(novadata):                  
            return                                                    

        dados['cpf'] = cpf
        dados['novadata'] = novadata
        dados['usuario'] = usuario
        dados['senha'] = senha
        root.destroy()

    tk.Button(root, text="Iniciar Automação", command=iniciar_automacao, bg="#000000", fg="white", font=fonte_botao).pack(pady=15)
    root.mainloop()
    return dados.get('cpf'), dados.get('novadata'), dados.get('usuario'), dados.get('senha')


#Execução
def run() -> None:
    #Puxando as variáveis "usuário" e "senha" informados pelo usuário
    cpf, novadata, usuario, senha,= painel_inicial()

#―――――Try/Except para evitar erros de execução e garantir que o navegador seja fechado corretamente
    if not all([cpf, novadata, usuario, senha]):
        messagebox.showinfo("Cancelado", "Automação cancelada pelo usuário.")
        return
    
    print("Iniciando automação...")

    with sync_playwright() as p:
        print("Iniciando Navegador...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        #---Tratativa gerais para erros esperados e não esperados.
        try:
            #---Tratativa para erros comuns durante login
            try:
                #Login
                page.goto(URL_LOGIN)
                page.fill("input[ng-model='email']", usuario)
                page.fill("input[type='password']", senha)
                page.click("button.btn-success")

                # Verifica se o login foi bem-sucedido;
                # se não encontrar o painel pós-login, assume credenciais inválidas.
                page.locator("div").filter(has_text="Pesquisa de usuário Selecione").nth(4).wait_for(timeout=3500)
            except Exception as e:
                raise RuntimeError("Usuário/Senha incorreta. Reinicie a aplicação e tente novamente")


            page.locator("div").filter(has_text="Pesquisa de usuário Selecione").nth(4).click()
            page.get_by_role("textbox", name="Informe o e-mail EBSERH, o").click()
            page.get_by_role("textbox", name="Informe o e-mail EBSERH, o").fill(cpf)
            page.get_by_role("button", name="Pesquisar").click()
            #Achado o usuário, ele abre o "Saber mais...""
            btn_visualizar = page.get_by_title("Visualizar dados do usuario")
            
            #Tratativa para usuário não encontrado
            try:
                expect(btn_visualizar).to_be_visible(timeout=3500)
                btn_visualizar.click()

            except Exception:
                # Usuário não encontrado — encerra silenciosamente, sem callback de código
                raise RuntimeError("Nenhum usuário encontrado para o CPF informado. Reinicie a automação, insira um CPF válido e tente novamente.")

            #Clica no campo de data
            page.get_by_role("textbox", name="__/__/____").click()
            #Como o campo é bugado, ele simula um "ESC"
            page.locator("div:nth-child(7) > .col-md-9 > .input-group > .ng-pristine.ng-untouched > .uib-datepicker-popup > li > .ng-scope.ng-isolate-scope > div > .uib-daypicker").press("Escape")
            page.get_by_role("textbox", name="__/__/____").fill(novadata)
            page.get_by_role("button", name="Atualizar dados").click()
            print("Atualização de colaborador realizada com sucesso!")
        except RuntimeError as e:
            # Erros esperados (login, elementos não encontrados)
            messagebox.showerror("Erro na Automação", str(e))

        except Exception as e:
            # Erros inesperados
            messagebox.showerror("Erro Inesperado", f"Contate o suporte:\n{e}")

        #garante que o sistema encerre caso algum problema ocorra
        finally:
            browser.close()
            print("Navegador encerrado.")

if __name__ == "__main__":
    run()




