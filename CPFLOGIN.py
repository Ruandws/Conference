import pandas as pd
from playwright.sync_api import sync_playwright
import os
import tkinter as tk
from tkinter import simpledialog, messagebox
import tkinter.font as tkFont

# CAMINHO BASEADO NO SEU LOG DE ERRO (OneDrive)
CAMINHO_PLANILHA = r"C:\Automacoes\planilha1.xlsx"
# Alterado para salvar na mesma pasta onde seu script está rodando (Área de Trabalho via OneDrive)
CAMINHO_SAIDA = r"C:\Automacoes\resultados\planilha2.xlsx"

URL_LOGIN = "https://servicosti.ebserh.gov.br/#/login"

def obter_credenciais():
    """Cria uma janela para capturar usuário e senha."""
    credenciais = {}

    # Janela principal
    root = tk.Tk()
    root.title("Login")
    root.geometry("300x150")
    root.resizable(False, False)
    root.eval('tk::PlaceWindow . center')  # centraliza a janela na tela
    root.configure(bg="#2596be")  # fundo pret

    # Campo Usuário
    tk.Label(root, text="Usuário:").pack(pady=(10, 0))
    usuario_entry = tk.Entry(root)
    usuario_entry.pack(pady=5)
    usuario_entry.focus()

    # Campo Senha
    tk.Label(root, text="Senha:").pack()
    senha_entry = tk.Entry(root, show="*")
    senha_entry.pack(pady=5)

    # Fonte base do botão 
    fonte_base = tkFont.nametofont("TkDefaultFont")
    tamanho_novo = int(fonte_base.cget("size") * 1.8)
    fonte_botao = (fonte_base.cget("family"), tamanho_novo, "bold")

    # Função do botão
    def enviar():
        credenciais['usuario'] = usuario_entry.get().strip()
        credenciais['senha'] = senha_entry.get().strip()
        root.destroy()  # fecha a janela

    # Botão de envio
    tk.Button(root, text="Entrar", command=enviar).pack(pady=10)

    # Espera o usuário enviar antes de continuar
    root.mainloop()

    return credenciais.get('usuario'), credenciais.get('senha')

def executar():
    # 1. Obter credenciais antes de começar tudo
    usuario, senha = obter_credenciais()

    #Tratamento de exceção - Caso não fornecidas as credencias, a execução encerra.
    if not usuario or not senha:
        print("Execução cancelada: Usuário ou senha não fornecidos.")
        return

    print("Lendo planilha...")

    #Tratamento de exceção - Verifica se o caminho da planilha está correto
    if not os.path.exists(CAMINHO_PLANILHA):
        print(f"Erro: Planilha não encontrada em {CAMINHO_PLANILHA}")
        return

    ##Lógica da leitura
    df = pd.read_excel(CAMINHO_PLANILHA, dtype=str)
    coluna_dados = "CPF" 
    resultados = []

    with sync_playwright() as p:
        print("Iniciando Navegador...")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Login
        page.goto(URL_LOGIN)
        page.fill("input[ng-model='email']", usuario)
        page.fill("input[type='password']", senha)
        page.click("button.btn-success")

        # Navegação
        selector_menu = "div.widget-title:has-text('Pesquisa de usuário')"
        page.wait_for_selector(selector_menu, state="visible")
        page.locator(selector_menu).click()

        print("Iniciando consultas...")
        for index, row in df.iterrows():
            cpf_bruto = str(row[coluna_dados]).strip()
            cpf_limpo = "".join(filter(str.isdigit, cpf_bruto))

            if not cpf_limpo: continue

            print(f"[{index+1}] Consultando: {cpf_limpo}")
            campo_pesquisa = page.locator("input.form-control").first
            campo_pesquisa.fill(cpf_limpo)
            page.locator("button.btn-primary").click()

            try:
                page.wait_for_selector("tr[ng-repeat*='usuario']", timeout=3000)
                login = page.locator("tr[ng-repeat*='usuario']").first.locator("td").nth(4).inner_text().strip()
            except:
                login = "Não encontrado"

            resultados.append({"CPF": cpf_limpo, "login": login})
            campo_pesquisa.fill("")
            page.wait_for_timeout(300)

        browser.close()

    # SALVAMENTO FINAL
    print(f"Salvando em: {CAMINHO_SAIDA}")
    df_saida = pd.DataFrame(resultados)
    
    # Cria a pasta caso ela não exista (prevenção de erro)
    os.makedirs(os.path.dirname(CAMINHO_SAIDA), exist_ok=True)
    df_saida.to_excel(CAMINHO_SAIDA, index=False)

    # Aviso visual de conclusão
    final_root = tk.Tk()
    final_root.withdraw()
    messagebox.showinfo("Sucesso", f"Automação finalizada!\nSalvo em: {CAMINHO_SAIDA}")
    final_root.destroy()

if __name__ == "__main__":
    executar()