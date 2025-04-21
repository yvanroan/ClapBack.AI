'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ChatInterface } from '@/components/chat-interface';
import { AssessmentResult } from '@/components/assessment-result';
import { Button } from '@/components/ui/button';
import { ScenarioData } from '@/lib/types';
import { useToast } from '@/hooks/use-toast';

export default function ChatPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { toast } = useToast();
  const [scenarioData, setScenarioData] = useState<ScenarioData | null>(null);
  const [showAssessment, setShowAssessment] = useState(false);
  const [assessmentData, setAssessmentData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    try {
      const data = JSON.parse(searchParams.get('data') || '');
      if (!data) {
        throw new Error('No scenario data found');
      }
      setScenarioData(data);
    } catch (error) {
      toast({
        title: "Oops! Something's missing",
        description: "We couldn't find your scenario data. Let's start over.",
        variant: "destructive",
      });
      router.push('/');
    }
  }, [searchParams, router, toast]);

  const handleMessageLimit = async () => {
    setIsLoading(true);
    try {
      // Mock API call for assessment
      // In a real app, this would be:
      const response = await fetch('/api/v1/conversation/assessment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversationId: scenarioData.id }),
      });
      const data = await response.json();
      
      // Mock data for demo
      // const mockAssessment = {
      //   overall_score: 85,
      //   feedback: "You've got some serious rizz! Your conversation game is strong, but there's always room to level up. You're great at keeping things flowing, but sometimes you might come on a bit too strong.",
      //   strengths: ["Great opening lines", "Smooth topic transitions", "Good humor integration"],
      //   areas_to_improve: ["Listen more actively", "Ask more open-ended questions"],
      //   stats: {
      //     engagement: 78,
      //     empathy: 82,
      //     humor: 90,
      //     authenticity: 85,
      //     confidence: 88
      //   }
      // };
      
      setTimeout(() => {
        setAssessmentData(mockAssessment);
        setShowAssessment(true);
        setIsLoading(false);
      }, 1500);
    } catch (error) {
      toast({
        title: "Assessment Failed",
        description: "We couldn't analyze your conversation. Try again later!",
        variant: "destructive",
      });
      setIsLoading(false);
    }
  };

  const handleRetry = () => {
    router.push('/scenario');
  };

  if (!scenarioData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-violet-800 to-indigo-900 flex items-center justify-center">
        <div className="text-center p-6 bg-black/30 backdrop-blur-lg rounded-xl">
          <h1 className="text-2xl font-bold mb-4">Loading your convo...</h1>
          <Button onClick={() => router.push('/')}>Back to Home</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-violet-800 to-indigo-900 relative overflow-hidden">
      {showAssessment ? (
        <AssessmentResult 
          assessmentData={assessmentData} 
          onRetry={handleRetry}
        />
      ) : (
        <ChatInterface 
          scenarioData={scenarioData} 
          onMessageLimit={handleMessageLimit}
          isLoading={isLoading}
        />
      )}
    </div>
  );
}