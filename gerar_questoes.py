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
        print("Nenhum PDF novo encontrado.")
        return

    banco_atual = carregar_banco_existente()
    proximo_id = len(banco_atual) + 1
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    for caminho_pdf in pdfs:
        print(f"Processando: {caminho_pdf}")
        reader = PdfReader(caminho_pdf)
        texto_acumulado = ""
        blocos = []

        for page in reader.pages:
            texto_acumulado += (page.extract_text() or "") + "\n"
            if len(texto_acumulado) >= 15000:
                blocos.append(texto_acumulado)
                texto_acumulado = ""
        if texto_acumulado.strip():
            blocos.append(texto_acumulado)

        for idx, bloco in enumerate(blocos, 1):
            print(f"Gerando lote de questões do bloco {idx}/{len(blocos)}...")
            
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
                "Com base EXCLUSIVAMENTE no texto regulatório abaixo, elabore 30 questões inéditas de múltipla escolha.\n\n"
                "Retorne APENAS um JSON puro (sem blocos de código markdown como ```json) no seguinte formato exato de lista:\n"
                f"{exemplo_json}\n\n"
                "TEXTO BASE:\n"
                f"{bloco}"
            )

            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                
                texto_resposta = response.text.strip()
                if texto_resposta.startswith("```"):
                    texto_resposta = texto_resposta.split("```")[1]
                    if texto_resposta.startswith("json"):
                        texto_resposta = texto_resposta[4:]
                texto_resposta = texto_resposta.strip()

                resultado = json.loads(texto_resposta)
                
                if isinstance(resultado, list):
                    for q in resultado:
                        if "texto" in q and "opcoes" in q and "respostaCorreta" in q:
                            if q["respostaCorreta"] in q["opcoes"]:
                                q["id"] = proximo_id
                                banco_atual.append(q)
                                proximo_id += 1
            except Exception as e:
                print(f"Erro ao processar bloco com IA: {e}")

        nome_arquivo = os.path.basename(caminho_pdf)
        shutil.move(caminho_pdf, os.path.join(PASTA_SAIDA, nome_arquivo))

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(banco_atual, f, ensure_ascii=False, indent=4)

    print(f"Processo finalizado. Total no banco: {len(banco_atual)} questões.")

if __name__ == "__main__":
    processar_todos_pdfs()
