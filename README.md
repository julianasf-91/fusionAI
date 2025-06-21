# 📄 Chat Fiscal - FusionAI

Um agente conversacional inteligente capaz de responder perguntas sobre notas fiscais a partir de arquivos CSV compactados.

## 🚀 Visão Geral

Esta aplicação permite ao usuário realizar perguntas em linguagem natural sobre arquivos fiscais CSV (como fornecedor com maior montante, itens mais vendidos etc.), utilizando uma LLM com interface web.

---

## 🧰 Tecnologias Utilizadas

- **🧠 LLM**: `gpt-4.1-nano-2025-04-14` (OpenAI)
- **🔗 Framework**: [LangChain](https://www.langchain.com/)
- **📊 Processamento de Dados**: Python com pandas (para economizar tokens)
- **☁️ API**: Azure Functions (plano gratuito)
- **🔐 Segurança**: Azure Key Vault para armazenar a chave da API
- **💬 Interface**: Streamlit (hospedado na versão gratuita)

---

## 🧠 Por que essas escolhas?

- **LangChain** foi escolhido pela sua facilidade de integração entre agentes e ferramentas externas, como DataFrames e LLMs.
- **GPT-4.1-nano-2025-04-14** foi escolhido por oferecer um bom equilíbrio entre custo, qualidade e limitação de tokens.
- **Pandas** foi utilizado para fazer toda a transformação prévia dos dados, reduzindo drasticamente a carga de tokens que precisaria ser enviada à LLM, o que ajuda a economizar em chamadas pagas.
- **Azure Functions + Key Vault** permitiram uma solução serverless, segura e com custo zero no plano gratuito.
- **Streamlit** foi usado por ser gratuito e permitir uma entrega rápida com uma interface amigável.

---

## 💡 Exemplo de perguntas que podem ser feitas

- "Qual fornecedor teve o maior montante recebido?"
- "Qual produto teve maior volume em quantidade?"
- "Quais os três estados com maior valor em notas fiscais?"
- "Qual a média de valor por nota fiscal?"

---

## 🛡️ Segurança

As chaves sensíveis estão **ocultas**:
- A chave da OpenAI foi armazenada no **Azure Key Vault**.
- A comunicação entre Streamlit e API é protegida com chave da Azure Function via `secrets.toml`.

