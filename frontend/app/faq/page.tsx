import fs from 'fs';
import path from 'path';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { ArrowLeft } from 'lucide-react';

// Function to safely load and parse JSON
const loadArchetypeData = () => {
  try {
    // Adjust path if archetypes.json is elsewhere relative to the project root
    const filePath = path.join(process.cwd(), '../backend/archetypes.json'); 
    const rawData = fs.readFileSync(filePath, 'utf-8');
    const jsonData = JSON.parse(rawData);
    return jsonData;
  } catch (error) {
    console.error("Error loading archetypes.json:", error);
    return { user_archetypes: {}, conversation_aspects: {} }; // Return empty structure on error
  }
};

export default function FaqPage() {
  const data = loadArchetypeData();
  const userArchetypes = data.user_archetypes || {};
  const conversationAspects = data.conversation_aspects || {};

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-black text-white p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <Link href="/scenario">
            <Button variant="outline" className="bg-gradient-to-r from-grey-500 to-grey-900 hover:text-blue-400 text-white mb-4">
              <ArrowLeft className="mr-2 h-4 w-4" /> Back to Scenario Setup
            </Button>
          </Link>
          <h1 className="text-3xl md:text-4xl font-bold mb-2 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-cyan-400 to-green-400">
            Understanding the Vibe
          </h1>
          <p className="text-lg text-white/70">
            Get familiar with the communication styles and conversational elements we analyze.
          </p>
        </div>

        {/* User Archetypes Section */}
        <Card className="mb-8 bg-white/5 border-white/10 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-2xl text-white">Gen Z Communication Archetypes</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(userArchetypes).map(([key, value]) => (
              <div key={key} className="p-4 bg-black/20 rounded-lg border border-white/10">
                <h3 className="font-semibold text-lg mb-1 text-cyan-300">{key}</h3>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Conversation Aspects Section */}
        <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-2xl text-white">Conversation Aspects Explained</CardTitle>
          </CardHeader>
          <CardContent>
             <Accordion type="single" collapsible className="w-full">
               {Object.entries(conversationAspects).map(([key, value]) => {
                  const details = value as { description?: string; good?: string; bad?: string }; // Type assertion
                  return (
                    <AccordionItem value={key} key={key} className="border-white/10">
                      <AccordionTrigger className="text-lg hover:no-underline text-green-300 font-medium">
                        {key}
                      </AccordionTrigger>
                      <AccordionContent className="text-white/80 space-y-2 text-base pt-2">
                        <p>{details.description || 'No description available.'}</p>
                      </AccordionContent>
                    </AccordionItem>
                  );
                })}
            </Accordion>
          </CardContent>
        </Card>

      </div>
    </div>
  );
} 