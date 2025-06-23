import streamlit as st
import pandas as pd
import requests

# Configurações iniciais da página
st.set_page_config(
    page_title="Chat Fiscal",
    page_icon="📄",
    layout="wide"
)

# Estilo personalizado
st.markdown("""
    <style>
        body {
            background-color: #f5f8fa;
        }

        .stChatMessage {
            padding: 10px;
            border-radius: 12px;
            margin: 10px 0;
        }

        footer {visibility: hidden;}

        .fusion-footer {
            text-align: center;
            color: gray;
            font-size: 13px;
            margin-top: 40px;
        }
    </style>
""", unsafe_allow_html=True)

# Logo e título
col1, col2 = st.columns([1, 5])
with col1:
    st.image("logo_fusionai.png", width=150)

with col2:
    st.markdown("<h1 style='color: #003f5c;'>Chat Fiscal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:18px; color: #0088a9;'>Inteligência que transforma o entendimento fiscal</p>", unsafe_allow_html=True)

st.markdown("---")

# Leitura do csv
try:
    df = pd.read_csv("df_resultado.csv")
    with st.expander("🔍 Visualizar base de Notas Fiscais"):
        st.dataframe(df, use_container_width=True)
except Exception as e:
    st.warning("Não foi possível carregar a base de conhecimento.")

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
    with st.chat_message(msg["role"], avatar="👨‍💻" if msg["role"] == "user" else "🤖"):
        st.write(msg["content"])

# Entrada do usuário
prompt = st.chat_input("Digite sua pergunta aqui...")

if prompt:
    # Adiciona pergunta do usuário no chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👨‍💻"):
        st.write(prompt)

    # Chama a API para obter resposta
    resposta = chamar_api(prompt)

    # Adiciona resposta do bot no chat
    st.session_state.messages.append({"role": "bot", "content": resposta})
    with st.chat_message("bot", avatar="🤖"):
        st.write(resposta)

# Rodapé
st.markdown("""
    <div class='fusion-footer'>
        Desenvolvido por <b>FusionAI by Juliana Ferreira</b> · <a href='https://github.com/julianasf-91/fusionAI' target='_blank'>GitHub</a>
    </div>
""", unsafe_allow_html=True)