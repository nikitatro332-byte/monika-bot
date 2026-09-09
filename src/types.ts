export type EmotionType = 'calm' | 'happy' | 'thinking' | 'sad' | 'angry' | 'wave' | 'dance';

export type AnimationType = 'idle' | 'wave' | 'dance' | 'happy';

export interface ChatMessage {
  id: string;
  sender: 'user' | 'hori';
  text: string;
  time: string;
  emotion?: EmotionType;
  animation?: AnimationType;
  voiceText?: string;
}

export interface FactItem {
  text: string;
  time: string;
}

export interface UserMemory {
  user_name: string;
  facts: FactItem[];
  interests: string[];
  conversations: Array<{ user: string; hori: string; time: string }>;
  mood: string;
  emotion: EmotionType;
  last_interaction: string | null;
  proactive_sent: string[];
}

export interface DiaryEntry {
  id?: string;
  date: string;
  time?: string;
  mood: string;
  title: string;
  text: string;
  tags?: string[];
}

export interface PersonalityData {
  name: string;
  source_character: string;
  identity_anchors: string[];
  traits: string[];
  speaking_style: {
    tone: string;
    length: string;
    emojis: string;
    language: string;
    vocabulary: string;
    humor: string;
    speech_patterns: string[];
  };
  values: string[];
  quirks: string[];
  emotional_patterns: {
    when_happy: string;
    when_sad: string;
    when_angry: string;
    when_thinking: string;
  };
  interests: string[];
  behavior_rules: string[];
  current_interests: string[];
  evolution_count: number;
}

export interface KnowledgeData {
  character: {
    name: string;
    romanized_name: string;
    series: string;
    school: string;
    family: string[];
    important_relationships: string[];
    public_side: string;
    private_side: string;
    core_conflict: string;
    personality: string[];
  };
  world: {
    setting: string;
    themes: string[];
    spoiler_policy: string;
  };
  response_guidance: {
    use_for: string[];
    do_not_claim: string[];
    memory_priority: string[];
    source_policy: {
      primary: string;
      secondary: string;
      always_check_for: string[];
      rule: string;
      citation: string;
    };
  };
}
