'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Mic, Send, Sparkles, Info } from 'lucide-react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { motion } from '@/lib/motion';
import { ScenarioData } from '@/lib/types';
import { useToast } from '@/hooks/use-toast';
import { ChatMessage } from '@/lib/types';
import Link from 'next/link';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

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
  onMessagesUpdate?: (messages: ChatMessage[]) => void;
}

// Define the API endpoint URL using environment variables with a fallback
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

if (API_BASE_URL=='http://localhost:8000') {
  console.log("🚨 You are using the local endpoint, hopefully this is not prod");
}

export function ChatInterface({ 
  scenarioData, 
  scenarioId,
  onMessageLimit,
  isLoading,
  onMessagesUpdate 
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

  useEffect(() => {
    if (onMessagesUpdate) {
      onMessagesUpdate(messages);
    }
  }, [messages, onMessagesUpdate]);

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
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <h2 className="font-semibold text-white">{characterName}</h2>
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="ghost" size="icon" className="h-6 w-6 rounded-full p-0 text-white/70 hover:text-white hover:bg-white/10">
                  <Info className="h-4 w-4" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80 bg-black/80 backdrop-blur-md border border-white/10 text-white p-4 rounded-xl shadow-xl">
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 via-purple-400 to-indigo-400">Scenario Details</h3>
                  
                  <div className="space-y-2">
                    <div>
                      <h4 className="text-xs text-white/50">Conversation Type</h4>
                      <p className="text-sm">{scenarioData.scenario_type || 'Not specified'}</p>
                    </div>
                    
                    <div>
                      <h4 className="text-xs text-white/50">Setting</h4>
                      <p className="text-sm">{scenarioData.setting}</p>
                    </div>
                    
                    <div>
                      <h4 className="text-xs text-white/50">Your Goal</h4>
                      <p className="text-sm">{scenarioData.goal}</p>
                    </div>
                    
                    <div>
                      <h4 className="text-xs text-white/50">Character Archetype</h4>
                      <p className="text-sm">{scenarioData.system_archetype}</p>
                    </div>
                    
                    <div>
                      <h4 className="text-xs text-white/50">Roast Level</h4>
                      <div className="flex items-center gap-2">
                        <div className="bg-white/10 h-1.5 flex-1 rounded-full overflow-hidden">
                          <div 
                            className="bg-gradient-to-r from-green-400 to-red-500 h-full" 
                            style={{ width: `${(scenarioData.roast_level / 5) * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-xs">{scenarioData.roast_level}/5</span>
                      </div>
                      <p className="text-xs text-white/50 mt-1">
                        {scenarioData.roast_level === 1 && "Be gentle with me"}
                        {scenarioData.roast_level === 2 && "Slight roast"}
                        {scenarioData.roast_level === 3 && "Balanced feedback"}
                        {scenarioData.roast_level === 4 && "Don't hold back"}
                        {scenarioData.roast_level === 5 && "Destroy me completely"}
                      </p>
                    </div>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          </div>
          <p className="text-xs text-white/60">
            {scenarioData.setting} • {scenarioData.scenario_type} conversation
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