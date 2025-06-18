# Register this blueprint by adding the following line of code 
# to your entry point file.  
# app.register_functions(fiscal_llm) 
# 
# Please refer to https://aka.ms/azure-functions-python-blueprints


import azure.functions as func
import logging
import pandas as pd
import zipfile
from io import BytesIO
import requests
from langchain_community.chat_models import ChatOpenAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from langchain.schema import SystemMessage

fiscal_llm = func.Blueprint()


@fiscal_llm.route(route="fiscal_llm_endpoint", auth_level=func.AuthLevel.FUNCTION)
def fiscal_llm_endpoint(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # Obter pergunta do corpo da requisição
        req_body = req.get_json()
        pergunta = req_body.get('pergunta')
        
        if not pergunta:
            return func.HttpResponse("Parâmetro 'pergunta' não encontrado no corpo da requisição", status_code=400)

        # Configuração do Azure Key Vault
        key_vault_name = "integracaoapi"
        key_vault_url = f"https://{key_vault_name}.vault.azure.net/"
        secret_name = "apiopenia"

        # Autenticação
        credential = DefaultAzureCredential()
        secret_client = SecretClient(vault_url=key_vault_url, credential=credential)
        openai_api_key = secret_client.get_secret(secret_name).value

        # Download e processamento dos dados
        url = 'https://drive.google.com/uc?export=download&id=1FlijXfHFSkFq0nf0I8mt3J9-NOOymR3y'
        response = requests.get(url)
        
        with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
            cabecalho_file = [f for f in zip_ref.namelist() if 'Cabecalho' in f][0]
            itens_file = [f for f in zip_ref.namelist() if 'Itens' in f][0]
            
            with zip_ref.open(cabecalho_file) as cf:
                df_cabecalho = pd.read_csv(cf)
            
            with zip_ref.open(itens_file) as itf:
                df_itens = pd.read_csv(itf)

        df_resultado = pd.merge(df_itens, df_cabecalho, on='CHAVE DE ACESSO', how='left')
        df_resultado = df_resultado.loc[:, ~df_resultado.columns.str.endswith('_y')]
        df_resultado.columns = df_resultado.columns.str.rstrip('_x')

        # Configuração do agente LangChain
        system_prompt = SystemMessage(content=(
            "Você é um assistente especializado em dados fiscais. "
            "As colunas disponíveis no DataFrame são: "
            "CHAVE DE ACESSO, MODELO, SÉRIE, NÚMERO, NATUREZA DA OPERAÇÃO, DATA EMISSÃO, CPF/CNPJ Emitente, "
            "RAZÃO SOCIAL EMITENTE, INSCRIÇÃO ESTADUAL EMITENTE, UF EMITENTE, MUNICÍPIO EMITENTE, CNPJ DESTINATÁRIO, "
            "NOME DESTINATÁRIO, UF DESTINATÁRIO, INDICADOR IE DESTINATÁRIO, DESTINO DA OPERAÇÃO, CONSUMIDOR FINAL, "
            "PRESENÇA DO COMPRADOR, NÚMERO PRODUTO, DESCRIÇÃO DO PRODUTO/SERVIÇO, CÓDIGO NCM/SH, NCM/SH (TIPO DE PRODUTO), "
            "CFOP, QUANTIDADE, UNIDADE, VALOR UNITÁRIO, VALOR TOTAL, EVENTO MAIS RECENTE, DATA/HORA EVENTO MAIS RECENTE, "
            "VALOR NOTA FISCAL. "
            "Responda sempre em português, com linguagem clara e objetiva. "
            "Formate valores monetários como 'R$ 1.234,56' e datas como 'DD/MM/AAAA'. "
            "Se a pergunta for ambígua, peça esclarecimentos. Seja preciso e não invente dados."
        ))

        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.2,
            max_tokens=400,
            openai_api_key=openai_api_key
        )

        agent = create_pandas_dataframe_agent(
            llm=llm,
            df=df_resultado,
            verbose=False,
            agent_type="openai-tools",
            agent_kwargs={"system_message": system_prompt},
            allow_dangerous_code=True
        )

        # Obter resposta
        resposta = agent.invoke(pergunta)['output']

        return func.HttpResponse(resposta, status_code=200)

    except Exception as e:
        logging.error(f"Erro: {str(e)}")
        return func.HttpResponse(f"Erro ao processar a requisição: {str(e)}", status_code=500)