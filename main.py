import datetime
from typing import Union
import markdown
from fastapi import FastAPI, WebSocket
from simple_guided_rag import SimpleGuidedRag
app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.websocket("/ws0")
async def websocket_endpoint0(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        print(f"Received on {datetime.datetime.now().strftime("%H:%M:%S")} {data}.")
        await websocket.send_text(f"{data}")
        print(f"{data}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print(f"Connected to websocket")
    rag = SimpleGuidedRag()
    while True:
        data = await websocket.receive_text()
        print(f"Received at {datetime.datetime.now().strftime("%H:%M:%S")}: {data}.")
        response = markdown.markdown(rag.chat(data))
        await websocket.send_text(f"{response}")
        print(f"Sent at {datetime.datetime.now().strftime("%H:%M:%S")}:")
        print(f"{response}")
