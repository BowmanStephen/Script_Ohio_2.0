import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import { Loader2, Send, Bot, User, Sparkles, BarChart3, Trophy, TrendingUp } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  intent?: string;
  confidence?: number;
  suggestions?: string[];
}

interface AIAssistantProps {
  className?: string;
  onAnalysisRequest?: (query: string) => void;
  onPredictionRequest?: (query: string) => void;
}

const intentIcons = {
  general_chat: Bot,
  data_analysis: BarChart3,
  predictions: Trophy,
  task_automation: Sparkles,
  learning_guidance: TrendingUp,
};

const intentColors = {
  general_chat: 'bg-blue-100 text-blue-800',
  data_analysis: 'bg-green-100 text-green-800',
  predictions: 'bg-orange-100 text-orange-800',
  task_automation: 'bg-purple-100 text-purple-800',
  learning_guidance: 'bg-indigo-100 text-indigo-800',
};

export function AIAssistant({ className, onAnalysisRequest, onPredictionRequest }: AIAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize session on mount
  useEffect(() => {
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);

    // Add welcome message
    const welcomeMessage: Message = {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm your AI assistant for college football analytics. I can help you with data analysis, predictions, task automation, and learning guidance. What would you like to explore today?",
      timestamp: new Date().toISOString(),
      intent: 'general_chat',
      confidence: 1.0,
      suggestions: [
        "Analyze Ohio State's performance this season",
        "Predict the Ohio State vs Michigan game",
        "Compare top 25 team statistics",
        "Explain how prediction models work"
      ]
    };
    setMessages([welcomeMessage]);
  }, []);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Call AI Assistant API
      const response = await fetch('/api/ai-assistant/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: sessionId,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        const assistantMessage: Message = {
          id: `assistant_${Date.now()}`,
          role: 'assistant',
          content: data.response,
          timestamp: new Date().toISOString(),
          intent: data.intent,
          confidence: data.confidence,
          suggestions: data.suggestions || [],
        };

        setMessages(prev => [...prev, assistantMessage]);

        // Trigger callbacks for specific intents
        if (data.intent === 'data_analysis' && onAnalysisRequest) {
          onAnalysisRequest(userMessage.content);
        } else if (data.intent === 'predictions' && onPredictionRequest) {
          onPredictionRequest(userMessage.content);
        }
      } else {
        throw new Error(data.error || 'Failed to get response from AI Assistant');
      }
    } catch (error) {
      const errorMessage: Message = {
        id: `error_${Date.now()}`,
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearConversation = () => {
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: "Conversation cleared! How can I help you today?",
      timestamp: new Date().toISOString(),
      intent: 'general_chat',
      confidence: 1.0,
    }]);
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Card className={`h-[600px] flex flex-col ${className}`}>
      <CardHeader className="flex-shrink-0 pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Bot className="h-5 w-5 text-blue-600" />
            <CardTitle className="text-lg">AI Assistant</CardTitle>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={clearConversation}
            className="text-xs"
          >
            Clear
          </Button>
        </div>
        <CardDescription>
          Ask me anything about college football analytics, predictions, and data analysis
        </CardDescription>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-4 pt-0">
        <ScrollArea className="flex-1 pr-4">
          <div className="space-y-4">
            {messages.map((message) => {
              const IntentIcon = message.intent ? intentIcons[message.intent as keyof typeof intentIcons] : Bot;
              const intentColor = message.intent ? intentColors[message.intent as keyof typeof intentColors] : 'bg-gray-100 text-gray-800';

              return (
                <div
                  key={message.id}
                  className={`flex ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-3 py-2 ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      <div className="flex-shrink-0 mt-0.5">
                        {message.role === 'user' ? (
                          <User className="h-4 w-4" />
                        ) : (
                          <IntentIcon className="h-4 w-4" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm whitespace-pre-wrap break-words">
                          {message.content}
                        </p>

                        {message.role === 'assistant' && (
                          <div className="mt-2 space-y-2">
                            {message.intent && (
                              <div className="flex items-center space-x-2">
                                <Badge className={`text-xs ${intentColor}`}>
                                  {message.intent.replace('_', ' ')}
                                </Badge>
                                {message.confidence && (
                                  <span className="text-xs text-gray-500">
                                    {Math.round(message.confidence * 100)}% confidence
                                  </span>
                                )}
                              </div>
                            )}

                            {message.suggestions && message.suggestions.length > 0 && (
                              <div className="space-y-1">
                                <p className="text-xs font-medium text-gray-600">Suggestions:</p>
                                <div className="flex flex-wrap gap-1">
                                  {message.suggestions.map((suggestion, index) => (
                                    <Button
                                      key={index}
                                      variant="ghost"
                                      size="sm"
                                      className="h-6 px-2 text-xs bg-white/80 hover:bg-white text-gray-700 border border-gray-200"
                                      onClick={() => handleSuggestionClick(suggestion)}
                                    >
                                      {suggestion}
                                    </Button>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}

                        <div className="mt-1 text-xs opacity-70">
                          {formatTime(message.timestamp)}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}

            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-lg px-3 py-2 bg-gray-100 text-gray-900">
                  <div className="flex items-center space-x-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        <Separator className="my-3" />

        <div className="flex space-x-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about college football..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            size="icon"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>

        <div className="mt-2 text-xs text-gray-500 text-center">
          Session: {sessionId.slice(-8)}
        </div>
      </CardContent>
    </Card>
  );
}