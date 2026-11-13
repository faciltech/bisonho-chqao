import glob
import json
import os
import shutil
from google import genai
from google.genai import types
from pydantic import BaseModel
from pypdf import PdfReader

# Lê a chave do cofre seguro do GitHub (Secrets)
CHAVE_API = os.environ.get("GEMINI_API_KEY")
ARQUIVO_SAIDA = "questoes.json"
PASTA_ENTRADA = "pdfs_novos"
PASTA_SAIDA = "pdfs_processados"

if not CHAVE_API:
    raise ValueError("A variável de ambiente GEMINI_API_KEY não foi configurada nos Secrets do GitHub.")

client = genai.Client(api_key=CHAVE_API)


class Questao(BaseModel):
    texto: str
    opcoes: list[str]
    respostaCorreta: str
    fundamentacao: str


class LoteQuestoes(BaseModel):
    questoes: list[Questao]


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
            if len(texto_acumulado) >= 12000:
                blocos.append(texto_acumulado)
                texto_acumulado = ""
        if texto_acumulado.strip():
            blocos.append(texto_acumulado)

        for idx, bloco in enumerate(blocos, 1):
            print(f"Gerando questões do bloco {idx}/{len(blocos)}...")
            prompt = f"""
            Atue como uma banca examinadora do Exército Brasileiro elaborando prova para o CHQAO.
            Com base EXCLUSIVAMENTE no texto regulatório abaixo, elabore 30 questões inéditas de múltipla escolha.
            
            Regras obrigatórias:
            1. Cada questão deve ter exatamente 4 alternativas em 'opcoes'.
            2. O campo 'respostaCorreta' deve conter o texto EXATAMENTE IGUAL ao da alternativa correta listada em 'opcoes'.
            3. No campo 'fundamentacao', cite expressamente o artigo, parágrafo, inciso ou item do texto que justifica o gabarito.
            4. Evite questões óbvias; cobre prazos, competências, classificações e exceções.

            TEXTO BASE:
            {bloco}
            """

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=LoteQuestoes,
                    temperature=0.3,
                ),
            )

            resultado = json.loads(response.text)
            for q in resultado.get("questoes", []):
                if q["respostaCorreta"] in q["opcoes"]:
                    q["id"] = proximo_id
                    banco_atual.append(q)
                    proximo_id += 1

        # Move o PDF processado para não rodar de novo no futuro
        nome_arquivo = os.path.basename(caminho_pdf)
        shutil.move(caminho_pdf, os.path.join(PASTA_SAIDA, nome_arquivo))

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(banco_atual, f, ensure_ascii=False, indent=4)

    print(f"Processo finalizado. Total no banco: {len(banco_atual)} questões.")


if __name__ == "__main__":
    processar_todos_pdfs()
