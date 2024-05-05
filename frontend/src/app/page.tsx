"use client";
import Image from "next/image";
import { useState } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useDropzone } from "react-dropzone";

const API_URL = "http://localhost:8080";

export default function Home() {
  const [uploadedVideo, setUploadedVideo] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState<"success" | "error" | null>(
    null,
  );
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [showDropzone, setShowDropzone] = useState(true);

  const handleDismiss = () => {
    setUploadStatus(null);
    setUploadMessage(null);
    setShowDropzone(true);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (file && file.name.endsWith(".mp4")) {
        const formData = new FormData();
        formData.append("file", file);

        try {
          const response = await axios.post(
            `${API_URL}/drone_footage`,
            formData,
          );
          setUploadedVideo(response.data.file_response.url);
          setUploadStatus("success");
          setUploadMessage("Video uploaded successfully!");
        } catch (error) {
          console.error("Error uploading video:", error);
          setUploadStatus("error");
          setUploadMessage("Failed to upload video. Please try again.");
          setShowDropzone(false);
        }
      } else {
        console.log("File type not supported");
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
          className={`relative flex items-center justify-center p-4 border-4 text-white text-lg transition-colors ${
            isDragActive
              ? "border-dashed border-white bg-white/10"
              : "border-white hover:border-gray-300 hover:bg-gray-800/30"
          }`}
        >
          <input {...getInputProps()} />
          {isDragActive ? (
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
            <Button variant="outline" onClick={handleDismiss}>
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
          />
        </div>
      )}

      <div className="mb-32 grid text-center lg:mb-0 lg:w-full lg:max-w-5xl lg:grid-cols-2 lg:text-left">
        <a
          href="https://nextjs.org/docs?utm_source=create-next-app&utm_medium=appdir-template&utm_campaign=create-next-app"
          className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 hover:dark:border-neutral-700 hover:dark:bg-neutral-800/30"
          target="_blank"
          rel="noopener noreferrer"
        >
          <h2 className="mb-3 text-2xl font-semibold">Heatmap </h2>
          <p className="m-0 max-w-[30ch] text-sm opacity-50">
            Find in-depth information about Next.js features and API.
          </p>
        </a>

        <a
          href="https://vercel.com/new?utm_source=create-next-app&utm_medium=appdir-template&utm_campaign=create-next-app"
          className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 hover:dark:border-neutral-700 hover:dark:bg-neutral-800/30"
          target="_blank"
          rel="noopener noreferrer"
        >
          <h2 className="mb-3 text-2xl font-semibold">
            Q&A{" "}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className="m-0 max-w-[30ch] text-balance text-sm opacity-50">
            Ask us anything!
          </p>
        </a>
      </div>
    </main>
  );
}
