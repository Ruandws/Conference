import pandas as pd
from playwright.sync_api import sync_playwright
import os

# CAMINHO BASEADO NO SEU LOG DE ERRO (OneDrive)
CAMINHO_PLANILHA = r"C:\Users\andrade.ruan\Downloads\planilha1.xlsx"
# Alterado para salvar na mesma pasta onde seu script está rodando (Área de Trabalho via OneDrive)
CAMINHO_SAIDA = r"C:\Users\andrade.ruan\OneDrive - EBSERH\Área de Trabalho\PROJETO\planilha2.xlsx"

URL_LOGIN = "https://servicosti.ebserh.gov.br/#/login"
USUARIO = "adm.rvandrade"
SENHA = "Mississipi1321c"

def executar():
    print("Lendo planilha...")
    df = pd.read_excel(CAMINHO_PLANILHA, dtype=str)
    
    coluna_dados = "CPF" 
    resultados = []

    with sync_playwright() as p:
        print("Iniciando Navegador...")
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Login
        page.goto(URL_LOGIN)
        page.fill("input[ng-model='email']", USUARIO)
        page.fill("input[type='password']", SENHA)
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
    print("Sucesso!")

if __name__ == "__main__":
    executar()