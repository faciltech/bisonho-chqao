# Bisonho - Simulado CHQAO

## Como configurar no GitHub (Passo a Passo)

1. **Criar o Repositório:** Crie um repositório novo no GitHub (pode ser Público ou Privado).
2. **Subir os Arquivos:** Extraia todos os arquivos deste pacote e faça o upload mantendo a estrutura de pastas (incluindo a pasta oculta `.github`).
3. **Configurar a Chave da API:**
   - Acesse **Settings** > **Secrets and variables** > **Actions** no seu repositório.
   - Clique em **New repository secret**.
   - Nome: `GEMINI_API_KEY`
   - Valor: Cole sua chave gerada no Google AI Studio.
4. **Publicar o Site (GitHub Pages):**
   - Acesse **Settings** > **Pages**.
   - Em **Branch**, selecione `main` (pasta `/root`) e clique em **Save**.

## Como alimentar com novos PDFs

1. No GitHub, abra a pasta `pdfs_novos`.
2. Clique em **Add file** > **Upload files** e envie o PDF do regulamento.
3. Clique em **Commit changes**.
4. O GitHub Actions processará o arquivo automaticamente em ~1 minuto, atualizará o `questoes.json` e moverá o PDF para `pdfs_processados`.
