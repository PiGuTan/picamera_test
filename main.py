import io
from datetime import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response,StreamingResponse
from pydantic import BaseModel
import picamera

app = FastAPI()

class Item(BaseModel):
    text: str = None
    is_done: bool = False


items = []


@app.get("/")
def root():
    return {"Hello": "World"}


@app.post("/items")
def create_item(item: Item):
    items.append(item)
    return items


@app.get("/items", response_model=list[Item])
def list_items(limit: int = 10):
    return items[0:limit]


@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int) -> Item:
    if item_id < len(items):
        return items[item_id]
    else:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

def generate_frames():
    with picamera.PiCamera() as camera:
        camera.resolution = (640, 480)
        camera.framerate = 30
        stream = io.BytesIO()

        for _ in camera.capture_continuous(stream, format="jpeg", use_video_port=True):
            stream.seek(0)
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + stream.read() + b'\r\n'
            stream.seek(0)
            stream.truncate()


@app.post("/feed")
def feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/image")
async def get_image():
    picam2 = picamera.PiCamera()
    # Configure for a 1080p still image
    capture_config = picam2.create_still_configuration(main={"size": (640, 480)})
    picam2.configure(capture_config)

    data = io.BytesIO()
    picam2.start()
    picam2.capture_file(data, format="jpeg")
    picam2.stop()
    picam2.close()  # Close the camera to release resources

    return Response(content=data.getvalue(), media_type="image/jpeg")