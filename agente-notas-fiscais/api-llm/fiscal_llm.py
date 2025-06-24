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
from azure.storage.blob import BlobServiceClient, BlobClient

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

        # Configuração do Azure Blob Storage
        # Nome do container e do arquivo
        container_name = "agentenotasfiscais"
        blob_file_name = "df_resultado.parquet"

        # Recuperar string de conexão do Key Vault
        blob_connection_str = secret_client.get_secret("blobagente").value
        blob_service_client = BlobServiceClient.from_connection_string(blob_connection_str)
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_file_name)

        # Verifica se o DataFrame já está salvo no blob
        if blob_client.exists():
            logging.info("Lendo DataFrame do blob via URL...")

            # Construir URL pública ou com SAS
            blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_file_name}"
            df_resultado = pd.read_parquet(blob_url)
        else:
            logging.info("Arquivo não encontrado. Processando dados...")

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

            # Remove coluna "Valor nota fiscal"
            df_resultado.drop(columns=['VALOR NOTA FISCAL'], inplace=True)
        
            # Salvar DataFrame no Azure Blob Storage
            output_stream = BytesIO()
            df_resultado.to_parquet(output_stream, index=False)
            output_stream.seek(0)
            blob_client.upload_blob(output_stream, overwrite=True)
            logging.info("DataFrame salvo no Azure Blob Storage.")

            # URL para leitura posterior
            blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_file_name}"
            logging.info(f"DataFrame salvo. Pode ser acessado via URL: {blob_url}")
            df_resultado = pd.read_parquet(blob_url)

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
            "Pergunta: 'Quantos CNPJs distintos de emitentes existem?'\n"
            "1. Raciocínio: O CNPJ do emitente está associado à nota, e não ao item. Como há repetição por itens, apliquei drop_duplicates sobre a coluna “CHAVE DE ACESSO” para garantir contagem correta.\n"
            "2. Query: df.drop_duplicates(subset='CHAVE DE ACESSO')['CPF/CNPJ Emitente'].nunique()\n"
            "3. Resposta final: Existem 43 CNPJs distintos de emitentes cadastrados nas notas fiscais.\n\n"
            "Pergunta 2: 'Qual o produto mais vendido?'\n"
            "1. Raciocínio: Agrupei os dados por 'DESCRIÇÃO DO PRODUTO/SERVIÇO', somando a coluna 'QUANTIDADE'.\n"
            "2. Query: df.groupby('DESCRIÇÃO DO PRODUTO/SERVIÇO')['QUANTIDADE'].sum().sort_values(ascending=False).head(1)\n\n"
            "3. Resposta final: O produto mais vendido foi 'CIMENTO CP-II' com 1.245 unidades.\n\n"
            "Sempre responda em português e explique seu raciocínio com clareza antes de responder."
            "IMPORTANTE: Sempre que a pergunta envolver dados únicos por nota fiscal (CHAVE DE ACESSO, RAZÃO SOCIAL EMITENTE, CPF/CNPJ Emitente, UF EMITENTE, CNPJ DESTINATÁRIO, NOME DESTINATÁRIO, etc.), "
            "use df.drop_duplicates(subset='CHAVE DE ACESSO')"
            "Colunas como: DESCRIÇÃO DO PRODUTO/SERVIÇO, QUANTIDADE, VALOR UNITÁRIO, UNIDADE, etc. Devem ser analisadas no nível do item, ou seja, sem remover duplicações"
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
        1. Raciocínio:  explique como chegou à resposta.
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