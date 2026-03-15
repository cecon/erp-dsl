---
description: Guia e melhores práticas para integração e exposição de Remote MCP Servers através do framework FastAPI e do SDK fastapi-mcp
---

# FastAPI MCP Integration (fastapi-mcp)

Este documento centraliza as melhores práticas descobertas ao implementar rotas do FastAPI como ferramentas MCP (Model Context Protocol), servindo como Remote MCP para o Claude. 
Ao usar o pacote `fastapi-mcp` para criar o servidor (seja em modo SSE ou Streamable HTTP), certos padrões internos do FastAPI podem quebrar a comunicação.

Essas regras são obrigatórias quando adicionar ou modificar ferramentas ("tools") e componentes ASGI relacionados ao MCP.

## Regra 1: Middlewares e SSE (Server-Sent Events)

O modo de transporte oficial recomendado do Claude Web/Desktop para servidores MCP HTTP é o fluxo de eventos **SSE (Server-Sent Events) via o método `.mount("/mcp")`** do SDK `fastapi-mcp`. 
O SSE mantém uma conexão de streaming assíncrona viva. 

### O Problema do `BaseHTTPMiddleware`
Se a aplicação FastAPI contiver Middlewares baseados em `@app.middleware("http")` (que por trás dos panos usam `BaseHTTPMiddleware` do Starlette), um bug interno de iteradores da ASGI fará com que qualquer resposta de `StreamingResponse` termine em um erro abrupto (`AssertionError` de `message["type"] == "http.response.body"`). Isso desconecta e inviabiliza conexões com o MCP via Claude.

### A Solução
Para garantir o fluxo adequado do SSE (e de rotas WebSockets), **todos os middlewares que interceptem requisições para a rota MCP devem ser escritos no padrão "ASGI puro"**, lidando diretamente com `scope`, `receive`, e `send`.

✅ Forma Correta:
```python
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

class PurifiedASGIMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope, receive=receive, send=send)
        
        # OBRIGATÓRIO: Bypass para a sub-rota do FastMCP que recebe as tools (POST)
        # O Claude Web só envia a api_key no Handshake SSE inicial. As chamadas seguintes
        # para enviar a pergunta vêm num POST que possui apenas "session_id", logo seriam barradas.
        path = scope.get("path", "")
        if request.method == "POST" and path.startswith("/mcp/messages"):
            return await self.app(scope, receive, send)
        
        # Validação do Auth (Header ou Query String)
        raw_token = request.headers.get("X-API-Key", "") or request.query_params.get("api_key")
        if not raw_token:
             response = JSONResponse(status_code=401, content={"error": "Unauthorized"})
             return await response(scope, receive, send)
             
        # Se válido: continua pipeline original sem quebrar o stream
        return await self.app(scope, receive, send)

# Na sua factory FastAPI:
app.add_middleware(PurifiedASGIMiddleware)
```

## Regra 2: Explicitando o Schema de Objetos no `Body`

O `fastapi-mcp` usa o JSON Schema do OpenAPI (gerado nativamente pelo FastAPI) para construir a representação de argumentos estritos requeridos pelo MCP (que o LLM usará). 

### O Problema do `dict[str, Any]` livre
Muitas rotas genéricas em Python declaram o payload apenas como type hint `body: dict[str, Any]`. O FastAPI não constrói chaves e validações rigorosas sob esse tipo no OpenAPI (deixando-o vazio ou omisso). No `fastapi-mcp`, ele converte esse campo em um parâmetro desprovido de chaves — e na ponta do Claude, isso se manifesta como uma recusa de Tool. O Claude reclamará que o payload (ex: "body") não contem propriedades para preencher.

### A Solução
Tratar a declaração como um `Body(...)` livre do Pydantic, com descrição associada.

✅ Forma Correta:
```python
from typing import Any
from fastapi import Body, APIRouter

router = APIRouter()

@router.post("/entidades/{name}")
def create_entity(
    name: str,
    body: dict[str, Any] = Body(
        ...,
        description="Campos JSON obrigatórios vindos da ferramenta."
    )
):
    # Processa os argumentos
    return {"message": "success"}
```

Dessa forma, o FastAPI expõe um content-type de `application/json` restrito e mapeando `body` como raiz requerida perante a documentação — o `fastapi-mcp` traduz isso em um input explícito do Tool.

## Contextualização e Fallbacks
Em custom-connectors do tipo *Remote MCP* para Claude Web, a Query String `?api_key=...` é comumente preenchida pelo Claude na URL do SSE (como *Connection URL*). O endpoint do FastApiMCP gera a URL de `/messages` em cima desse initial-request ASGI. Por isso o `request.query_params.get('api_key')` é essencial na lógica do Middleware Puro (citado na Regra 1) se houver auth.
