'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { ArrowLeft, ArrowRight, Sparkles, Loader2, Dices } from 'lucide-react';
import { motion } from '@/lib/motion';
import { ScenarioIDResponse } from '@/lib/types';
import { useToast } from '@/hooks/use-toast';
import Link from 'next/link';

const formSchema = z.object({
  scenario_type: z.string().min(1, "Select a conversation type"),
  setting: z.string().min(3, "Setting is required"),
  goal: z.string().min(3, "Goal is required"),
  system_archetype: z.string().min(1, "Character type is required"),
  roast_level: z.coerce.number().min(1).max(5),
  player_sex: z.string().min(1, "Please select your gender"),
  system_sex: z.string().min(1, "Please select character gender"),
});

// Define the API endpoint URL using environment variables with a fallback
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function ScenarioForm() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      scenario_type: "",
      setting: "",
      goal: "",
      system_archetype: "",
      roast_level: 3,
      player_sex: "",
      system_sex: "",
    },
  });

  const goToStep = (stepNumber: number) => {
    if (stepNumber === 2) {
      const step1Fields = ['scenario_type', 'setting', 'goal'];
      const step1Valid = step1Fields.every(field => {
        const fieldState = form.getFieldState(field as any);
        return !fieldState.invalid;
      });
      
      if (!step1Valid) {
        form.trigger(['scenario_type', 'setting', 'goal']);
        return;
      }
    }
    setStep(stepNumber);
  };

  const randomizeForm = () => {
    // Sample settings for randomization
    const settings = [
      "Coffee shop in downtown",
      "Beach party",
      "College campus",
      "Music festival",
      "Dating app chat",
      "Work happy hour",
      "Neighbor's BBQ",
      "Book club meeting",
      "Gym class",
      "Airport lounge"
    ];
    
    const goals = [
      "Get a date for Friday night",
      "Make a new friend",
      "Get their phone number",
      "Start a meaningful conversation",
      "Find common interests",
      "Practice social skills",
      "Impress them with your wit",
      "Plan a future meetup",
      "Get to know them better",
      "Just have a fun conversation"
    ];
    
    const scenarioTypes = ["dating", "friendship", "small_talk", "random_deep_talk"];
    const archetypes = [
      "The Icy One",
      "The Awkward Sweetheart",
      "The Certified Baddie",
      "The Philosopher Situationship",
      "The Chaotic Extrovert"
    ];
    const genders = ["male", "female", "non-binary", "other"];
    
    // Generate random values
    const randomValues = {
      scenario_type: scenarioTypes[Math.floor(Math.random() * scenarioTypes.length)],
      setting: settings[Math.floor(Math.random() * settings.length)],
      goal: goals[Math.floor(Math.random() * goals.length)],
      system_archetype: archetypes[Math.floor(Math.random() * archetypes.length)],
      roast_level: Math.floor(Math.random() * 5) + 1,
      player_sex: genders[Math.floor(Math.random() * genders.length)],
      system_sex: genders[Math.floor(Math.random() * genders.length)],
    };
    
    // Set random values in form
    form.reset(randomValues);
    
    toast({
      title: "Random scenario generated!",
      description: "Feel free to modify any values before continuing.",
    });
  };

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    setIsLoading(true);
    try {
      console.log("Submitting scenario data:", values);
      const response = await fetch(`${API_BASE_URL}/api/v1/scenario`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(values),
      });

      if (!response.ok) {
        let errorDetail = "Failed to create scenario.";
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || errorDetail;
        } catch (e) {
          // Ignore if response is not JSON
          errorDetail = await response.text();
        }
        throw new Error(`API Error (${response.status}): ${errorDetail}`);
      }

      const scenarioIdResponse: ScenarioIDResponse = await response.json();
      console.log("Received scenario ID from backend:", scenarioIdResponse.id);

      router.push(`/chat?id=${scenarioIdResponse.id}`);

    } catch (error) {
      console.error("Error submitting scenario:", error);
      toast({
        title: "Submission Failed",
        description: error instanceof Error ? error.message : "Could not connect to the server. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-black/30 backdrop-blur-lg rounded-xl border border-white/10 p-6 shadow-xl">
      <div className="mb-6 text-center">
        <motion.h1 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-2xl md:text-3xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-pink-400 via-purple-400 to-indigo-400"
        >
          Set Your Vibe ✨
        </motion.h1>
        <p className="text-white/70">
          {step === 1 ? 
            "Let's set the scene for your conversation" : 
            "Almost there! A few more details..."}
        </p>
        <Button 
          type="button" 
          onClick={randomizeForm} 
          variant="outline"
          className="mt-2 bg-black/50 border-white/20 text-white hover:bg-white/10"
        >
          <Dices className="mr-2 h-4 w-4" /> Randomize
        </Button>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {step === 1 && (
            <motion.div 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
              className="space-y-6"
            >
              <FormField
                control={form.control}
                name="scenario_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-white">Conversation Type</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger className="bg-black/50 border-white/20 text-white">
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent className="bg-gray-400 border-white/20">
                        <SelectItem value="dating">Dating</SelectItem>
                        <SelectItem value="friendship">Friendship</SelectItem>
                        <SelectItem value="small_talk">Small Talk</SelectItem>
                        <SelectItem value="random_deep_talk">Random Deep Talk</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="setting"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-white">Where's this happening?</FormLabel>
                    <FormControl>
                      <Input 
                        placeholder="Coffee shop, party, Zoom call..." 
                        {...field} 
                        className="bg-black/50 border-white/20 text-white" 
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="goal"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-white">What's your goal?</FormLabel>
                    <FormControl>
                      <Input 
                        placeholder="Get a date, make friends, first impression..." 
                        {...field} 
                        className="bg-black/50 border-white/20 text-white" 
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <div className="flex justify-end pt-4">
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Button 
                    type="button" 
                    onClick={() => goToStep(2)}
                    className="bg-gradient-to-r from-blue-500 to-violet-500 hover:from-blue-600 hover:to-violet-600 text-white"
                  >
                    Next Step <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </motion.div>
              </div>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div 
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              className="space-y-6"
            >
              <FormField
                control={form.control}
                name="system_archetype"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-white">Who are you talking to?</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger className="bg-black/50 border-white/20 text-white">
                          <SelectValue placeholder="Select character archetype" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent className="bg-gray-400 border-white/20">
                        {[
                          "The Icy One",
                          "The Awkward Sweetheart",
                          "The Certified Baddie",
                          "The Philosopher Situationship",
                          "The Chaotic Extrovert"
                        ].map(archetype => (
                          <SelectItem key={archetype} value={archetype}>
                            {archetype}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="roast_level"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-white flex justify-between">
                      <span>Roast Level</span>
                      <span className="text-white/70 text-sm">
                        {field.value === 1 && "Be gentle with me"}
                        {field.value === 2 && "Slight roast"}
                        {field.value === 3 && "Balanced feedback"}
                        {field.value === 4 && "Don't hold back"}
                        {field.value === 5 && "Destroy me completely"}
                      </span>
                    </FormLabel>
                    <FormControl>
                      <Slider
                        defaultValue={[field.value]}
                        max={5}
                        min={1}
                        step={1}
                        onValueChange={(vals) => field.onChange(vals[0])}
                        className="py-4"
                      />
                    </FormControl>
                    <div className="flex justify-between text-xs text-white/50">
                      <span>Gentle</span>
                      <span>Brutal</span>
                    </div>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="player_sex"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-white">Your Gender</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger className="bg-black/50 border-white/20 text-white">
                            <SelectValue placeholder="Select" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent className="bg-gray-400 border-white/20">
                          <SelectItem value="male">Male</SelectItem>
                          <SelectItem value="female">Female</SelectItem>
                          <SelectItem value="non-binary">Non-binary</SelectItem>
                          <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="system_sex"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-white">Their Gender</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger className="bg-black/50 border-white/20 text-white">
                            <SelectValue placeholder="Select" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent className="bg-gray-400 border-white/20">
                          <SelectItem value="male">Male</SelectItem>
                          <SelectItem value="female">Female</SelectItem>
                          <SelectItem value="non-binary">Non-binary</SelectItem>
                          <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="flex justify-between pt-4">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => goToStep(1)}
                  disabled={isLoading}
                  className="bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:bg-white/10 text-white"
                >
                  <ArrowLeft className="mr-2 h-4 w-4" /> Back
                </Button>
                
                <motion.div whileHover={{ scale: isLoading ? 1 : 1.05 }} whileTap={{ scale: isLoading ? 1: 0.95 }}>
                  <Button 
                    type="submit" 
                    disabled={isLoading}
                    className="bg-gradient-to-r from-pink-500 to-purple-600 hover:from-pink-600 hover:to-purple-700 text-white"
                  >
                    {isLoading ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Sparkles className="mr-2 h-4 w-4" />
                    )}
                    {isLoading ? 'Setting up...' : 'Start Chatting'}
                  </Button>
                </motion.div>
              </div>
            </motion.div>
          )}
        </form>
      </Form>
      <p className="text-center text-xs text-white/50 mt-6">
        Confused about archetypes or conversation aspects? 
        <Link href="/faq" className="text-cyan-400 hover:text-cyan-300 underline ml-1">
           Learn more here.
        </Link>
      </p>
    </div>
  );
}