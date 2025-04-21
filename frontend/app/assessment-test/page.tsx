'use client';

import { AssessmentResult } from '@/components/assessment-result';
import { useRouter } from 'next/navigation';

// Mock assessment data based on the provided JSON
const mockAssessmentData = {
  primary_archetype: "Dry Texter IRL",
  secondary_archetype: "No Social Battery",
  strengths: [
    "Reciprocity",
    "Initial engagement",
    "Willingness to start conversation"
  ],
  weaknesses: [
    "Emotional Heat",
    "Depth of conversation",
    "Sustaining engagement"
  ],
  justification: "The user started strong but quickly became avoidant of deeper engagement, defaulting to safe and somewhat generic responses, and ultimately shutting down the philosophical back-and-forth. They seem to lose steam and push back when the conversation requires vulnerability.",
  highlights: [
    "Maybe. Or maybe your presence just makes the room aware of what it's missing. My name is Obi by the way, whats yours ?",
    "I'd probably remember this moment, your voice, the room, my friends. you know, now is all we have"
  ],
  cringe_moments: [
    "i think that you're fishing too deep here, just have fun. its a party, come on jess is cutting the cake",
    "everything isn't about philosophized, life is meant for leaving. if you keep thinking about everything you have nothing in your mind except thoughts. enjoy the experience here and now"
  ],
  raw_text_response: null
};

export default function AssessmentTestPage() {
  const router = useRouter();
  
  const handleRetry = () => {
    router.push('/scenario');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-violet-800 to-indigo-900 relative overflow-hidden">
      <AssessmentResult 
        assessmentData={mockAssessmentData} 
        onRetry={handleRetry}
      />
    </div>
  );
} 