import streamlit as st
import requests

# Configurações iniciais da página
st.set_page_config(page_title="Chat Fiscal AI", layout="wide")
st.title("Chat Fiscal AI")

# Inicializa histórico de mensagens na sessão
if "messages" not in st.session_state:
    st.session_state.messages = []

# Função para chamar a API Azure Function
def chamar_api(pergunta):
    url = st.secrets["azure"]["function_url"]  # substitua pelo endpoint real
    headers = {
        "Content-Type": "application/json",
        "x-functions-key": st.secrets["azure"]["functions_key"]  # se sua função exigir chave
    }
    payload = {"pergunta": pergunta}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.text  # ou response.json() se a API retornar JSON estruturado
    else:
        return f"Erro {response.status_code}: {response.text}"

# Exibe mensagens anteriores
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Entrada do usuário
prompt = st.chat_input("Digite sua pergunta aqui...")

if prompt:
    # Adiciona pergunta do usuário no chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Chama a API para obter resposta
    resposta = chamar_api(prompt)

    # Adiciona resposta do bot no chat
    st.session_state.messages.append({"role": "bot", "content": resposta})
    with st.chat_message("bot"):
        st.write(resposta)
