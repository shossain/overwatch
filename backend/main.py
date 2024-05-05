import json
import os
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

FILE_PATH = "files"
app = FastAPI()

class VideoMetadata(BaseModel):
    json_data: dict

@app.post("/drone_footage", response_model=VideoMetadata)
async def upload_drone_footage(file: UploadFile) -> tuple[FileResponse, VideoMetadata]:
    if file.filename and file.filename.endswith(".mp4"):
        file_path = os.path.join(str(FILE_PATH), str(file.filename))
        if os.path.exists(path=file_path):
            processed_folder = file.filename.split('.')[0]
            processed_video_path = os.path.join(FILE_PATH, processed_folder, file.filename)
            json_file_path = os.path.join(FILE_PATH, processed_folder, f"{file.filename.split('.')[0]}.json")
            
            if os.path.exists(processed_video_path) and os.path.exists(json_file_path):
                with open(json_file_path, "r") as json_file:
                    json_data = json.load(json_file)
                
                return FileResponse(processed_video_path), VideoMetadata(json_data=json_data)
            else:
                raise HTTPException(status_code=404, detail="Processed video and metadata not found.")
        else:
            raise HTTPException(status_code=404, detail="Uploaded file not found.")
    else:
        raise HTTPException(status_code=400, detail="Invalid file format. Only MP4 files are allowed.")
            
@app.post("/grounding_dino")
async def run_grounding_dino(query: str):


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

