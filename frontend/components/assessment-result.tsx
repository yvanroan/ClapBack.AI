'use client';

import React, { useState } from 'react';
import { motion } from '@/lib/motion';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { PlusCircle, MinusCircle, RefreshCw, MessageSquare, AlertTriangle, CheckCircle2, Star, HistoryIcon, XIcon } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ChatMessage, ScenarioData } from '@/lib/types';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

interface AssessmentResultProps {
  assessmentData: any;
  onRetry: () => void;
  messages?: ChatMessage[];
  scenarioData?: ScenarioData;
}

export function AssessmentResult({ 
  assessmentData, 
  onRetry,
  messages = [],
  scenarioData
}: AssessmentResultProps) {
  const [showConversation, setShowConversation] = useState(false);
  
  if (!assessmentData) return null;

  const {
    primary_archetype,
    secondary_archetype,
    strengths,
    weaknesses,
    justification,
    highlights,
    cringe_moments,
    raw_text_response
  } = assessmentData;

  const toggleConversation = () => {
    setShowConversation(!showConversation);
  };
  
  // Format timestamp to readable time
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="min-h-screen max-w-4xl mx-auto p-4 py-8 flex flex-col items-center justify-center"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.3, duration: 0.5 }}
        className="w-full"
      >
        <Card className="bg-black/30 backdrop-blur-lg border border-white/10 overflow-hidden">
          <div className="p-6 lg:p-8">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-8">
              <div className="text-center md:text-left">
                <h3 className="text-lg text-white/70">Your Rizz Report™</h3>
                <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-pink-400 via-purple-400 to-indigo-400">
                  Conversation Analysis
                </h1>
              </div>
              
              <div className="flex flex-col items-center">
                <div className="relative">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ 
                      type: "spring", 
                      stiffness: 260, 
                      damping: 20,
                      delay: 0.6 
                    }}
                    className="w-32 h-32 rounded-full flex flex-col items-center justify-center bg-gradient-to-br from-indigo-900/50 to-purple-900/50 border-4 border-white/10 p-2"
                  >
                    <div className="text-sm font-medium text-white/80">Your Style</div>
                    <div className="text-xl font-bold text-white text-center mt-1">
                      {primary_archetype}
                    </div>
                  </motion.div>
                  {secondary_archetype && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 1 }}
                      className="absolute -top-2 -right-2 bg-gradient-to-r from-yellow-400 to-orange-500 text-white text-xs font-bold px-3 py-1 rounded-full flex items-center"
                    >
                      <Star className="h-3 w-3 mr-1" />
                      {secondary_archetype}
                    </motion.div>
                  )}
                </div>
              </div>
            </div>
            
            {/* Conversation History Modal */}
            {showConversation && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
                onClick={(e) => {
                  if (e.target === e.currentTarget) toggleConversation();
                }}
              >
                <div className="w-full max-w-3xl bg-black/70 border border-white/10 rounded-xl overflow-hidden">
                  <div className="p-4 border-b border-white/10 flex justify-between items-center">
                    <h3 className="text-xl font-bold text-white">Conversation History</h3>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      onClick={toggleConversation}
                      className="text-white/70 hover:text-white"
                    >
                      <XIcon className="h-5 w-5" />
                    </Button>
                  </div>
                  <ScrollArea className="h-[70vh] p-4">
                    <div className="space-y-4">
                      {messages.length > 0 ? (
                        messages.map((message) => (
                          <div 
                            key={message.id}
                            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                          >
                            {message.sender === 'system' && scenarioData && (
                              <Avatar className="h-8 w-8 mr-2 flex-shrink-0 self-end mb-2">
                                <AvatarFallback>{scenarioData.system_archetype.charAt(0)}</AvatarFallback>
                              </Avatar>
                            )}
                            <div
                              className={`max-w-[80%] rounded-2xl px-4 py-3 
                                ${message.sender === 'user' 
                                  ? 'bg-gradient-to-br from-blue-600 to-violet-600 text-white rounded-tr-none' 
                                  : 'bg-white/10 text-white rounded-tl-none'
                                }`}
                            >
                              <p>{message.text}</p>
                              <div className={`text-xs mt-1 ${message.sender === 'user' ? 'text-blue-100' : 'text-white/50'}`}>
                                {formatTime(message.timestamp)}
                              </div>
                            </div>
                            {message.sender === 'user' && (
                              <Avatar className="h-8 w-8 ml-2 flex-shrink-0 self-end mb-2">
                                <AvatarFallback>U</AvatarFallback>
                              </Avatar>
                            )}
                          </div>
                        ))
                      ) : (
                        <p className="text-center text-white/50 py-8">No conversation history available</p>
                      )}
                    </div>
                  </ScrollArea>
                </div>
              </motion.div>
            )}
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 }}
                className="flex flex-col"
              >
                <h2 className="text-xl font-semibold mb-3 text-white flex items-center">
                  <MessageSquare className="h-5 w-5 mr-2 text-blue-400" />
                  Analysis
                </h2>
                <div className="bg-white/5 rounded-xl p-5 flex-1 border border-white/10">
                  <p className="text-white/80 leading-relaxed">{justification}</p>
                </div>
                
                <h2 className="text-xl font-semibold mt-6 mb-3 text-white flex items-center">
                  <CheckCircle2 className="h-5 w-5 mr-2 text-indigo-400" />
                  Highlights
                </h2>
                
                <div className="bg-white/5 rounded-xl p-5 border border-white/10">
                  <ul className="space-y-3">
                    {highlights?.map((highlight: string, index: number) => (
                      <motion.li
                        key={index}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 1 + index * 0.1 }}
                        className="flex items-start"
                      >
                        <span className="bg-indigo-500/20 text-indigo-400 rounded-full w-6 h-6 flex items-center justify-center mr-3 mt-0.5 flex-shrink-0 border border-indigo-500/30">
                          ✓
                        </span>
                        <span className="text-white/80">{highlight}</span>
                      </motion.li>
                    ))}
                  </ul>
                </div>
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.9 }}
              >
                <h2 className="text-xl font-semibold mb-3 text-white flex items-center">
                  <PlusCircle className="h-5 w-5 mr-2 text-green-400" />
                  Strengths
                </h2>
                <div className="bg-white/5 rounded-xl p-5 mb-6 border border-white/10">
                  <ul className="space-y-3">
                    {Array.isArray(strengths) ? (
                      strengths.map((strength: string, index: number) => (
                        <motion.li
                          key={index}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 1 + index * 0.1 }}
                          className="flex items-start"
                        >
                          <span className="bg-green-500/20 text-green-400 rounded-full w-6 h-6 flex items-center justify-center mr-3 mt-0.5 flex-shrink-0 border border-green-500/30">
                            ✓
                          </span>
                          <span className="text-white/80">{strength}</span>
                        </motion.li>
                      ))
                    ) : strengths ? (
                      <motion.li
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 1 }}
                        className="flex items-start"
                      >
                        <span className="bg-green-500/20 text-green-400 rounded-full w-6 h-6 flex items-center justify-center mr-3 mt-0.5 flex-shrink-0 border border-green-500/30">
                          ✓
                        </span>
                        <span className="text-white/80">{strengths}</span>
                      </motion.li>
                    ) : (
                      <p className="text-white/50 italic">No strengths identified</p>
                    )}
                  </ul>
                </div>
                
                <h2 className="text-xl font-semibold mb-3 text-white flex items-center">
                  <MinusCircle className="h-5 w-5 mr-2 text-orange-400" />
                  Areas to Improve
                </h2>
                <div className="bg-white/5 rounded-xl p-5 mb-6 border border-white/10">
                  <ul className="space-y-3">
                    {Array.isArray(weaknesses) ? (
                      weaknesses.map((weakness: string, index: number) => (
                        <motion.li
                          key={index}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 1.3 + index * 0.1 }}
                          className="flex items-start"
                        >
                          <span className="bg-orange-500/20 text-orange-400 rounded-full w-6 h-6 flex items-center justify-center mr-3 mt-0.5 flex-shrink-0 border border-orange-500/30">
                            !
                          </span>
                          <span className="text-white/80">{weakness}</span>
                        </motion.li>
                      ))
                    ) : weaknesses ? (
                      <motion.li
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 1.3 }}
                        className="flex items-start"
                      >
                        <span className="bg-orange-500/20 text-orange-400 rounded-full w-6 h-6 flex items-center justify-center mr-3 mt-0.5 flex-shrink-0 border border-orange-500/30">
                          !
                        </span>
                        <span className="text-white/80">{weaknesses}</span>
                      </motion.li>
                    ) : (
                      <p className="text-white/50 italic">No areas to improve identified</p>
                    )}
                  </ul>
                </div>
                
                <h2 className="text-xl font-semibold mb-3 text-white flex items-center">
                  <AlertTriangle className="h-5 w-5 mr-2 text-red-400" />
                  Cringe Moments
                </h2>
                <div className="bg-white/5 rounded-xl p-5 border border-white/10">
                  <ul className="space-y-3">
                    {cringe_moments?.map((moment: string, index: number) => (
                      <motion.li
                        key={index}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 1.3 + index * 0.1 }}
                        className="flex items-start"
                      >
                        <span className="bg-red-500/20 text-red-400 rounded-full w-6 h-6 flex items-center justify-center mr-3 mt-0.5 flex-shrink-0 border border-red-500/30">
                          ✗
                        </span>
                        <span className="text-white/80">{moment}</span>
                      </motion.li>
                    ))}
                  </ul>
                </div>
                
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 1.6 }}
                  className="mt-8 flex justify-center gap-4"
                >
                  <Button
                    onClick={toggleConversation}
                    className="bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white font-medium px-4 py-2"
                  >
                    <HistoryIcon className="mr-2 h-4 w-4" />
                    View Conversation
                  </Button>
                  
                  <Button
                    onClick={onRetry}
                    className="bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white font-medium px-4 py-2"
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Try Another Conversation
                  </Button>
                </motion.div>
              </motion.div>
            </div>
          </div>
        </Card>
      </motion.div>
    </motion.div>
  );
}