'use client';

import { useState, useRef, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, ExternalLink, Copy, Check, Trash2 } from 'lucide-react';
import Image from 'next/image';
import InteractiveBackground from './InteractiveBackground';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface Source {
  episode_id: string;
  title: string;
  url: string;
}

interface Message {
  type: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}


const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';




const LoadingDots = () => (
  <div className="flex space-x-2 p-4 bg-slate-100 rounded-lg max-w-[80%]">
    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
  </div>
);

const VideoDialog = ({ url, title }: { url: string; title: string }) => {
  const getYouTubeEmbedUrl = (url: string) => {
    const videoId = url.split('v=')[1]?.split('&')[0];
    return `https://www.youtube.com/embed/${videoId}`;
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="link" className="p-0 h-auto font-normal hover:no-underline flex items-center gap-1 text-purple-600">
          {title} <ExternalLink className="h-3 w-3" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl w-full">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <div className="aspect-video w-full">
          <iframe
            width="100%"
            height="100%"
            src={getYouTubeEmbedUrl(url)}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            className="rounded-lg"
          />
        </div>
      </DialogContent>
    </Dialog>
  );
};

// MessageActions component
const MessageActions = ({ content, onCopy }: { content: string; onCopy: () => void }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    // Use the content prop here
    navigator.clipboard.writeText(content).then(() => {
      onCopy();
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute top-2 right-2 flex gap-2">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={handleCopy}
            >
              {copied ? (
                <Check className="h-4 w-4 text-green-500" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Copy message</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  );
};

const PodcastQuery = () => {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [isClient, setIsClient] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Handle hydration safely
  useEffect(() => {
    setIsClient(true);
    const savedMessages = localStorage.getItem('chatMessages');
    if (savedMessages) {
      setMessages(JSON.parse(savedMessages));
    }
  }, []);

  // Save messages to localStorage
  useEffect(() => {
    if (isClient && messages.length > 0) {
      localStorage.setItem('chatMessages', JSON.stringify(messages));
    }
  }, [messages, isClient]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleCopyMessage = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      // Add toast notification here when you implement it
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

  const clearHistory = () => {
    setMessages([]);
    if (isClient) {
      localStorage.removeItem('chatMessages');
    }
    // Add toast notification here when you implement it
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
  
    const userQuestion = question;
    setQuestion('');
    setLoading(true);
  
    setMessages(prev => [...prev, { type: 'user', content: userQuestion }]);
    
    try {
      console.log('Making request to:', API_URL);
      const response = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: userQuestion }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch response');
      }
      
      const data = await response.json();
      console.log('Response:', data);
      
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: data.answer,
        sources: data.sources
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: error instanceof Error ? error.message : 'Failed to fetch response'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative">
      <InteractiveBackground />
    <div className="relative z-10 p-4"></div>
      <div className="max-w-4xl mx-auto flex flex-col h-[90vh]">
        <Card className="flex-1 flex flex-col mb-4 bg-white/95 backdrop-blur-sm shadow-xl">
          <CardHeader className="border-b flex flex-row justify-between items-center">
            <div className="flex items-center justify-between w-full">
              <CardTitle>The Skip Podcast Interactive Search</CardTitle>
              <div className="flex items-center gap-4">
                {isClient && messages.length > 0 && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={clearHistory}
                          className="h-8 w-8"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Clear chat history</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
                <div className="relative w-12 h-12">
                  {isClient && (
                    <Image
                      src="/skip-logo.png"
                      alt="Skip Logo"
                      fill
                      style={{ objectFit: 'contain' }}
                      priority
                    />
                  )}
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col pt-4">
            <ScrollArea className="flex-1 pr-4 mb-4">
              <div className="space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`relative group max-w-[80%] rounded-lg p-4 shadow-md transition-all duration-300 ease-in-out ${
                      message.type === 'user'
                        ? 'bg-purple-600 text-white ml-4'
                        : 'bg-slate-100 mr-4'
                    }`}
                  >
                    {isClient && (
                      <MessageActions 
                        content={message.content}
                        onCopy={() => handleCopyMessage(message.content)}
                      />
                    )}
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-2 text-sm opacity-80">
                        <p className="font-medium">Sources:</p>
                        <ul className="list-disc pl-4">
                          {message.sources.map((source, idx) => (
                            <li key={idx}>
                              <VideoDialog url={source.url} title={source.title} />
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))}
                {loading && (
                  <div className="flex justify-start">
                    <LoadingDots />
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>
            <div className="border-t pt-4">
              <form onSubmit={handleSubmit} className="flex gap-2">
                <Input
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask about the podcast..."
                  className="flex-1"
                  disabled={loading}
                />
                <Button 
                  type="submit" 
                  disabled={loading}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Ask'}
                </Button>
              </form>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default PodcastQuery;