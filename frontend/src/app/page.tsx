"use client";
import Image from "next/image";
import { useState } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { BarLoader } from "react-spinners";
import { useDropzone } from "react-dropzone";
import Chat from "./chat";

const API_URL = "http://localhost:8080";

export default function Home() {
  const [uploadedVideo, setUploadedVideo] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState<"success" | "error" | null>(
    null,
  );

  const [wsMessages, setWsMessages] = useState<any[]>([]);

  const [fileaname, setFilename] = useState<string | null>(null);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [showDropzone, setShowDropzone] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [metadata, setMetadata] = useState<string[]>([]);
  const [currentMetadata, setCurrentMetadata] = useState<string>("");
  const [metadataLog, setMetadataLog] = useState<
    {
      timestamp: number;
      data: string;
    }[]
  >([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [frameRate, setFrameRate] = useState(30);
  const [searchString, setSearchString] = useState("");
  const [localization, setLocalization] = useState<string>("");
  const [localizationResponse, setLocalizationResponse] = useState<string>("");

  const handleDismiss = () => {
    setUploadStatus(null);
    setUploadMessage(null);
    setShowDropzone(true);
  };

  const handleTimeUpdate = (event: React.SyntheticEvent<HTMLVideoElement>) => {
    const currentTime = event.currentTarget.currentTime;
    const currentFrame = Math.floor(currentTime * 30);
    const newMetadata = metadata[currentFrame] || "";

    var canvas = document.querySelector("#canvas") as HTMLCanvasElement;
    var video = event.currentTarget as HTMLVideoElement;
    var ctx = canvas.getContext("2d");
    ctx?.drawImage(video, 0, 0, 720, 500);

    var matchingMessages = wsMessages.filter((message) =>
      currentFrame - message.frame_idx < 5 && currentFrame - message.frame_idx >= 0
    );
    for (const box of matchingMessages) {
      console.log("drawing bbox", box.bbox);
      var bbox = box.bbox;
      ctx?.beginPath();
      if (!bbox.fixed) {
        const originalWidth = video.videoWidth;

        bbox[0][0] = bbox[0][0] * 720 / originalWidth;
        bbox[0][1] = bbox[0][1] * 500 / video.videoHeight;
        bbox[1][0] = bbox[1][0] * 720 / originalWidth;
        bbox[1][1] = bbox[1][1] * 500 / video.videoHeight;
      }
      const w = bbox[1][0] - bbox[0][0];
      const h = bbox[1][1] - bbox[0][1];
      bbox.fixed = true;
      if (ctx) {
        ctx?.rect(bbox[0][0], bbox[0][1], w, h);
        ctx.strokeStyle = "red";
        ctx.lineWidth = 2;
        ctx?.stroke();
      }

    }

    setCurrentTime(currentTime);
  };
  const handleLoadedMetadata = (
    event: React.SyntheticEvent<HTMLVideoElement>,
  ) => {
    const video = event.currentTarget as HTMLVideoElement;
    const stream = video.captureStream();
    const videoTracks = stream.getVideoTracks();
    if (videoTracks.length > 0) {
      const frameRate = videoTracks[0].getSettings().frameRate || 30;
      setFrameRate(frameRate);
    }


    handleTimeUpdate(event);
  };

  const formatTimestamp = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds < 10 ? "0" : ""}${remainingSeconds}`;
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (file && file.name.endsWith(".mp4")) {
        const filename = file.name;
        setFilename(filename);

        try {
          setIsLoading(true);
          setWsMessages([]);
          const response = await axios.get(`${API_URL}/video?video_name=${filename}`, {
            responseType: "blob",
          });
          setUploadedVideo(URL.createObjectURL(response.data));
          const metadataResponse = await axios.get(
            `${API_URL}/metadata?video_name=${filename}`,
          );
          setMetadata(metadataResponse.data);
          const metadata = metadataResponse.data.map((data: string, index: number) => ({
            timestamp: index / (frameRate || 30),
            data,
          }));
          const filteredMetadata = metadata.filter(
            (data: any) => data.data !== "",
          );
          setMetadataLog(
            filteredMetadata
          );
          setUploadStatus(null);
          //setUploadMessage("Video uploaded successfully!");
          setShowDropzone(false);
        } catch (error) {
          setUploadStatus("error");
          setUploadMessage("Failed to upload video. Please try again.");
          setShowDropzone(false);
        } finally {
          setIsLoading(false);
        }
      } else {
        setUploadStatus("error");
        setUploadMessage("Unsupported file type. Please upload an MP4 video.");
      }
    },
    accept: {
      "video/mp4": [".mp4"],
    },
    maxSize: Infinity,
  });

  const search = () => {
    setWsMessages([]);
    const websocket = new WebSocket(`ws://localhost:8080/ws?target_video=${fileaname}&query=${searchString}`);
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log(data);
      setWsMessages((prevMessages) => [...prevMessages, data]);
    };
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24 bg-black text-white">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex">
        <div className="pointer-events-none flex place-items-center gap-2 p-8 text-2xl lg:pointer-events-auto lg:p-0">
          Overwatch{" "}
          <Image
            src="/overwatch.svg"
            alt="Overwatch Logo"
            className="dark:invert"
            width={32}
            height={32}
            priority
          />
        </div>
        {showDropzone && (
          <div
            {...getRootProps()}
            className={`relative flex items-center justify-center p-4 text-white text-lg transition-colors ${isLoading
              ? ""
              : `border-4 ${isDragActive
                ? "border-dashed border-white bg-white/10"
                : "border-white hover:border-gray-300 hover:bg-gray-800/30"
              }`
              }`}
          >
            <input {...getInputProps()} />
            {isLoading ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-black bg-opacity-50">
                <div>
                  <BarLoader color="#ffffff" height={10} />
                </div>
                <p className="mt-4">Analyzing video...</p>
              </div>
            ) : isDragActive ? (
              <p>Drop the drone footage here...</p>
            ) : (
              <span className="inline-flex items-center">
                Upload drone footage
                <Image
                  src="/right_arrow.svg"
                  alt="Right Arrow"
                  width={24}
                  height={24}
                  priority
                  className="ml-2 transition-transform group-hover:translate-x-1 motion-reduce:transform-none"
                />
              </span>
            )}
          </div>
        )}
      </div>



      {uploadStatus && (
        <Alert
          className="max-w-xl"
          variant={uploadStatus === "success" ? "success" : "destructive"}
        >
          <AlertTitle>
            {uploadStatus === "success" ? "Upload Success" : "Upload Error"}
          </AlertTitle>
          <AlertDescription>{uploadMessage}</AlertDescription>
          <div className="mt-4">
            <Button
              variant="outline"
              className="text-black"
              onClick={handleDismiss}
            >
              Dismiss
            </Button>
          </div>
        </Alert>
      )}

      {uploadedVideo && (
        <div className="mt-8 grid grid-cols-2 w-full">
          <div className="videos flex flex-col gap-y-4">
            <video
              src={uploadedVideo}
              controls
              width="720"
              height="500"
              onTimeUpdate={handleTimeUpdate}
              onLoadedMetadata={handleLoadedMetadata}
            />
            <canvas id="canvas" width="720" height="500" />
          </div>

          <div className="mt-4">
            <div className="bg-black shadow-md rounded-lg p-4 text-white">
              <div className="flex flex-col gap-y-2">
                <div className="flex flex-row gap-x-2">

                  <input type="text" value={searchString} onChange={(e) => setSearchString(e.target.value)} placeholder="Search video..." className="w-full p-2 bg-black border-b border-white focus:outline-none focus:border-gray-300" />
                  <button onClick={search}>Search </button>
                </div>
                {wsMessages?.length > 0 && <div className="font-bold">Search Results</div>}
                {
                  wsMessages.map((message, index) => {
                    if (index > 0 && (message.frame_idx - wsMessages[index - 1].frame_idx <= 10)) {
                      return null
                    } else return (
                      <div key={index} className="flex flex-row gap-x-2 content-center">
                        <div onClick={() => {
                          const video = document.querySelector("video") as HTMLVideoElement;
                          video.currentTime = message.frame_idx / frameRate;
                          video.play();
                        }} className="border p-1 hover:border-rose-500">{message.label}</div>
                        <div className="p-1">Start frame: {message.frame_idx}</div>
                      </div>
                    )
                  })
                }


                {currentMetadata && <><div className="font-bold mb-2">Current Metadata</div>
                  <div>{currentMetadata}</div></>}
                <div className="mt-4">
                  <div className="font-bold mb-2">Metadata Log</div>
                  <div
                    className="max-h-64 overflow-y-auto"
                  /* ref={(el) => el?.scrollIntoView({ behavior: "smooth" })} */
                  >
                    {metadataLog.map((entry, index) => (
                      <div key={index} className="mb-2 border p-2 rounded-md hover:border-rose-500 z-50" onClick={
                        () => {
                          const video = document.querySelector("video") as HTMLVideoElement;
                          video.currentTime = entry.timestamp;
                          video.play();
                        }

                      }>
                        <div className="text-sm text-gray-300">
                          Timestamp: {formatTimestamp(entry.timestamp)}
                        </div>
                        <div>{entry.data}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="localization mt-12">
                <input type="text" value={localization} onChange={(e) => setLocalization(e.target.value)} placeholder="Localization..." className="w-full p-2 bg-black border-b border-white focus:outline-none focus:border-gray-300" />
                <button onClick={async () => {
                  // make request to https://252c-4-78-254-114.ngrok-free.app/heatmap?center={localization} and current frame of video as file
                  const video = document.querySelector("video") as HTMLVideoElement;
                  const canvas = document.querySelector("#canvas") as HTMLCanvasElement;
                  const dataUrl = canvas.toDataURL();
                  const blob = await fetch(dataUrl).then((res) => res.blob());
                  const formData = new FormData();
                  formData.append("file", blob, "frame.png");
                  const response = await axios.post(`https://b887-12-94-170-82.ngrok-free.app/heatmap?center=${localization}`, formData, {
                    headers: {
                      "Content-Type": "multipart/form-data"
                    }
                  }
                  );
                  const data = response.data;
                  setLocalizationResponse(data);
                }}>Localize</button>
                {localizationResponse && <div className="mt-4">
                  <img src={localizationResponse} />
                </div>}
              </div>

            </div>
          </div>
        </div>
      )}
    </main>
  );
}
