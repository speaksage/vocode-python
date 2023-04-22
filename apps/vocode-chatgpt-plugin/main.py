from dotenv import load_dotenv

load_dotenv()

import logging
from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from vocode.streaming.telephony.server.base import TelephonyServer
from vocode.streaming.telephony.config_manager.in_memory_config_manager import (
    InMemoryConfigManager,
)
from vocode.streaming.telephony.conversation.outbound_call import OutboundCall
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage


app = FastAPI(docs_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chat.openai.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

config_manager = InMemoryConfigManager()

BASE_URL = "d0c256b11fe8.ngrok.app"

telephony_server = TelephonyServer(
    base_url=BASE_URL,
    config_manager=config_manager,
    logger=logger,
)

app.include_router(telephony_server.get_router())


class CreateOutboundCall(BaseModel):
    recipient_number: str
    gpt_prompt: str = ""
    initial_message: str


@app.post("/call")
async def outbound_call(request: CreateOutboundCall):
    call = OutboundCall(
        base_url=BASE_URL,
        to_phone=request.recipient_number,
        from_phone="+16507299536",
        config_manager=config_manager,
        agent_config=ChatGPTAgentConfig(
            prompt_preamble=request.gpt_prompt,
            end_conversation_on_goodbye=True,
            initial_message=BaseMessage(text=request.initial_message),
        ),
        logger=logging.Logger("call_phone_number"),
    )
    call.start()
    return "OK"


@app.get("/logo.png")
async def plugin_logo():
    filename = "logo.png"
    return FileResponse(filename, media_type="image/png")


@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    with open("./.well-known/ai-plugin.json") as f:
        text = f.read()
        return Response(text, media_type="text/json")


@app.get("/openapi.yaml")
async def openapi_spec(request: Request):
    host = request.headers["Host"]
    with open("openapi.yaml") as f:
        text = f.read()
        return Response(text, media_type="text/yaml")