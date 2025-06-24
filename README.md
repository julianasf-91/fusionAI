# 📄 Chat Fiscal - FusionAI

Um agente inteligente capaz de responder perguntas sobre arquivos fiscais CSV compactados, usando LLM, pandas, LangChain e infraestrutura na nuvem.

## 🚀 Visão Geral

Esta aplicação permite ao usuário consultar, via linguagem natural, um conjunto de notas fiscais em formato CSV. O sistema descompacta os dados, processa com pandas, armazena no Azure Blob e responde usando um agente LangChain com LLM.


## 🧰 Tecnologias Utilizadas

| Tecnologia          | Finalidade                                      |
|---------------------|-------------------------------------------------|
| LangChain           | Framework de construção do agente               |
| GPT-4.1-nano        | Modelo LLM econômico e eficiente da OpenAI      |
| Python (pandas)     | Processamento e análise de dados                |
| Azure Functions     | Backend da API (serverless)                     |
| Azure Key Vault     | Armazenamento seguro das chaves                 |
| Azure Blob Storage  | Armazenamento do DataFrame em Parquet           |
| Streamlit           | Interface web amigável (versão gratuita usada)  |


## 🧠 Por que essas escolhas?

- **LangChain** foi escolhido pela sua facilidade de integração entre agentes e ferramentas externas, como DataFrames e LLMs.
- **GPT-4.1-nano-2025-04-14** foi escolhido por oferecer um bom equilíbrio entre custo, qualidade e limitação de tokens.
- **Pandas** foi utilizado para fazer toda a transformação prévia dos dados, reduzindo drasticamente a carga de tokens que precisaria ser enviada à LLM, o que ajuda a economizar em chamadas pagas.
- **Azure Functions + Key Vault + Blob Storage** permitiram uma solução serverless, segura e com custo zero no plano gratuito.
- **Streamlit** foi usado por ser gratuito e permitir uma entrega rápida com uma interface amigável.


## 💡 Exemplo de perguntas que podem ser feitas

- Qual fornecedor teve o maior montante recebido?
- Qual produto teve maior volume entregue?
- Quais foram os três estados com maior valor em notas?
- Qual é a média de valor por nota fiscal?
- Qual item foi mais vendido em quantidade?
- Quais municípios emitiram mais notas?


## 🛡️ Segurança

- 🔐 As **chaves sensíveis** (OpenAI, Blob) estão ocultas no `secrets.toml` e no **Azure Key Vault**
- ✅ O backend usa `DefaultAzureCredential` com **registro de aplicativo** no Azure
- 🔒 Nenhuma informação sensível está hardcoded no repositório


## ▶️ Como Rodar Localmente
1. Clone o repositório:
git clone https://github.com/julianasf-91/fusionAI.git
cd fusionAI/front-agente-notas-fiscais

2. Crie o arquivo .streamlit/secrets.toml com:
[azure]
function_url = "SUA_URL_DA_FUNCTION"
functions_key = "SUA_CHAVE_DA_FUNCTION"

3. Instale as dependências:
pip install -r requirements.txt

4. Execute o app:
streamlit run app.py


## 📌 Observações
A assinatura da Azure utilizada é gratuita.
A interface e os dados foram otimizados para economizar tokens.
O sistema é modular e pode ser estendido para outras bases fiscais.

## ✨ Desenvolvido por
Juliana Ferreira | FusionAI
🔗 https://github.com/julianasf-91/fusionAI