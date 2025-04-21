'use client';

import { ScenarioForm } from '@/components/scenario-form';
import { FloatingEmojis } from '@/components/ui/floating-emojis';

export default function ScenarioPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-violet-800 to-indigo-900 flex items-center justify-center p-4 overflow-hidden">
      <FloatingEmojis />
      <div className="w-full max-w-lg">
        <ScenarioForm />
      </div>
    </div>
  );
}