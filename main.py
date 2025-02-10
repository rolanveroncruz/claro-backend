import datetime
from typing import Union
import markdown
from simple_guided_rag import SimpleGuidedRag
import json
from fastapi import FastAPI, WebSocket

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
        ###
        # stream_mode="updates" returns updates to the state made by the node.
        # stream_mode="messages" either taking too long, or hanging..?
        ###
        stream_mode = "messages"
        outputs = rag.chat(data, stream_mode)
        for output in outputs:
            # response = markdown.markdown(output)
            # await websocket.send_text(f"{response}")
            if stream_mode == "updates":
                if 'generate' in output.keys():
                    raw_answer = output['generate']['answer'].content
                    html_response = markdown.markdown(raw_answer)
                    await websocket.send_text(html_response)
                    print(f"{raw_answer}")
            elif stream_mode == "messages":
                raw_answer = output[0].content
                await websocket.send_text(raw_answer)
                print(f"{raw_answer}")


@app.websocket("/ws0")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")
