export interface ScenarioData {
  id: string;
  type: string;
  setting: string;
  goal: string;
  system_archetype: string;
  roast_level: number;
  player_sex: string;
  system_sex: string;
}

export interface ScenarioIDResponse {
  id: string;
}

export interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'system';
  timestamp: string;
}