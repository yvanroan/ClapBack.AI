'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ChatInterface } from '@/components/chat-interface';
import { AssessmentResult } from '@/components/assessment-result';
import { Button } from '@/components/ui/button';
import { ScenarioData, ChatMessage } from '@/lib/types';
import { useToast } from '@/hooks/use-toast';
import { Loader2 } from 'lucide-react';

// Define the API endpoint URL using environment variables with a fallback
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

if (API_BASE_URL=='http://localhost:8000') {
  console.log("🚨 You are using the local endpoint, hopefully this is not prod");
}

export default function ChatPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { toast } = useToast();
  
  // State Management
  const [scenarioId, setScenarioId] = useState<string | null>(null);
  const [scenarioData, setScenarioData] = useState<ScenarioData | null>(null);
  const [isScenarioLoading, setIsScenarioLoading] = useState(true); // Loading state for initial scenario fetch
  const [showAssessment, setShowAssessment] = useState(false);
  const [assessmentData, setAssessmentData] = useState(null);
  const [isAssessmentLoading, setIsAssessmentLoading] = useState(false); // Loading state for assessment fetch
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  // Effect to fetch Scenario Data based on ID from URL
  useEffect(() => {
    const id = searchParams.get('id');
    if (!id) {
      toast({
        title: "Missing Scenario ID",
        description: "Could not find the scenario identifier. Redirecting home.",
        variant: "destructive",
      });
      router.push('/');
      return;
    }
    setScenarioId(id);

    const fetchScenario = async () => {
      setIsScenarioLoading(true);
      try {
        console.log(`Fetching scenario data for ID: ${id}`);
        const response = await fetch(`${API_BASE_URL}/api/v1/scenario/${id}`);
        if (!response.ok) {
           let errorDetail = "Scenario details not found or invalid.";
            try {
              const errorData = await response.json();
              errorDetail = errorData.detail || errorDetail;
            } catch (e) { errorDetail = await response.text();} 
          throw new Error(`API Error (${response.status}): ${errorDetail}`);
        }
        const data: ScenarioData = await response.json();
        setScenarioData(data);
        console.log("Scenario data loaded:", data);
      } catch (error) {
        console.error('Error fetching scenario data:', error);
        toast({
          title: "Failed to Load Scenario",
          description: error instanceof Error ? error.message : "Could not load the conversation details.",
          variant: "destructive",
        });
        router.push('/'); // Redirect home on failure
      } finally {
        setIsScenarioLoading(false);
      }
    };

    fetchScenario();

  }, [searchParams, router, toast]); // Dependencies

  // MODIFIED: handleMessageLimit to fetch real assessment
  const handleMessageLimit = async () => {
    if (!scenarioId) {
        toast({ title: "Error", description: "Scenario ID is missing.", variant: "destructive"});
        return;
    }
    
    setIsAssessmentLoading(true); // Use specific loading state
    console.log(`Requesting assessment for scenario ID: ${scenarioId}`);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/conversation/${scenarioId}/assess`, {
        method: 'POST', // POST request to trigger assessment
        headers: { 'Content-Type': 'application/json' },
        // No body needed if ID is in the URL
      });
      
      if (!response.ok) {
          let errorDetail = "Failed to get assessment.";
          try {
            const errorData = await response.json();
            errorDetail = errorData.detail || errorDetail;
          } catch (e) { errorDetail = await response.text();} 
        throw new Error(`API Error (${response.status}): ${errorDetail}`);
      }
      
      // Safely parse the JSON response
      let assessmentResult;
      try {
        const responseText = await response.text();
        // Try to parse the response, handle any syntax errors
        try {
          assessmentResult = JSON.parse(responseText);
        } catch (parseError: any) {
          console.error("JSON parse error:", parseError);
          console.log("Raw response:", responseText);
          // Attempt to clean the response if it has extra characters
          const cleanedText = responseText.replace(/[^\x20-\x7E]/g, '');
          try {
            assessmentResult = JSON.parse(cleanedText);
          } catch (secondParseError) {
            throw new Error(`Invalid JSON response: ${parseError.message}`);
          }
        }
      } catch (error) {
        console.error("Error processing response:", error);
        throw new Error("Failed to process assessment response");
      }
      
      console.log("Assessment received:", assessmentResult);

      // Check if the response contains the raw text fallback
      if (assessmentResult.raw_text_response && assessmentResult.raw_text_response !== "") {
           toast({
            title: "Assessment Parsing Issue",
            description: "The AI's assessment wasn't perfectly formatted, showing raw results.",
            variant: "default",
          });
          console.log("Raw AI assessment text response:", assessmentResult.raw_text_response);
      } 
      // Or if assessment is completely empty/invalid
      else if (!assessmentResult || Object.keys(assessmentResult).length === 0) { 
          throw new Error("Received empty or invalid assessment data.");
      }

      setAssessmentData(assessmentResult); 
      setShowAssessment(true);

    } catch (error) {
       console.error("Error fetching assessment:", error);
      toast({
        title: "Assessment Failed",
        description: error instanceof Error ? error.message : "We couldn't analyze your conversation. Try again later!",
        variant: "destructive",
      });
      // Keep the user on the chat page or provide a retry option? 
      // For now, just show the error.
    } finally {
      setIsAssessmentLoading(false); // Use specific loading state
    }
  };

  const handleRetry = () => {
    // Navigate back to the scenario setup page
    router.push('/scenario'); 
  };

  // Loading state for initial scenario fetch
  if (isScenarioLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-violet-800 to-indigo-900 flex items-center justify-center">
        <div className="text-center p-6">
          <Loader2 className="h-12 w-12 text-white animate-spin mx-auto mb-4" />
          <h1 className="text-xl font-semibold text-white/80">Loading Scenario...</h1>
        </div>
      </div>
    );
  }
  
  // If scenario data failed to load after trying (should be caught by useEffect redirect, but good fallback)
  if (!scenarioData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-violet-800 to-indigo-900 flex items-center justify-center">
        <div className="text-center p-6 bg-black/30 backdrop-blur-lg rounded-xl">
          <h1 className="text-2xl font-bold mb-4 text-red-400">Failed to Load Scenario</h1>
          <Button onClick={() => router.push('/')} variant="secondary">Back to Home</Button>
        </div>
      </div>
    );
  }

  // Main component rendering logic
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-violet-800 to-indigo-900 relative overflow-hidden">
      {showAssessment ? (
        <AssessmentResult 
          assessmentData={assessmentData} 
          onRetry={handleRetry} // Pass retry handler
          messages={messages} // Pass conversation messages to assessment result
          scenarioData={scenarioData} // Pass scenario data for context
        />
      ) : (
        <ChatInterface 
          scenarioData={scenarioData} 
          scenarioId={scenarioId}
          onMessageLimit={handleMessageLimit}
          isLoading={isAssessmentLoading} 
          onMessagesUpdate={setMessages}
        />
      )}
    </div>
  );
}