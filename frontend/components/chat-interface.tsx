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
import Link from 'next/link';

// Import archetype images
import IcyOneMale from './assets/icy_one_2_male.png';
import IcyOneFemale from './assets/icy_one_2_female.png';
import ChaoticExtrovertMale from './assets/chaotic_extrovert_male.png';
import ChaoticExtrovertFemale from './assets/chaotic_extrovert_female.png';
import PhilosopherMale from './assets/philosopher_situationship_male.png';
import PhilosopherFemale from './assets/philosopher_situationship_female.png';
import CertifiedBaddieMale from './assets/certified_baddie_males.png';
import CertifiedBaddieFemale from './assets/certified_baddie_female.png';
import AwkwardSweetheartMale from './assets/awkward_sweetheart_male.png';
import AwkwardSweetheartFemale from './assets/awkward_sweetheart_female.png';

// Function to get the appropriate avatar based on archetype and sex
const getAvatarForArchetype = (archetype: string, sex: string) => {
  const archetypeKey = archetype.toLowerCase().split(',')[0].trim();
  
  if (archetypeKey.includes('icy')) {
    return sex.toLowerCase() === 'male' ? IcyOneMale.src : IcyOneFemale.src;
  } else if (archetypeKey.includes('chaotic')) {
    return sex.toLowerCase() === 'male' ? ChaoticExtrovertMale.src : ChaoticExtrovertFemale.src;
  } else if (archetypeKey.includes('philosopher')) {
    return sex.toLowerCase() === 'male' ? PhilosopherMale.src : PhilosopherFemale.src;
  } else if (archetypeKey.includes('baddie')) {
    return sex.toLowerCase() === 'male' ? CertifiedBaddieMale.src : CertifiedBaddieFemale.src;
  } else if (archetypeKey.includes('awkward')) {
    return sex.toLowerCase() === 'male' ? AwkwardSweetheartMale.src : AwkwardSweetheartFemale.src;
  }
  
  // Default fallback
  return sex.toLowerCase() === 'male' ? AwkwardSweetheartMale.src : AwkwardSweetheartFemale.src;
};

const getInitials = (name: string) => {
  return name
    .split(' ')
    .map(word => word[0])
    .join('')
    .toUpperCase();
};

interface ChatInterfaceProps {
  scenarioData: ScenarioData;
  scenarioId: string | null;
  onMessageLimit: () => void;
  isLoading: boolean;
}

// Define the API endpoint URL using environment variables with a fallback
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function ChatInterface({ 
  scenarioData, 
  scenarioId,
  onMessageLimit,
  isLoading 
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const characterName = scenarioData.system_archetype.split(',')[0];
  const avatarSrc = getAvatarForArchetype(scenarioData.system_archetype, scenarioData.system_sex);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading || !scenarioId) {
      if (!scenarioId) {
        console.error("Attempted to send message but scenarioId prop is missing.");
        toast({
          title: "Missing scenario ID",
          description: "Could not send message. Please try again later.",
          variant: "destructive",
        });
      }
      return;
    }
    
    const currentUserMessageCount = messages.filter(m => m.sender === 'user').length;
    if (currentUserMessageCount >= 5) {
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

    const currentInput = inputValue;
    
    setMessages(prev => [...prev, newMessage]); 
    setInputValue('');

    try {
      const payload = {
          scenario_id: scenarioId,
          user_input: currentInput
      };

      console.log("Sending to /api/v1/process_chat:", payload);

      const response = await fetch(`${API_BASE_URL}/api/v1/process_chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        let errorDetail = "Failed to get response from AI.";
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || errorDetail;
        } catch (e) {
            errorDetail = await response.text();
        }
        throw new Error(`API Error (${response.status}): ${errorDetail}`);
      }

      const data = await response.json();

      if (!data || !data.content){
          throw new Error("Invalid response format from AI.");
      }

      // Add AI response to UI
      const aiMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          text: data.content,
          sender: 'system', // Use 'system' or 'assistant' for role
          timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, aiMessage]);

      // Check message limit AFTER successful AI response
      if (currentUserMessageCount + 1 >= 5) {
           setTimeout(() => { // Small delay before triggering assessment UI
               onMessageLimit();
           }, 1000);
      }
      
    } catch (error) {
        console.error("Error sending message:", error);
        toast({
            title: "Message Failed",
            description: error instanceof Error ? error.message : "Could not get AI response. Please try again.",
            variant: "destructive",
          });
        // Optional: Remove the user's message if the API call failed?
        // setMessages(prev => prev.slice(0, -1)); 
    } 
    // No finally block needed if isLoading is fully managed by the parent
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
      <Avatar className="w-24 h-24 border border-white/20 overflow-hidden">
      <AvatarImage src={avatarSrc} alt={characterName} className="object-scale-down" />
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
              {Math.max(0, 5 - messages.filter(m => m.sender === 'user').length)} messages left
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
            disabled={isLoading || messages.filter(m => m.sender === 'user').length >= 5}
          />
          <Button
            size="icon"
            variant="outline"
            className="border-white/10 bg-white/5 text-white hover:bg-white/10"
            disabled={isLoading}
          >
            <Mic className="h-5 w-5" />
          </Button>
          <Button
            size="icon"
            onClick={handleSendMessage}
            className="bg-gradient-to-r from-blue-600 to-violet-600 text-white hover:from-blue-700 hover:to-violet-700"
            disabled={!inputValue.trim() || isLoading || messages.filter(m => m.sender === 'user').length >= 5}
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
        
        {messages.filter(m => m.sender === 'user').length >= 5 && !isLoading && (
          <p className="text-center text-white/70 text-sm mt-2">
            Message limit reached. Your conversation will be assessed soon.
          </p>
        )}
        
        {isLoading && (
          <p className="text-center text-white/70 text-sm mt-2 animate-pulse">
            Thinking...
          </p>
        )}
        
        {/* FAQ Link */}
        <p className="text-center text-xs text-white/50 mt-3 pt-2 border-t border-white/10">
          Want to understand communication archetypes better? 
          <Link href="/faq" className="text-cyan-400 hover:text-cyan-300 underline ml-1">
            Check out our guide
          </Link>
        </p>
      </div>
    </div>
  );
}