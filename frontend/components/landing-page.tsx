'use client';

import { useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { motion } from '@/lib/motion';
import { MessageCircle, Sparkles, Star, Zap } from 'lucide-react';
import { FloatingEmojis } from './ui/floating-emojis';
import { TypeAnimation } from './ui/type-animation';

export function LandingPage() {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoverState, setHoverState] = useState(false);

  return (
    <div ref={containerRef} className="min-h-screen relative bg-gradient-to-br from-purple-900 via-violet-800 to-indigo-900 flex flex-col items-center justify-center p-4 overflow-hidden">
      <FloatingEmojis />
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="max-w-3xl mx-auto text-center z-10"
      >
        <div className="mb-6 flex justify-center">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.3, type: "spring", stiffness: 200 }}
            className="w-24 h-24 bg-gradient-to-br from-pink-500 to-orange-400 rounded-2xl flex items-center justify-center shadow-lg"
          >
            <MessageCircle size={48} className="text-white" />
          </motion.div>
        </div>

        <h1 className="text-4xl md:text-6xl font-bold mb-3 text-transparent bg-clip-text bg-gradient-to-r from-pink-400 via-purple-400 to-indigo-400">
          <TypeAnimation text="How's Your Rizz Game?" />
        </h1>
        
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 0.8 }}
          className="text-xl md:text-2xl mb-8 text-white/90"
        >
          Test your conversation skills and get <span className="font-bold text-pink-300">brutally honest</span> feedback
        </motion.p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10 max-w-3xl mx-auto">
          {[
            { 
              icon: <Zap className="h-8 w-8 text-yellow-300" />, 
              title: "Chat Simulator", 
              description: "Practice your conversation game in different scenarios" 
            },
            { 
              icon: <Sparkles className="h-8 w-8 text-blue-300" />, 
              title: "Instant Feedback", 
              description: "Get roasted or praised based on your performance" 
            },
            { 
              icon: <Star className="h-8 w-8 text-pink-300" />, 
              title: "Level Up", 
              description: "Improve your rizz with actionable advice" 
            }
          ].map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 + index * 0.2, duration: 0.5 }}
              className="bg-black/30 backdrop-blur-md p-6 rounded-xl border border-white/10"
            >
              <div className="rounded-full w-12 h-12 flex items-center justify-center bg-white/10 mb-4 mx-auto">
                {feature.icon}
              </div>
              <h3 className="text-xl font-semibold mb-2 text-white">{feature.title}</h3>
              <p className="text-white/70">{feature.description}</p>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1.6, duration: 0.5 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.98 }}
        >
          <Button
            onClick={() => router.push('/scenario')}
            onMouseEnter={() => setHoverState(true)}
            onMouseLeave={() => setHoverState(false)}
            className="relative overflow-hidden group bg-gradient-to-r from-pink-500 to-purple-600 text-white text-lg px-8 py-6 rounded-xl font-semibold shadow-lg hover:shadow-pink-500/25 transition-all duration-300"
            size="lg"
          >
            <span className="relative z-10 flex items-center gap-2">
              Start Your Rizz Test
              <motion.span
                animate={{ rotate: hoverState ? 360 : 0 }}
                transition={{ duration: 0.5 }}
              >
                <Sparkles className="h-5 w-5" />
              </motion.span>
            </span>
            <motion.span
              className="absolute inset-0 bg-gradient-to-r from-purple-600 to-pink-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
              initial={false}
              animate={hoverState ? { opacity: 1 } : { opacity: 0 }}
            />
          </Button>
        </motion.div>
      </motion.div>
      
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 2, duration: 1 }}
        className="absolute bottom-4 text-center text-white/50 text-sm"
      >
        No sign-up required · Just vibe and get feedback
      </motion.div>
    </div>
  );
}