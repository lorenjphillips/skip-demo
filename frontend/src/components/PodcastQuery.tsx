'use client';

import { useState, useRef, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2 } from 'lucide-react';
import Image from 'next/image';

interface Source {
  episode_id: string;
  title: string;
  timestamp?: string;
}

interface Message {
  type: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

const LoadingDots = () => (
  <div className="flex space-x-2 p-4 bg-slate-100 rounded-lg max-w-[80%]">
    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
  </div>
);

const PodcastQuery = () => {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    const userQuestion = question;
    setQuestion('');
    setLoading(true);

    setMessages(prev => [...prev, { type: 'user', content: userQuestion }]);
    
    try {
      const response = await fetch('http://localhost:8000/query', {
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4 absolute inset-0">
      <div className="max-w-4xl mx-auto flex flex-col h-[90vh]">
        <Card className="flex-1 flex flex-col mb-4 bg-white/95 backdrop-blur-sm shadow-xl">
          <CardHeader className="border-b flex flex-row justify-between items-center">
            <CardTitle>The Skip Podcast Interactive Search</CardTitle>
            <div className="relative w-12 h-12">
              <Image
                src="/skip-logo.png"
                alt="Skip Logo"
                fill
                style={{ objectFit: 'contain' }}
                priority
              />
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
                      className={`max-w-[80%] rounded-lg p-4 shadow-md transition-all duration-300 ease-in-out ${
                        message.type === 'user'
                          ? 'bg-purple-600 text-white ml-4'
                          : 'bg-slate-100 mr-4'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{message.content}</p>
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-2 text-sm opacity-80">
                          <p className="font-medium">Sources:</p>
                          <ul className="list-disc pl-4">
                            {message.sources.map((source, idx) => (
                              <li key={idx}>
                                {source.title}
                                {source.timestamp && ` - ${source.timestamp}`}
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