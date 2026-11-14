import json
import os

ARQUIVO_SAIDA = "questoes.json"

def testar_atualizacao():
    # Carrega banco atual ou cria lista vazia
    banco = []
    if os.path.exists(ARQUIVO_SAIDA):
        with open(ARQUIVO_SAIDA, "r", encoding="utf-8") as f:
            try:
                banco = json.load(f)
            except:
                banco = []

    # Adiciona uma questão de teste para provar que o salvamento funciona
    nova_questao = {
        "id": len(banco) + 1,
        "texto": "Questão de teste gerada automaticamente pelo GitHub Actions.",
        "opcoes": ["Alternativa A", "Alternativa B", "Alternativa C", "Alternativa D"],
        "respostaCorreta": "Alternativa A",
        "fundamentacao": "Teste de funcionamento do workflow."
    }
    
    banco.append(nova_questao)

    # Salva o arquivo JSON
    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(banco, f, ensure_ascii=False, indent=4)

    print(f"Sucesso! Total de questões no banco agora: {len(banco)}")

if __name__ == "__main__":
    testar_atualizacao()
