import React from 'react';
import { UserCheck, Sparkles, Shield, Compass, BookOpen, ExternalLink } from 'lucide-react';
import { PersonalityData, KnowledgeData } from '../types';

interface PersonalityKnowledgeViewProps {
  personality: PersonalityData | null;
  knowledge: KnowledgeData | null;
}

export const PersonalityKnowledgeView: React.FC<PersonalityKnowledgeViewProps> = ({
  personality,
  knowledge,
}) => {
  return (
    <div id="personality-knowledge-panel" className="h-full flex flex-col bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl overflow-hidden backdrop-blur-md">
      {/* Header */}
      <div className="px-5 py-3.5 border-b border-slate-800/80 bg-slate-950/40 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-100">Личность и Канон</h2>
            <p className="text-xs text-slate-400">Характер Хори Кёко, манера общения и канон Horimiya</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Character Identity Card */}
        <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/70 space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-rose-400 uppercase tracking-wider">Персонаж</span>
            <span className="text-xs text-slate-400">Horimiya • {knowledge?.character.romanized_name || 'Hori Kyouko'}</span>
          </div>

          <h3 className="text-base font-bold text-slate-100">{personality?.name || 'Хори Кёко'}</h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            {knowledge?.character.public_side || 'Популярная, аккуратная и уверенная ученица в школе Катагири.'}
          </p>
          <div className="p-2.5 rounded-lg bg-slate-900/70 border border-slate-800 text-xs text-slate-400 italic">
            «{knowledge?.character.private_side || 'Дома заботится о младшем брате Соте, готовит, убирает и выглядит проще, чем в школе.'}»
          </div>
        </div>

        {/* Character Traits */}
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Черты характера:</span>
          </h4>
          <div className="flex flex-wrap gap-1.5">
            {(personality?.traits || ['общительная', 'энергичная', 'заботливая', 'прямая', 'ответственная']).map((trait, i) => (
              <span
                key={i}
                className="px-2.5 py-1 rounded-lg text-xs bg-slate-800/90 border border-slate-700 text-slate-200"
              >
                {trait}
              </span>
            ))}
          </div>
        </div>

        {/* Speaking Style & Rules */}
        <div className="space-y-2 p-3.5 rounded-xl bg-slate-800/40 border border-slate-700/50">
          <h4 className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <UserCheck className="w-3.5 h-3.5 text-rose-400" />
            <span>Манера общения:</span>
          </h4>
          <ul className="text-xs text-slate-400 space-y-1.5 list-disc list-inside">
            <li>Тон: {personality?.speaking_style.tone || 'живой, прямой, тёплый, иногда резкий и смешной'}</li>
            <li>Язык: разговорный русский, без сухого канцелярита</li>
            <li>Реакции: заботится конкретными делами, может добродушно поворчать при волнении</li>
            <li>Осознание: всегда отвечает от первого лица как Хори Кёко</li>
          </ul>
        </div>

        {/* Sources & Canon */}
        <div className="p-3.5 rounded-xl bg-slate-800/40 border border-slate-700/50 space-y-2 text-xs">
          <div className="flex items-center gap-1.5 font-semibold text-slate-300">
            <BookOpen className="w-3.5 h-3.5 text-sky-400" />
            <span>Источники канона:</span>
          </div>
          <div className="flex flex-col gap-1 text-[11px] text-sky-400">
            <a
              href="https://en.wikipedia.org/wiki/Horimiya"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 hover:underline"
            >
              <span>Wikipedia: Horimiya (English)</span>
              <ExternalLink className="w-3 h-3" />
            </a>
            <a
              href="https://ru.wikipedia.org/wiki/Хоримия"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 hover:underline"
            >
              <span>Википедия: Хоримия (Русский)</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};
