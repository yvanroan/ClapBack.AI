'use client';

import React from 'react';
import { motion } from '@/lib/motion';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Sparkles, Award, PlusCircle, MinusCircle, AreaChart, RefreshCw } from 'lucide-react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

interface AssessmentResultProps {
  assessmentData: any;
  onRetry: () => void;
}

export function AssessmentResult({ assessmentData, onRetry }: AssessmentResultProps) {
  if (!assessmentData) return null;

  const {
    overall_score,
    feedback,
    strengths,
    areas_to_improve,
    stats
  } = assessmentData;

  // Convert stats object to array for RadarChart
  const chartData = Object.entries(stats).map(([key, value]) => ({
    subject: key.charAt(0).toUpperCase() + key.slice(1),
    value: value,
    fullMark: 100,
  }));

  // Get score color based on value
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-400';
    if (score >= 75) return 'text-blue-400';
    if (score >= 60) return 'text-yellow-400';
    if (score >= 40) return 'text-orange-400';
    return 'text-red-400';
  };

  // Get score label based on value
  const getScoreLabel = (score: number) => {
    if (score >= 90) return 'S-Tier Rizz';
    if (score >= 80) return 'Elite Conversationalist';
    if (score >= 70) return 'Smooth Talker';
    if (score >= 60) return 'Decent Vibes';
    if (score >= 50) return 'Mid Game';
    if (score >= 40) return 'Awkward Energy';
    if (score >= 30) return 'Major Yikes';
    return 'Rizz-less';
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
                    className="w-32 h-32 rounded-full flex items-center justify-center bg-gradient-to-br from-indigo-900/50 to-purple-900/50 border-4 border-white/10"
                  >
                    <div className="text-3xl font-bold text-white">
                      {overall_score}
                    </div>
                  </motion.div>
                  <motion.div
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 1 }}
                    className="absolute -top-2 -right-2 bg-gradient-to-r from-yellow-400 to-orange-500 text-white text-xs font-bold px-3 py-1 rounded-full flex items-center"
                  >
                    <Award className="h-3 w-3 mr-1" />
                    {getScoreLabel(overall_score)}
                  </motion.div>
                </div>
                <p className={`mt-2 font-semibold ${getScoreColor(overall_score)}`}>
                  {overall_score >= 70 ? 'Impressive!' : overall_score >= 50 ? 'Not bad.' : 'Needs work!'}
                </p>
              </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 }}
                className="flex flex-col"
              >
                <h2 className="text-xl font-semibold mb-3 text-white flex items-center">
                  <Sparkles className="h-5 w-5 mr-2 text-blue-400" />
                  Feedback Summary
                </h2>
                <div className="bg-white/5 rounded-xl p-5 flex-1 border border-white/10">
                  <p className="text-white/80 leading-relaxed">{feedback}</p>
                </div>
                
                <h2 className="text-xl font-semibold mt-6 mb-3 text-white flex items-center">
                  <AreaChart className="h-5 w-5 mr-2 text-indigo-400" />
                  Conversation Stats
                </h2>
                
                <div className="bg-white/5 rounded-xl p-4 border border-white/10 h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={chartData} margin={{ top: 0, right: 30, bottom: 0, left: 30 }}>
                      <PolarGrid stroke="rgba(255, 255, 255, 0.1)" />
                      <PolarAngleAxis dataKey="subject" tick={{ fill: 'rgba(255, 255, 255, 0.7)', fontSize: 12 }} />
                      <Radar
                        name="Skills"
                        dataKey="value"
                        stroke="rgba(147, 51, 234, 0.8)"
                        fill="rgba(147, 51, 234, 0.6)"
                        fillOpacity={0.6}
                      />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'rgba(0, 0, 0, 0.8)', 
                          border: '1px solid rgba(255, 255, 255, 0.2)',
                          borderRadius: '6px',
                          color: 'white'
                        }}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
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
                    {strengths.map((strength: string, index: number) => (
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
                    ))}
                  </ul>
                </div>
                
                <h2 className="text-xl font-semibold mb-3 text-white flex items-center">
                  <MinusCircle className="h-5 w-5 mr-2 text-orange-400" />
                  Areas to Improve
                </h2>
                <div className="bg-white/5 rounded-xl p-5 border border-white/10">
                  <ul className="space-y-3">
                    {areas_to_improve.map((area: string, index: number) => (
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
                        <span className="text-white/80">{area}</span>
                      </motion.li>
                    ))}
                  </ul>
                </div>
                
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 1.6 }}
                  className="mt-8 flex justify-center"
                >
                  <Button
                    onClick={onRetry}
                    className="bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white font-medium px-6 py-2"
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