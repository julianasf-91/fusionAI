import azure.functions as func
import logging
from fiscal_llm import fiscal_llm

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
app.register_functions(fiscal_llm)

@app.route(route="appapi")
def appapi(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )