import glob
import json
import os
import shutil
from google import genai
from pypdf import PdfReader

CHAVE_API = os.environ.get("GEMINI_API_KEY")
ARQUIVO_SAIDA = "questoes.json"
PASTA_ENTRADA = "pdfs_novos"
PASTA_SAIDA = "pdfs_processados"

if not CHAVE_API:
    raise ValueError("A variavel GEMINI_API_KEY nao foi configurada nos Secrets do GitHub.")

client = genai.Client(api_key=CHAVE_API)

def carregar_banco_existente():
    if os.path.exists(ARQUIVO_SAIDA):
        with open(ARQUIVO_SAIDA, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def processar_todos_pdfs():
    pdfs = glob.glob(os.path.join(PASTA_ENTRADA, "*.pdf"))
    if not pdfs:
        print("Nenhum PDF novo encontrado na pasta.")
        return

    banco_atual = carregar_banco_existente()
    proximo_id = len(banco_atual) + 1
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    for caminho_pdf in pdfs:
        print(f"Processando arquivo: {caminho_pdf}")
        reader = PdfReader(caminho_pdf)
        texto_acumulado = ""
        
        for i, page in enumerate(reader.pages):
            texto_pagina = page.extract_text() or ""
            texto_acumulado += texto_pagina + "\n"
            
        print(f"Total de caracteres extraídos do PDF: {len(texto_acumulado)}")
        
        if len(texto_acumulado.strip()) < 50:
            print("AVISO CRÍTICO: O PDF parece ser uma imagem digitalizada sem texto selecionável (OCR necessário). O script não pode ler o conteúdo.")
            # Move o arquivo para processados para não travar o fluxo
            nome_arquivo = os.path.basename(caminho_pdf)
            destino = os.path.join(PASTA_SAIDA, nome_arquivo)
            if os.path.exists(destino):
                os.remove(destino)
            shutil.move(caminho_pdf, destino)
            continue

        # Divide em blocos caso o texto seja muito longo
        blocos = []
        for i in range(0, len(texto_acumulado), 15000):
            blocos.append(texto_acumulado[i:i+15000])

        for idx, bloco in enumerate(blocos, 1):
            print(f"Enviando bloco {idx}/{len(blocos)} para a IA gerar questões...")
            
            exemplo_json = """[
  {
    "texto": "Enunciado da questão aqui?",
    "opcoes": [
      "Alternativa A",
      "Alternativa B",
      "Alternativa C",
      "Alternativa D"
    ],
    "respostaCorreta": "Alternativa A",
    "fundamentacao": "Artigo X do regulamento."
  }
]"""

            prompt = (
                "Atue como uma banca examinadora do Exército Brasileiro elaborando prova para o CHQAO.\n"
                "Com base EXCLUSIVAMENTE no texto regulatório abaixo, elabore questões inéditas de múltipla escolha.\n\n"
                "Retorne APENAS um JSON puro em formato de lista contendo os campos: texto, opcoes (array com 4 strings), respostaCorreta e fundamentacao.\n"
                "Exemplo de estrutura:\n"
                + exemplo_json + "\n\n"
                "TEXTO BASE:\n"
                + bloco
            )

            try:
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt
                )
                
                texto_resposta = response.text.strip()
                print(f"Resposta bruta recebida do Gemini (tamanho: {len(texto_resposta)})")

                if "```json" in texto_resposta:
                    texto_resposta = texto_resposta.split("```json")[1].split("```")[0].strip()
                elif "```" in texto_resposta:
                    texto_resposta = texto_resposta.split("```")[1].split("```")[0].strip()

                resultado = json.loads(texto_resposta)
                
                if isinstance(resultado, list):
                    adicionadas = 0
                    for q in resultado:
                        if "texto" in q and "opcoes" in q and "respostaCorreta" in q:
                            q["id"] = proximo_id
                            banco_atual.append(q)
                            proximo_id += 1
                            adicionadas += 1
                    print(f"Sucesso! {adicionadas} questões adicionadas ao banco.")
                else:
                    print("Aviso: A resposta da IA não retornou uma lista JSON válida.")
            except Exception as e:
                print(f"ERRO ao processar com a IA ou converter JSON: {e}")

        nome_arquivo = os.path.basename(caminho_pdf)
        destino = os.path.join(PASTA_SAIDA, nome_arquivo)
        if os.path.exists(destino):
            os.remove(destino)
        shutil.move(caminho_pdf, destino)

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(banco_atual, f, ensure_ascii=False, indent=4)

    print(f"Processo finalizado. Total geral no banco: {len(banco_atual)} questões.")

if __name__ == "__main__":
    processar_todos_pdfs()
