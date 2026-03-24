import pandas as pd
from playwright.sync_api import sync_playwright
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.font as tkFont

URL_LOGIN = "https://servicosti.ebserh.gov.br/#/login"

##Funções Auxiliares
def tratar_cpf(valor):

    if pd.isna(valor):
        return None

    cpf_original = str(valor).strip()

    # remove apóstrofo
    cpf_original = cpf_original.replace("'", "")

    # remove tudo que não for número
    cpf = re.sub(r"\D", "", cpf_original)

    if cpf == "":
        return None

    if len(cpf) < 11:
        cpf = cpf.zfill(11)
        return cpf

    if len(cpf) > 11:
        return None

    return cpf


##Interface
def painel_inicial():
    """Janela única para caminhos e credenciais com um único botão para iniciar a automação."""
    dados = {}

    root = tk.Tk()
    root.title("Automação EBSERH")
    root.geometry("500x360")
    root.resizable(False, False)
    root.eval('tk::PlaceWindow . center')
    root.configure(bg="#2596be")

    # --- Container Superior: Caminhos ---
    frame_caminhos = tk.Frame(root, bg="#2596be")
    frame_caminhos.pack(fill="x", padx=20, pady=(10,5))
    tk.Label(frame_caminhos, text="Planilha de Entrada (.xlsx):", bg="#2596be", fg="white").pack(anchor="w")
    
    entrada_var = tk.StringVar()
    entrada_entry = tk.Entry(frame_caminhos, textvariable=entrada_var, width=50)
    entrada_entry.pack(pady=3)

    def escolher_entrada():
        arquivo = filedialog.askopenfilename(filetypes=[("Arquivos Excel", "*.xlsx")])
        if arquivo:
            entrada_var.set(arquivo)

    tk.Button(frame_caminhos, text="Selecionar Entrada", command=escolher_entrada, bg="#000000", fg="white").pack(pady=3)

    tk.Label(frame_caminhos, text="Arquivo de Saída (.xlsx):", bg="#2596be", fg="white").pack(anchor="w", pady=(10,0))
    saida_var = tk.StringVar()
    saida_entry = tk.Entry(frame_caminhos, textvariable=saida_var, width=50)
    saida_entry.pack(pady=3)

    def escolher_saida():
        arquivo = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                               filetypes=[("Arquivos Excel", "*.xlsx")])
        if arquivo:
            saida_var.set(arquivo)

    tk.Button(frame_caminhos, text="Selecionar Saída", command=escolher_saida, bg="#000000", fg="white").pack(pady=3)

    # --- Container Inferior: Credenciais ---
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
        if not entrada_var.get() or not saida_var.get():
            messagebox.showwarning("Aviso", "Selecione os caminhos de entrada e saída!")
            return
        if not usuario_entry.get() or not senha_entry.get():
            messagebox.showwarning("Aviso", "Preencha usuário e senha!")
            return

        dados['entrada'] = entrada_var.get()
        dados['saida'] = saida_var.get()
        dados['usuario'] = usuario_entry.get().strip()
        dados['senha'] = senha_entry.get().strip()
        root.destroy()

    tk.Button(root, text="Iniciar Automação", command=iniciar_automacao, bg="#000000", fg="white", font=fonte_botao).pack(pady=15)

    root.mainloop()
    return dados.get('entrada'), dados.get('saida'), dados.get('usuario'), dados.get('senha')


##Execução
def executar():
    CAMINHO_PLANILHA, CAMINHO_SAIDA, usuario, senha = painel_inicial()

    if not CAMINHO_PLANILHA or not CAMINHO_SAIDA or not usuario or not senha:
        print("Execução cancelada: Dados incompletos.")
        return

    print("Lendo planilha...")

    if not os.path.exists(CAMINHO_PLANILHA):
        print(f"Erro: Planilha não encontrada em {CAMINHO_PLANILHA}")
        return

    df = pd.read_excel(CAMINHO_PLANILHA, dtype=str)

    coluna_dados = "CPF"
    resultados = []

    # NORMALIZA TODOS OS CPFs UMA VEZ
    df["CPF_normalizado"] = df[coluna_dados].apply(tratar_cpf)
    df["CPF_normalizado"] = df["CPF_normalizado"].astype("string")

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

        # CACHE DOS LOCATORS
        campo_pesquisa = page.locator("input.form-control").first
        botao_pesquisa = page.locator("button.btn-primary")

        print("Iniciando consultas...")

        for index, row in df.iterrows():
            cpf_original = row["CPF"]
            cpf_limpo = row["CPF_normalizado"]

            if pd.isna(cpf_limpo) or cpf_limpo is None:
                resultados.append({
                    "CPF_original": cpf_original,
                    "CPF_tratado": None,
                    "login": None
                })
                continue

            print(f"[{index+1}] Consultando: {cpf_limpo}")

            campo_pesquisa.fill(str(cpf_limpo))
            botao_pesquisa.click()

            try:
                page.wait_for_selector("tr[ng-repeat*='usuario']", timeout=3000)
                login = page.locator("tr[ng-repeat*='usuario']").first.locator("td").nth(4).inner_text().strip()
            except:
                login = "Não encontrado"

            resultados.append({
                "CPF_original": cpf_original,
                "CPF_tratado": cpf_limpo,
                "login": login
            })

            campo_pesquisa.fill("")
            page.wait_for_timeout(300)

        browser.close()

    os.makedirs(os.path.dirname(CAMINHO_SAIDA), exist_ok=True)
    df_saida = pd.DataFrame(resultados)
    df_saida.to_excel(CAMINHO_SAIDA, index=False)

    final_root = tk.Tk()
    final_root.withdraw()

    messagebox.showinfo("Sucesso", f"Automação finalizada!\nSalvo em: {CAMINHO_SAIDA}")

    final_root.destroy()


if __name__ == "__main__":
    executar()