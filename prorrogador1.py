import re
from playwright.sync_api import Playwright, sync_playwright
import tkinter as tk
import tkinter.font as tkFont
from tkinter import filedialog, messagebox

URL_LOGIN = "https://servicosti.ebserh.gov.br/#/login"

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
    novadata_entry = tk.Entry(frame_info)
    novadata_entry.pack(pady=3)

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

    # Botão único para iniciar automação
    def iniciar_automacao():
        if not usuario_entry.get() or not senha_entry.get():
            messagebox.showwarning("Aviso", "Preencha usuário e senha!")
            return

        dados['cpf'] = cpf_entry.get().strip()
        dados['novadata'] = novadata_entry.get().strip()
        dados['usuario'] = usuario_entry.get().strip()
        dados['senha'] = senha_entry.get().strip()
        root.destroy()

    tk.Button(root, text="Iniciar Automação", command=iniciar_automacao, bg="#000000", fg="white", font=fonte_botao).pack(pady=15)

    root.mainloop()
    return dados.get('cpf'), dados.get('novadata'), dados.get('usuario'), dados.get('senha')


#Execução
def run() -> None:
    #Puxando as variáveis "usuário" e "senha" informados pelo usuário
    cpf, novadata, usuario, senha,= painel_inicial()

    if not usuario or not senha:
        print("Execução cancelada: Dados incompletos.")
        return
    
    print("Iniciando automação...")

    with sync_playwright() as p:
    #Abertura do Navegador
        print("Iniciando Navegador...")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        #Login
        page.goto(URL_LOGIN)
        page.fill("input[ng-model='email']", usuario)
        page.fill("input[type='password']", senha)
        page.click("button.btn-success")
        page.locator("div").filter(has_text="Pesquisa de usuário Selecione").nth(4).click()
        page.get_by_role("textbox", name="Informe o e-mail EBSERH, o").click()
        page.get_by_role("textbox", name="Informe o e-mail EBSERH, o").fill(cpf)
        page.get_by_role("button", name="Pesquisar").click()
        #Achado o usuário, ele abre o "Saber mais...""
        page.get_by_title("Visualizar dados do usuario").click()
        #Clica no campo de data
        page.get_by_role("textbox", name="__/__/____").click()
        #Como o campo é bugado, ele simula um "ESC"
        page.locator("div:nth-child(7) > .col-md-9 > .input-group > .ng-pristine.ng-untouched > .uib-datepicker-popup > li > .ng-scope.ng-isolate-scope > div > .uib-daypicker").press("Escape")
        page.get_by_role("textbox", name="__/__/____").fill(novadata)
        page.get_by_role("button", name="Atualizar dados").click()
        # Feito a prorrogação até a data informada, volta para a pesquisa de usuários a fim de recomeçar o looping.
        ##page.goto("https://servicosti.ebserh.gov.br/#/pesquisa-usuarios")
        ##page.get_by_role("textbox", name="Informe o e-mail EBSERH, o").click()

if __name__ == "__main__":
    run()




