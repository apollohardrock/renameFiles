import os
import re
import json
import pdfplumber
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk, simpledialog
import urllib.request
import subprocess
import time

class RenomeadorPDFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Renomeador Inteligente de PDFs")
        self.root.geometry("750x750") # Aumentei a altura para caber a nova seção
        
        # Identifica a pasta de execução corretamente
        if getattr(sys, 'frozen', False):
            self.pasta_padrao = os.path.dirname(sys.executable)
        else:
            self.pasta_padrao = os.path.dirname(os.path.abspath(__file__))

        # 1. DECLARE AS VARIÁVEIS DE VERSÃO AQUI PRIMEIRO
        self.versao_atual = "1.4"
        self.url_versao = "https://raw.githubusercontent.com/apollohardrock/renameFiles/main/versao.txt"
        self.url_exe = "https://github.com/apollohardrock/renameFiles/releases/latest/download/renameFiles.exe"


        self.pasta_selecionada = ""
        self.padrao_nomeclatura = [] 
        
        # Sistema de Templates
        self.arquivo_templates = os.path.join(self.pasta_padrao, "templates_renomeador.json")
        self.templates_salvos = self.carregar_templates_do_arquivo()
        
        self.criar_widgets()
        self.atualizar_combobox_templates()
        
    def criar_widgets(self):
        # --- Seção 1: Seleção de Pasta ---
        frame_pasta = tk.LabelFrame(self.root, text="1. Selecionar Pasta de Arquivos", padx=10, pady=10)
        frame_pasta.pack(fill="x", padx=10, pady=5)
        
        self.btn_pasta = tk.Button(frame_pasta, text="Procurar Pasta...", command=self.selecionar_pasta)
        self.btn_pasta.pack(side="left")
        
        self.lbl_pasta = tk.Label(frame_pasta, text="Nenhuma pasta selecionada", fg="red")
        self.lbl_pasta.pack(side="left", padx=10)
        
        # --- Seção 2: Modelos Salvos (NOVIDADE) ---
        frame_templates = tk.LabelFrame(self.root, text="2. Modelos Salvos", padx=10, pady=10)
        frame_templates.pack(fill="x", padx=10, pady=5)
        
        linha_tpl = tk.Frame(frame_templates)
        linha_tpl.pack(fill="x")
        
        tk.Label(linha_tpl, text="Modelo:").pack(side="left")
        self.combo_templates = ttk.Combobox(linha_tpl, state="readonly", width=30)
        self.combo_templates.pack(side="left", padx=(5, 10))
        
        btn_carregar = tk.Button(linha_tpl, text="Carregar", command=self.carregar_modelo_selecionado)
        btn_carregar.pack(side="left", padx=2)
        
        btn_salvar_tpl = tk.Button(linha_tpl, text="Salvar Atual como Novo Modelo", command=self.salvar_modelo_atual)
        btn_salvar_tpl.pack(side="left", padx=10)
        
        btn_excluir_tpl = tk.Button(linha_tpl, text="Excluir", command=self.excluir_modelo, fg="red")
        btn_excluir_tpl.pack(side="right", padx=2)

        # --- Seção 3: Campos Dinâmicos e Textos Fixos ---
        frame_campos = tk.LabelFrame(self.root, text="3. Construa o Padrão do Nome", padx=10, pady=10)
        frame_campos.pack(fill="x", padx=10, pady=5)
        
        lbl_instrucao = tk.Label(frame_campos, text="Adicione campos ou carregue um modelo acima.", justify="left")
        lbl_instrucao.pack(anchor="w", pady=(0, 5))
        
        linha_add = tk.Frame(frame_campos)
        linha_add.pack(fill="x")
        
        tk.Label(linha_add, text="Texto/Campo:").pack(side="left")
        self.entry_campo = tk.Entry(linha_add, width=25)
        self.entry_campo.pack(side="left", padx=(2, 10))
        
        tk.Label(linha_add, text="Aparição nº:").pack(side="left")
        self.spin_ocorrencia = tk.Spinbox(linha_add, from_=1, to=10, width=3)
        self.spin_ocorrencia.pack(side="left", padx=(2, 10))
        
        btn_add_pdf = tk.Button(linha_add, text="+ Buscar no PDF", bg="#e0f7fa", command=lambda: self.adicionar_item('pdf'))
        btn_add_pdf.pack(side="left", padx=2)
        
        btn_add_fixo = tk.Button(linha_add, text="+ Texto Fixo", bg="#fff9c4", command=lambda: self.adicionar_item('fixo'))
        btn_add_fixo.pack(side="left", padx=2)
        
        btn_limpar = tk.Button(linha_add, text="Limpar", command=self.limpar_campos)
        btn_limpar.pack(side="right")
        
        self.listbox_campos = tk.Listbox(frame_campos, height=5)
        self.listbox_campos.pack(fill="x", pady=10)
        
        # --- Seção 4: Execução ---
        frame_exec = tk.Frame(self.root, pady=10)
        frame_exec.pack(fill="x", padx=10)
        
        self.btn_executar = tk.Button(frame_exec, text="RENOMEAR ARQUIVOS", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), command=self.processar_arquivos)
        self.btn_executar.pack(fill="x")
        
        tk.Label(self.root, text="Status da Execução:").pack(anchor="w", padx=10)
        self.log_area = scrolledtext.ScrolledText(self.root, height=10, state='disabled', bg="#f4f4f4")
        self.log_area.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # --- Rodapé (Footer) ---
        frame_rodape = tk.Frame(self.root)
        frame_rodape.pack(fill="x", padx=10, pady=5)
        
        # Mostra a versão atual no canto esquerdo
        lbl_versao = tk.Label(frame_rodape, text=f"Versão Atual: {self.versao_atual}", fg="gray", font=("Arial", 9, "italic"))
        lbl_versao.pack(side="left")
        
        # Botão de atualização no canto direito
        btn_atualizar = tk.Button(frame_rodape, text="🔄 Verificar Atualizações", command=self.verificar_atualizacao, bg="#2196F3", fg="white")
        btn_atualizar.pack(side="right")


    def carregar_templates_do_arquivo(self):
        if os.path.exists(self.arquivo_templates):
            try:
                with open(self.arquivo_templates, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def salvar_templates_no_arquivo(self):
        try:
            with open(self.arquivo_templates, 'w', encoding='utf-8') as f:
                json.dump(self.templates_salvos, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar os templates no disco:\n{e}")

    def atualizar_combobox_templates(self):
        modelos = list(self.templates_salvos.keys())
        self.combo_templates['values'] = modelos
        if modelos and not self.combo_templates.get():
            self.combo_templates.current(0)
        elif not modelos:
            self.combo_templates.set('')

    def salvar_modelo_atual(self):
        if not self.padrao_nomeclatura:
            messagebox.showwarning("Aviso", "A lista atual está vazia! Adicione campos antes de salvar um modelo.")
            return
            
        nome_modelo = simpledialog.askstring("Salvar Modelo", "Digite um nome para este padrão\n(ex: 'Notas Fiscais de Serviço', 'Boletos Sicredi'):")
        if nome_modelo:
            nome_modelo = nome_modelo.strip()
            self.templates_salvos[nome_modelo] = self.padrao_nomeclatura.copy()
            self.salvar_templates_no_arquivo()
            self.atualizar_combobox_templates()
            self.combo_templates.set(nome_modelo)
            self.log(f"✅ Modelo '{nome_modelo}' salvo com sucesso!")

    def carregar_modelo_selecionado(self):
        nome_modelo = self.combo_templates.get()
        if nome_modelo in self.templates_salvos:
            self.padrao_nomeclatura = self.templates_salvos[nome_modelo].copy()
            self.atualizar_listbox()
            self.log(f"🔄 Modelo '{nome_modelo}' carregado.")
        else:
            messagebox.showwarning("Aviso", "Selecione um modelo válido na lista.")

    def excluir_modelo(self):
        nome_modelo = self.combo_templates.get()
        if nome_modelo in self.templates_salvos:
            resposta = messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o modelo '{nome_modelo}'?")
            if resposta:
                del self.templates_salvos[nome_modelo]
                self.salvar_templates_no_arquivo()
                self.atualizar_combobox_templates()
                self.limpar_campos()
                self.log(f"🗑️ Modelo '{nome_modelo}' excluído.")

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory(initialdir=self.pasta_padrao)
        if pasta:
            self.pasta_selecionada = pasta
            self.lbl_pasta.config(text=self.pasta_selecionada, fg="green")
            
    def adicionar_item(self, tipo):
        texto = self.entry_campo.get().strip()
        ocorrencia = int(self.spin_ocorrencia.get())
        if texto:
            self.padrao_nomeclatura.append({"tipo": tipo, "valor": texto, "ocorrencia": ocorrencia})
            self.atualizar_listbox()
            self.entry_campo.delete(0, tk.END)
            self.spin_ocorrencia.delete(0, tk.END)
            self.spin_ocorrencia.insert(0, "1")
            self.entry_campo.focus()
            
    def limpar_campos(self):
        self.padrao_nomeclatura = []
        self.atualizar_listbox()
        
    def atualizar_listbox(self):
        self.listbox_campos.delete(0, tk.END)
        for i, item in enumerate(self.padrao_nomeclatura):
            if item['tipo'] == 'fixo':
                self.listbox_campos.insert(tk.END, f"{i+1}º -> [TEXTO FIXO]: {item['valor']}")
                self.listbox_campos.itemconfig(i, {'fg': '#c4a000'})
            else:
                ordem_texto = f"({item['ocorrencia']}ª aparição no PDF)" if item['ocorrencia'] > 1 else ""
                self.listbox_campos.insert(tk.END, f"{i+1}º -> [BUSCA NO PDF]: {item['valor']} {ordem_texto}")
                self.listbox_campos.itemconfig(i, {'fg': '#006064'})
                
    def log(self, mensagem):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, mensagem + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
        self.root.update_idletasks()
        
    def limpar_nome_arquivo(self, nome):
        nome_seguro = str(nome).replace("/", "-").replace("\\", "-")
        return re.sub(r'[*?:"<>|]', "", nome_seguro).strip()

    def extrair_valor_dinamico(self, texto, campo, aparicao):
        try:
            # 1. Higienização de Tabela Sicoob (Quebras de linha vazias)
            texto_limpo = re.sub(r'\n[ \t]+', ' ', texto)
            
            # NOVO: Correção de Desalinhamento (A Ilusão de Ótica do Sicoob)
            # Puxa o texto que subiu para a linha do Destinatário de volta para a linha do Nome
            texto_limpo = re.sub(
                r'Destinatário:\s*([^\n]+)\n[\s]*Nome:([^\n]*)', 
                r'Destinatário:\nNome: \1 \2', 
                texto_limpo, 
                flags=re.IGNORECASE
            )
            
            # 2. Motor de Busca Flexível
            padrao = re.compile(rf"{re.escape(campo)}[\s\n:]*([^\n\r]+)", re.IGNORECASE)
            
            resultados = list(padrao.finditer(texto_limpo))
            
            if resultados and len(resultados) >= aparicao:
                valor = resultados[aparicao - 1].group(1).strip()
                
                # Filtro Automático 1: Remove horas grudadas na Data
                valor = re.sub(r'(\d{2}/\d{2}/\d{4})[\s-]+(?:\d{2}:\d{2}(?::\d{2})?)', r'\1', valor)
                
                # Filtro Automático 2: Limpa sujeiras ao redor de Valores Monetários
                if "valor" in campo.lower():
                    match_valor = re.search(r'(R\$[\s]*[0-9.,]+)', valor)
                    if match_valor:
                        valor = match_valor.group(1)
                
                # Filtro Automático 3: Limpeza de MEI e Códigos Bancários
                elif any(palavra in campo.lower() for palavra in ["nome", "razão", "razao", "favorecido", "destinatário", "beneficiário"]):
                    # AQUI ESTÁ A MÁGICA NOVA: Regex atualizada para pegar números com espaços
                    valor = re.sub(r'(?<!\S)(?:\d[\s.-]*){6,}(?!\S)', '', valor)
                    valor = re.sub(r'\s+', ' ', valor).strip()
                        
                return valor
            else:
                return f"[{campo} n/e]"
        except Exception:
            return f"[Erro na busca de {campo}]"
        
    def processar_arquivos(self):
        if not self.pasta_selecionada:
            messagebox.showwarning("Aviso", "Por favor, selecione a pasta com os PDFs primeiro!")
            return
        if not self.padrao_nomeclatura:
            messagebox.showwarning("Aviso", "Construa o padrão de nome adicionando pelo menos um item!")
            return
            
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        
        arquivos_pdf = [f for f in os.listdir(self.pasta_selecionada) if f.lower().endswith(".pdf")]
        
        if not arquivos_pdf:
            self.log("❌ Nenhum arquivo PDF encontrado na pasta selecionada.")
            return
            
        self.log(f"Iniciando processamento de {len(arquivos_pdf)} arquivos...\n")
        self.btn_executar.config(state='disabled', text="PROCESSANDO...")
        
        for arquivo in arquivos_pdf:
            caminho_antigo = os.path.join(self.pasta_selecionada, arquivo)
            valores_extraidos = []
            
            try:
                with pdfplumber.open(caminho_antigo) as pdf:
                    texto = pdf.pages[0].extract_text()
                    
                if texto:
                    for item in self.padrao_nomeclatura:
                        if item['tipo'] == 'fixo':
                            valores_extraidos.append(self.limpar_nome_arquivo(item['valor']))
                        else:
                            valor_pdf = self.extrair_valor_dinamico(texto, item['valor'], item['ocorrencia'])
                            if valor_pdf:
                                valores_extraidos.append(valor_pdf)
                            else:
                                valores_extraidos.append(f"[{item['valor']} n/e]")
                                
                if valores_extraidos:
                    novo_nome_base = " - ".join(valores_extraidos)
                    novo_nome = f"{novo_nome_base}.pdf"
                    caminho_novo = os.path.join(self.pasta_selecionada, novo_nome)
                    
                    contador = 1
                    while os.path.exists(caminho_novo):
                        caminho_novo = os.path.join(self.pasta_selecionada, f"{novo_nome_base}_{contador}.pdf")
                        contador += 1
                        
                    os.rename(caminho_antigo, caminho_novo)
                    self.log(f"✅ SUCESSO: {arquivo}\n      -> {os.path.basename(caminho_novo)}")
                else:
                    self.log(f"⚠️ AVISO: Não consegui ler texto em {arquivo}")
                    
            except Exception as e:
                self.log(f"❌ ERRO ao abrir {arquivo}: {str(e)}")
                
        self.log("\nProcessamento finalizado!")
        self.btn_executar.config(state='normal', text="RENOMEAR ARQUIVOS")

    def verificar_atualizacao(self):
        self.log("Verificando se há atualizações...")
        self.root.update()
        
        try:
            # O truque do cache: adiciona os milissegundos atuais no final do link
            import time
            url_sem_cache = f"{self.url_versao}?t={int(time.time())}"
            
            resposta = urllib.request.urlopen(url_sem_cache, timeout=5)
            versao_online = resposta.read().decode('utf-8').strip()

            if versao_online > self.versao_atual:
                if messagebox.askyesno("Atualização Disponível", f"Uma nova versão ({versao_online}) foi encontrada!\nSua versão atual: {self.versao_atual}\n\nDeseja atualizar agora?"):
                    self.aplicar_atualizacao()
            else:
                messagebox.showinfo("Atualizado", "O sistema já está na versão mais recente!")
                self.log(f"Versão local: {self.versao_atual} | Versão online lida: {versao_online}")
                
        except Exception as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível verificar atualizações.\nVerifique sua internet ou servidor.\n\nDetalhe: {e}")
            self.log("Falha ao verificar atualizações.")

    def aplicar_atualizacao(self):
        self.btn_executar.config(state='disabled')
        self.log("Baixando nova versão... O aplicativo será reiniciado em instantes.")
        self.root.update()

        exe_antigo = sys.executable 
        exe_novo = exe_antigo + "_temp.exe"

        try:
            # Baixa o novo arquivo
            urllib.request.urlretrieve(self.url_exe, exe_novo)

            # Trava de Segurança
            tamanho_baixado = os.path.getsize(exe_novo)
            if tamanho_baixado < 10 * 1024 * 1024:  # 10 MB em bytes
                self.log("❌ Erro: O arquivo baixado é muito pequeno.")
                os.remove(exe_novo)
                self.btn_executar.config(state='normal')
                return

            bat_path = os.path.join(os.path.dirname(exe_antigo), "atualizador.bat")
            nome_original = os.path.basename(exe_antigo)
            
            # --- O SCRIPT BAT BLINDADO ---
            # Ele cria um loop (:tentar_deletar). Fica tentando apagar o arquivo a cada 1 segundo.
            # Só avança para o "ren" quando o exe_antigo não existir mais.
            comandos_bat = f"""@echo off
:tentar_deletar
timeout /t 1 /nobreak > NUL
del "{exe_antigo}" > NUL 2>&1
if exist "{exe_antigo}" goto tentar_deletar

ren "{exe_novo}" "{nome_original}"
start "" "{exe_antigo}"
del "%~f0"
"""
            with open(bat_path, 'w', encoding='utf-8') as f:
                f.write(comandos_bat)

            # Inicia o BAT desvinculado do processo atual
            subprocess.Popen(bat_path, shell=True)
            
            # Força o fechamento imediato do aplicativo
            self.root.destroy()
            sys.exit()

        except Exception as e:
            self.log(f"Erro crítico durante a atualização: {e}")
            self.btn_executar.config(state='normal')

if __name__ == "__main__":
    root = tk.Tk()
    app = RenomeadorPDFApp(root)
    root.mainloop()