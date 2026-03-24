import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from datetime import datetime

class PreparadorPlanilhaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Preparador de Planilhas - Sistema EBSERH")
        self.root.geometry("500x620")

        # --- SEÇÃO DE SELEÇÃO DE CAMINHOS ---
        tk.Label(root, text="GERENCIAMENTO DE ARQUIVOS", font=("Arial", 10, "bold")).pack(pady=10)
        
        # Campo para selecionar a planilha V (Origem)
        self.path_v = self.criar_campo_selecao(
            "1. Selecione a Planilha de Origem (V):", 
            tipo="arquivo"
    )
        
        # Campo para selecionar a pasta onde a P será criada
        self.path_destino = self.criar_campo_selecao(
            "2. Selecione a Pasta para exportar a Planilha P:", 
            tipo="pasta"
        )

        tk.Label(root, text="---" * 20).pack(pady=10)

        # --- SEÇÃO DE DADOS MANUAIS ---
        tk.Label(root, text="DADOS PARA PREENCHIMENTO AUTOMÁTICO", font=("Arial", 10, "bold")).pack(pady=5)
        
        self.campos_fixos = {}
        colunas_manuais = ["Tipo", "Escritório", "Empresa", "Cargo", "Gerente", "Data Expiração"]

        for coluna in colunas_manuais:
            frame = tk.Frame(root)
            frame.pack(fill="x", padx=40, pady=3)
            tk.Label(frame, text=f"{coluna}:", width=15, anchor="w").pack(side="left")
            entry = tk.Entry(frame)
            entry.pack(side="right", expand=True, fill="x")
            self.campos_fixos[coluna] = entry

        # --- BOTÃO DE AÇÃO ---
        self.btn_processar = tk.Button(
            root, text="GERAR PLANILHA P AGORA", 
            bg="#0056b3", fg="white",
            font=("Arial", 11, "bold"), 
            height=2, 
            command=self.processar
        )
        self.btn_processar.pack(pady=35, padx=50, fill="x")

    def criar_campo_selecao(self, texto, tipo):
        frame = tk.Frame(self.root)
        frame.pack(fill="x", padx=25, pady=5)
        tk.Label(frame, text=texto, font=("Arial", 9)).pack(anchor="w")
        
        sub_frame = tk.Frame(frame)
        sub_frame.pack(fill="x")
        
        entry = tk.Entry(sub_frame)
        entry.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        def selecionar():
            if tipo == "arquivo":
                caminho = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
            else:
                caminho = filedialog.askdirectory()
            
            if caminho:
                entry.delete(0, tk.END)
                entry.insert(0, caminho)

        tk.Button(sub_frame, text="Buscar", command=selecionar).pack(side="right")
        return entry

    def processar(self):
        v_path = self.path_v.get()
        destino_pasta = self.path_destino.get()

        if not v_path or not destino_pasta:
            messagebox.showwarning("Atenção", "Preencha a origem e o destino!")
            return

        try:
            # 1. Carregar planilha
            df_v = pd.read_excel(v_path)

            # Normalizar nomes das colunas
            df_v.columns = df_v.columns.str.strip().str.lower()

            # 2. Mapeamento
            mapeamento = {
                "Nome": ["nome completo"],
                "Login": ["login"],
                "CPF": ["cpf"],
                "E-mail alternativo": ["e-mail alternativo", "e-mail", "email"]
            }

            df_p = pd.DataFrame()

            for destino, origens in mapeamento.items():
                for origem in origens:
                    if origem in df_v.columns:
                        df_p[destino] = df_v[origem]
                        break
                else:
                    print(f"Nenhuma coluna encontrada para: {destino}")

            # 3. Inserir dados fixos
            for nome_col, entry in self.campos_fixos.items():
                df_p[nome_col] = entry.get()

            # Garantir CPF com 11 dígitos
            df_p["CPF"] = (
                df_p["CPF"]
                .astype(str)
                .str.replace(".0", "", regex=False)
                .str.zfill(11)
            )

            # 4. Ordem final
            ordem_final = [
                "Tipo", "Escritório", "Nome", "Login", "CPF",
                "E-mail alternativo", "Empresa", "Cargo", "Gerente", "Data Expiração"
            ]

            for col in ordem_final:
                if col not in df_p.columns:
                    df_p[col] = ""

            df_p = df_p[ordem_final]

            # 5. Exportar CSV (Excel Brasil)
            nome_arquivo = "Import.csv"
            caminho_completo = os.path.join(destino_pasta, nome_arquivo)

            df_p.to_csv(
                caminho_completo,
                index=False,
                sep=";",
                encoding="utf-8-sig"
            )

            messagebox.showinfo("Sucesso!", f"Planilha gerada com sucesso!\n\nArquivo: {nome_arquivo}")

        except Exception as e:
            messagebox.showerror("Erro de Processamento", f"Ocorreu um erro: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PreparadorPlanilhaApp(root)
    root.mainloop()