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

  const handleDismiss = () => {
    setUploadStatus(null);
    setUploadMessage(null);
    setShowDropzone(true);
  };

  const handleTimeUpdate = (event: React.SyntheticEvent<HTMLVideoElement>) => {
    const currentTime = event.currentTarget.currentTime;
    const currentFrame = Math.floor(currentTime * 30);
    const newMetadata = metadata[currentFrame] || "";

    if (newMetadata !== currentMetadata) {
      setCurrentMetadata(newMetadata);
      if (newMetadata !== "") {
        setMetadataLog((prevLog) => [
          ...prevLog,
          { timestamp: currentTime, data: newMetadata },
        ]);
      }
    }

    setCurrentTime(currentTime);
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

        try {
          setIsLoading(true);
          const response = await axios.get(`${API_URL}/video/${filename}`, {
            responseType: "blob",
          });
          setUploadedVideo(URL.createObjectURL(response.data));
          const metadataResponse = await axios.get(
            `${API_URL}/metadata/${filename}`,
          );
          setMetadata(metadataResponse.data);
          setUploadStatus("success");
          setUploadMessage("Video uploaded successfully!");
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
      </div>

      {showDropzone && (
        <div
          {...getRootProps()}
          className={`relative flex items-center justify-center p-4 text-white text-lg transition-colors ${
            isLoading
              ? ""
              : `border-4 ${
                  isDragActive
                    ? "border-dashed border-white bg-white/10"
                    : "border-white hover:border-gray-300 hover:bg-gray-800/30"
                }`
          }`}
        >
          <input {...getInputProps()} />
          {isLoading ? (
            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
              <BarLoader color="#ffffff" height={10} />
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
        <div className="mt-8">
          <video
            src={uploadedVideo}
            controls
            width="640"
            height="480"
            onTimeUpdate={handleTimeUpdate}
          />
          <div className="mt-4">
            <div className="bg-black shadow-md rounded-lg p-4 text-white">
              <div className="font-bold mb-2">Current Metadata</div>
              <div>{currentMetadata}</div>
              <div className="mt-4">
                <div className="font-bold mb-2">Metadata Log</div>
                <div className="max-h-64 overflow-y-auto">
                  {metadataLog.map((entry, index) => (
                    <div key={index} className="mb-2">
                      <div className="text-sm text-gray-300">
                        Timestamp: {formatTimestamp(entry.timestamp)}
                      </div>
                      <div>{entry.data}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
