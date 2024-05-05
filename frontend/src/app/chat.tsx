"use client";
import { useState, useEffect } from "react";
import axios from "axios";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

const API_URL = "http://localhost:8080";

interface Message {
  role: "user" | "ai";
  content: string;
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");

  useEffect(() => {
    const socket = new WebSocket(`ws://${API_URL}/chat`);

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages((prevMessages) => [
        ...prevMessages,
        { role: "ai", content: data.message },
      ]);
    };

    return () => {
      socket.close();
    };
  }, []);

  const sendMessage = () => {
    if (input.trim() !== "") {
      setMessages((prevMessages) => [
        ...prevMessages,
        { role: "user", content: input },
      ]);
      axios.post(`${API_URL}/chat`, { message: input });
      setInput("");
    }
  };

  return (
    <Card>
      <CardContent>
        <div className="h-64 overflow-y-auto">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`mb-2 ${message.role === "user" ? "text-right" : ""}`}
            >
              <span
                className={
                  message.role === "user" ? "text-blue-500" : "text-green-500"
                }
              >
                {message.role === "user" ? "You" : "AI"}:
              </span>{" "}
              {message.content}
            </div>
          ))}
        </div>
        <div className="mt-4 flex">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-grow"
          />
          <Button onClick={sendMessage} className="ml-2">
            Send
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
