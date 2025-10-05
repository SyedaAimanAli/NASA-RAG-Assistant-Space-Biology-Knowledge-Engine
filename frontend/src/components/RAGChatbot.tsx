import { useState, useRef, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { DocumentPanel } from "./DocumentPanel";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PanelLeftOpen, PanelLeftClose, BarChart3, FileText, X } from "lucide-react";
import nasaHero from "@/assets/nasa-hero.jpg";

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

interface Document {
  id: string;
  title: string;
  score: number;
  snippet?: string;
  url?: string;
}

interface ApiResponse {
  answer: string;
  docs?: Document[];
  chart?: string;
}

export function RAGChatbot() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      content:
        "Hello! I'm your NASA RAG Assistant. Ask me anything about space missions, research, or NASA projects.",
      isUser: false,
      timestamp: new Date(),
    },
  ]);

  const [documents, setDocuments] = useState<Document[]>([]);
  const [chartUrl, setChartUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [activePanel, setActivePanel] = useState<"documents" | "chart">("documents");
  const [showChartModal, setShowChartModal] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // === SEND MESSAGE ===
  const handleSendMessage = async (message: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content: message,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: message }),
      });

      if (!response.ok) throw new Error(`Backend error (${response.status})`);

      const data: ApiResponse = await response.json();

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.answer || "No response received from backend.",
        isUser: false,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, aiMessage]);
      setDocuments(data.docs || []);
      setChartUrl(data.chart || null);

      if ((data.docs && data.docs.length > 0) || data.chart) {
        setShowSidebar(true);
      }

      toast({
        title: "Response received",
        description: "NASA RAG Assistant processed your question successfully.",
      });
    } catch (error) {
      console.error("Error fetching response:", error);
      toast({
        title: "Connection Error",
        description:
          "Could not reach the backend. Please make sure your FastAPI server is running.",
        variant: "destructive",
      });

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          content:
            "⚠️ Unable to connect to the backend. Please check your FastAPI server or network connection.",
          isUser: false,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <div className="border-b bg-card shadow-sm">
        <div className="flex items-center justify-between p-3 md:p-4">
          <div className="flex items-center gap-2 md:gap-3">
            <img
              src={nasaHero}
              alt="NASA"
              className="h-6 w-8 md:h-8 md:w-12 object-cover rounded"
            />
            <h1 className="text-lg md:text-xl font-semibold text-foreground">
              NASA RAG Assistant
            </h1>
          </div>

          <div className="flex items-center gap-1 md:gap-2">
            {/* Panel Toggles */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setActivePanel("documents");
                setShowSidebar(true);
              }}
              className={`${
                activePanel === "documents" ? "bg-primary text-primary-foreground" : ""
              } hidden md:flex`}
            >
              <FileText className="h-4 w-4 mr-1" /> Docs
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setActivePanel("chart");
                setShowSidebar(true);
              }}
              className={`${
                activePanel === "chart" ? "bg-primary text-primary-foreground" : ""
              } hidden md:flex`}
            >
              <BarChart3 className="h-4 w-4 mr-1" /> Studies
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowSidebar(!showSidebar)}
            >
              {showSidebar ? (
                <PanelLeftClose className="h-4 w-4" />
              ) : (
                <PanelLeftOpen className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Main Layout */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Chat Section */}
        <div className="flex-1 flex flex-col min-h-0">
          <ScrollArea className="flex-1 p-3 md:p-4" ref={scrollRef}>
            <div className="w-full max-w-4xl mx-auto space-y-4">
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg.content}
                  isUser={msg.isUser}
                  timestamp={msg.timestamp}
                />
              ))}
            </div>
          </ScrollArea>
          <div className="shrink-0">
            <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
          </div>
        </div>

        {/* Sidebar */}
        {showSidebar && (
          <div className="hidden md:flex w-full md:w-80 lg:w-96 border-l bg-card flex-col items-center justify-center p-4">
            {activePanel === "documents" ? (
              <div className="w-full space-y-2">
                {documents.length > 0 ? (
                  documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="border rounded-lg p-3 hover:bg-muted transition-colors"
                    >
                      <h3 className="font-semibold text-sm">
                        {doc.url ? (
                          <a
                            href={doc.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            {doc.title}
                          </a>
                        ) : (
                          doc.title
                        )}
                      </h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        {doc.snippet}
                      </p>
                      <p className="text-[10px] mt-1 text-muted-foreground">
                        Relevance Score: {doc.score}
                      </p>
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground text-sm text-center">
                    No related documents.
                  </p>
                )}
              </div>
            ) : chartUrl ? (
              <img
                src={chartUrl}
                alt="Relevance Chart"
                className="rounded-lg shadow-md max-w-full cursor-pointer"
                onClick={() => setShowChartModal(true)}
              />
            ) : (
              <p className="text-muted-foreground text-sm">No chart available.</p>
            )}
          </div>
        )}
      </div>

      {/* === Chart Modal (click to enlarge) === */}
      {showChartModal && (
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50"
          onClick={() => setShowChartModal(false)}
        >
          <div className="relative bg-card p-4 rounded-lg max-w-4xl max-h-[90vh] overflow-auto">
            <Button
              variant="ghost"
              size="icon"
              className="absolute top-2 right-2 text-white"
              onClick={() => setShowChartModal(false)}
            >
              <X className="h-5 w-5" />
            </Button>
            <img
              src={chartUrl || ""}
              alt="Enlarged Chart"
              className="rounded-lg w-full h-auto"
            />
          </div>
        </div>
      )}
    </div>
  );
}
