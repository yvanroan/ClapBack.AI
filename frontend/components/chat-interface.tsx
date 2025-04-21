'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Mic, Send, Sparkles } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { motion } from '@/lib/motion';
import { ScenarioData } from '@/lib/types';
import { useToast } from '@/hooks/use-toast';
import { ChatMessage } from '@/lib/types';

// Generate a random avatar for the AI character
const avatarOptions = [
  'https://images.pexels.com/photos/1674752/pexels-photo-1674752.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/2726111/pexels-photo-2726111.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/1681010/pexels-photo-1681010.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/614810/pexels-photo-614810.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
];

const getInitials = (name: string) => {
  return name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase();
};

interface ChatInterfaceProps {
  scenarioData: ScenarioData;
  onMessageLimit: () => void;
  isLoading: boolean;
}

export function ChatInterface({ 
  scenarioData, 
  onMessageLimit,
  isLoading 
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const aiAvatar = avatarOptions[Math.floor(Math.random() * avatarOptions.length)];

  // Generate character name from archetype
  const characterName = scenarioData.system_archetype
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');

  useEffect(() => {
    // Generate first message based on scenario
    const generateFirstMessage = () => {
      setIsTyping(true);
      
      // Examples based on conversation type
      const firstMessages: Record<string, string[]> = {
        dating: [
          "Hey there! I noticed you from across the room. What brings you here tonight?",
          "Hi! I don't think we've met before. I'm loving the vibe here, aren't you?",
          "Well hello! Mind if I join you? This place is packed tonight."
        ],
        interview: [
          "Thanks for coming in today. I've looked over your resume, and I'm impressed. Tell me more about yourself.",
          "Welcome! We're excited to learn more about you today. What made you interested in this position?",
          "Good to meet you! Let's start by discussing your background and why you think you're a good fit for our team."
        ],
        negotiation: [
          "I've reviewed your proposal. There are some points I'd like to discuss further.",
          "Thanks for meeting with me today. I'm interested in hearing more about your terms.",
          "I'm glad we could set up this meeting. I have some thoughts on how we can make this work for both of us."
        ],
        friendship: [
          "Hey, I'm new to the area. Any cool spots you recommend checking out?",
          "So how do you know everyone here? I came with my roommate but they disappeared!",
          "This class/event is something else, huh? Have you been to one before?"
        ],
        networking: [
          "I noticed you work in the same industry. What's your role exactly?",
          "Great to meet someone new at this event! What brings you here today?",
          "I'm always interested in connecting with people in this field. What's your background?"
        ]
      };

      // Default messages if type not found
      const defaultMessages = [
        "Hey there! Nice to meet you. How are you doing?",
        "Hi! I'm glad we have a chance to chat. What's on your mind?",
        "Hello! Great to connect with you. What should we talk about?"
      ];

      // Choose a random message from the appropriate category or default
      const messageOptions = firstMessages[scenarioData.type] || defaultMessages;
      const selectedMessage = messageOptions[Math.floor(Math.random() * messageOptions.length)];
      
      // Simulate typing delay
      setTimeout(() => {
        setMessages([
          {
            id: Date.now().toString(),
            text: selectedMessage,
            sender: 'system',
            timestamp: new Date().toISOString()
          }
        ]);
        setIsTyping(false);
      }, 1500);
    };

    generateFirstMessage();
    // Focus input after first message appears
    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }, 2000);
  }, [scenarioData.type]);

  useEffect(() => {
    // Scroll to bottom when new messages arrive
    scrollToBottom();
  }, [messages, isTyping]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
    
    // Check if we've reached the message limit (9 messages from user = 10 total exchanges)
    const userMessages = messages.filter(m => m.sender === 'user');
    if (userMessages.length >= 9) {
      toast({
        title: "Message limit reached",
        description: "We're analyzing your conversation now...",
      });
      onMessageLimit();
      return;
    }

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      text: inputValue,
      sender: 'user',
      timestamp: new Date().toISOString()
    };

    // Add user message
    setMessages(prev => [...prev, newMessage]);
    setInputValue('');

    // In a real app, this would be:
    // try {
    //   const response = await fetch('/api/v1/conversation/message', {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify({
    //       conversationId: scenarioData.id,
    //       message: inputValue
    //     }),
    //   });
    //   const data = await response.json();
    //   // Process AI response
    // } catch (error) {
    //   console.error('Error sending message:', error);
    // }

    // Mock AI response with typing indicator
    setIsTyping(true);
    
    // Generate responses based on context - would be replaced by actual API call
    setTimeout(() => {
      const responseOptions = [
        "That's interesting! Tell me more about that.",
        "I see where you're coming from. What makes you feel that way?",
        "Hmm, I haven't thought about it like that before. What else is on your mind?",
        "I totally get what you're saying! What else do you enjoy?",
        "That's cool! I'm actually into similar things. Have you always been interested in that?",
        "Interesting perspective! I'd love to hear more about your thoughts on this.",
        "I'm not sure I fully understand - could you explain a bit more?",
        "That's a unique way of looking at things. What led you to that conclusion?",
        "I really like how you expressed that! What else would you like to talk about?",
        "That's quite the take! Do you usually approach conversations this way?"
      ];
      
      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        text: responseOptions[Math.floor(Math.random() * responseOptions.length)],
        sender: 'system',
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, aiMessage]);
      setIsTyping(false);
      
      // If this was the 10th total message exchange, trigger the assessment
      const updatedUserMessages = messages.filter(m => m.sender === 'user');
      if (updatedUserMessages.length >= 9) {
        setTimeout(() => {
          onMessageLimit();
        }, 1000);
      }
    }, 1500);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-3xl mx-auto p-4">
      <div className="bg-black/30 backdrop-blur-md rounded-t-xl border border-white/10 p-4 flex items-center gap-3">
        <Avatar>
          <AvatarImage src={aiAvatar} />
          <AvatarFallback>{getInitials(characterName)}</AvatarFallback>
        </Avatar>
        <div>
          <h2 className="font-semibold text-white">{characterName}</h2>
          <p className="text-xs text-white/60">
            {scenarioData.setting} • {scenarioData.type} conversation
          </p>
        </div>
        <div className="ml-auto flex gap-2">
          <Button
            size="sm"
            variant="outline"
            className="text-xs border-white/10 bg-white/5 text-white hover:bg-white/10"
          >
            <Sparkles className="h-3 w-3 mr-1" />
            <span>
              {10 - messages.filter(m => m.sender === 'user').length} messages left
            </span>
          </Button>
        </div>
      </div>
      
      <ScrollArea className="flex-1 bg-black/20 backdrop-blur-sm border-x border-white/10 p-4">
        <div className="space-y-4 min-h-[calc(100vh-12rem)]">
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 
                  ${message.sender === 'user' 
                    ? 'bg-gradient-to-br from-blue-600 to-violet-600 text-white rounded-tr-none' 
                    : 'bg-white/10 text-white rounded-tl-none'
                  }`}
              >
                <p>{message.text}</p>
                <div className={`text-xs mt-1 ${message.sender === 'user' ? 'text-blue-100' : 'text-white/50'}`}>
                  {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </motion.div>
          ))}
          
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-white/10 text-white rounded-tl-none">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 rounded-full bg-white/50 animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 rounded-full bg-white/50 animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 rounded-full bg-white/50 animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </motion.div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>
      
      <div className="bg-black/30 backdrop-blur-md rounded-b-xl border border-white/10 p-4">
        <div className="flex items-center gap-2">
          <Input
            ref={inputRef}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            className="flex-1 bg-white/10 border-white/10 text-white"
            disabled={isLoading || isTyping || messages.filter(m => m.sender === 'user').length >= 9}
          />
          <Button
            size="icon"
            variant="outline"
            className="border-white/10 bg-white/5 text-white hover:bg-white/10"
            disabled={isLoading || isTyping}
          >
            <Mic className="h-5 w-5" />
          </Button>
          <Button
            size="icon"
            onClick={handleSendMessage}
            className="bg-gradient-to-r from-blue-600 to-violet-600 text-white hover:from-blue-700 hover:to-violet-700"
            disabled={!inputValue.trim() || isLoading || isTyping || messages.filter(m => m.sender === 'user').length >= 9}
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
        
        {messages.filter(m => m.sender === 'user').length >= 9 && !isLoading && (
          <p className="text-center text-white/70 text-sm mt-2">
            Message limit reached. Your conversation will be assessed soon.
          </p>
        )}
        
        {isLoading && (
          <p className="text-center text-white/70 text-sm mt-2 animate-pulse">
            Analyzing your conversation skills...
          </p>
        )}
      </div>
    </div>
  );
}