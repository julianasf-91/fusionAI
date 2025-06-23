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

        # Conveter todas as colunas de data em Datetime
        df_resultado['DATA EMISSÃO'] = pd.to_datetime(df_resultado['DATA EMISSÃO'])
        df_resultado['DATA/HORA EVENTO MAIS RECENTE'] = pd.to_datetime(df_resultado['DATA/HORA EVENTO MAIS RECENTE'])

        # Formatar colunas de data e hora
        df_resultado['DATA EMISSÃO'] = df_resultado['DATA EMISSÃO'].dt.strftime('%d/%m/%Y %H:%M:%S')
        df_resultado['DATA/HORA EVENTO MAIS RECENTE'] = df_resultado['DATA/HORA EVENTO MAIS RECENTE'].dt.strftime('%d/%m/%Y %H:%M:%S')

        # Separar coluna de "DATA EMISSÃO" e "HORA EMISSÃO"
        df_resultado[['DATA EMISSÃO', 'HORA EMISSÃO']] = df_resultado['DATA EMISSÃO'].str.split(' ', expand=True)

        # Organizar ordem das colunas
        df_resultado=df_resultado[['CHAVE DE ACESSO', 'MODELO', 'SÉRIE', 'NÚMERO', 'NATUREZA DA OPERAÇÃO',
       'DATA EMISSÃO', 'HORA EMISSÃO', 'CPF/CNPJ Emitente', 'RAZÃO SOCIAL EMITENTE',
       'INSCRIÇÃO ESTADUAL EMITENTE', 'UF EMITENTE', 'MUNICÍPIO EMITENTE',
       'CNPJ DESTINATÁRIO', 'NOME DESTINATÁRIO', 'UF DESTINATÁRIO',
       'INDICADOR IE DESTINATÁRIO', 'DESTINO DA OPERAÇÃO', 'CONSUMIDOR FINAL',
       'PRESENÇA DO COMPRADOR', 'NÚMERO PRODUTO',
       'DESCRIÇÃO DO PRODUTO/SERVIÇO', 'CÓDIGO NCM/SH',
       'NCM/SH (TIPO DE PRODUTO)', 'CFOP', 'QUANTIDADE', 'UNIDADE',
       'VALOR UNITÁRIO', 'VALOR TOTAL', 'EVENTO MAIS RECENTE',
       'DATA/HORA EVENTO MAIS RECENTE', 'VALOR NOTA FISCAL']]
        
        # Salvar DataFrame resultante em CSV no Armazenamento de blobs do Azure
        # (opcional, dependendo do uso posterior)
        # df_resultado.to_csv('df_resultado.csv', index=False)
        # Criar agente de análise de DataFrame com LLM
        

        # # Prompt do sistema com Chain-of-Thought e exemplo de formatação
        system_prompt = SystemMessage(content=(
            "Você é um assistente especializado em análise de notas fiscais usando pandas DataFrames. "
            "Siga SEMPRE este formato de resposta:\n"
            "1. Raciocínio: explique os passos de análise que realizou.\n"
            "2. Query: mostre as queries pandas (ou pseudocódigo) utilizadas.\n"
            "3. Resposta final: formate os resultados para leitura humana.\n\n"
            "Colunas disponíveis: CHAVE DE ACESSO, MODELO, SÉRIE, NÚMERO, NATUREZA DA OPERAÇÃO, DATA EMISSÃO, HORA EMISSÃO, "
            "CPF/CNPJ Emitente, RAZÃO SOCIAL EMITENTE, INSCRIÇÃO ESTADUAL EMITENTE, UF EMITENTE, MUNICÍPIO EMITENTE, "
            "CNPJ DESTINATÁRIO, NOME DESTINATÁRIO, UF DESTINATÁRIO, INDICADOR IE DESTINATÁRIO, DESTINO DA OPERAÇÃO, "
            "CONSUMIDOR FINAL, PRESENÇA DO COMPRADOR, NÚMERO PRODUTO, DESCRIÇÃO DO PRODUTO/SERVIÇO, CÓDIGO NCM/SH, "
            "NCM/SH (TIPO DE PRODUTO), CFOP, QUANTIDADE, UNIDADE, VALOR UNITÁRIO, VALOR TOTAL, EVENTO MAIS RECENTE, "
            "DATA/HORA EVENTO MAIS RECENTE, VALOR NOTA FISCAL.\n\n"
            "Exemplo:\n"
            "Pergunta: 'Qual o produto mais vendido?'\n"
            "1. Raciocínio: Agrupei os dados por 'DESCRIÇÃO DO PRODUTO/SERVIÇO', somando a coluna 'QUANTIDADE'.\n"
            "2. Query: df.groupby('DESCRIÇÃO DO PRODUTO/SERVIÇO')['QUANTIDADE'].sum().sort_values(ascending=False).head(1)\n"
            "3. Resposta final: O produto mais vendido foi 'CIMENTO CP-II' com 1.245 unidades.\n\n"
            "Sempre responda em português e explique seu raciocínio com clareza antes de responder."
        ))

        llm = ChatOpenAI(
            model_name="gpt-4.1-nano-2025-04-14",
            temperature=0.3,
            max_tokens=800,
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

        # Prompt com instrução explícita ao modelo
        prompt_usuario = f"""Responda à pergunta abaixo seguindo este formato:
        1. Raciocínio: explique como chegou à resposta.
        2. Query: mostre o código/pandas utilizado.
        3. Resposta final: apresente o resultado de forma clara e objetiva.

        Pergunta: {pergunta}
        """

        # Obter resposta
        resposta = agent.invoke(prompt_usuario)['output']

        return func.HttpResponse(resposta, status_code=200)

    except Exception as e:
        logging.error(f"Erro: {str(e)}")
        return func.HttpResponse(f"Erro ao processar a requisição: {str(e)}", status_code=500)