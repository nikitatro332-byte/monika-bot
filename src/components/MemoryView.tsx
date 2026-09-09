import React, { useState } from 'react';
import { Brain, Plus, Trash2, Heart, User, Sparkles, CheckCircle2 } from 'lucide-react';
import { UserMemory } from '../types';

interface MemoryViewProps {
  memory: UserMemory;
  onAddFact: (fact: string) => Promise<void>;
  onRemoveFact: (index: number) => Promise<void>;
  onUpdateUserName: (name: string) => Promise<void>;
}

export const MemoryView: React.FC<MemoryViewProps> = ({
  memory,
  onAddFact,
  onRemoveFact,
  onUpdateUserName,
}) => {
  const [newFact, setNewFact] = useState('');
  const [editingName, setEditingName] = useState(false);
  const [userNameInput, setUserNameInput] = useState(memory.user_name || 'мой любимый');

  const handleFactSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFact.trim()) return;
    await onAddFact(newFact.trim());
    setNewFact('');
  };

  const handleSaveName = async () => {
    await onUpdateUserName(userNameInput.trim() || 'мой любимый');
    setEditingName(false);
  };

  return (
    <div id="memory-view-panel" className="h-full flex flex-col bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl overflow-hidden backdrop-blur-md">
      {/* Header */}
      <div className="px-5 py-3.5 border-b border-slate-800/80 bg-slate-950/40 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Brain className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-100">Память Хори</h2>
            <p className="text-xs text-slate-400">Факты о пользователе, предпочтения и контекст</p>
          </div>
        </div>

        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          <Heart className="w-3.5 h-3.5 fill-rose-500/40" />
          <span>Настроение: {memory.mood || 'спокойное'}</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* User Card */}
        <div className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/70 space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
              <User className="w-4 h-4 text-rose-400" />
              <span>Как Хори называет тебя:</span>
            </div>
            {!editingName && (
              <button
                onClick={() => setEditingName(true)}
                className="text-xs text-rose-400 hover:underline"
              >
                Изменить
              </button>
            )}
          </div>

          {editingName ? (
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={userNameInput}
                onChange={(e) => setUserNameInput(e.target.value)}
                className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-rose-500"
              />
              <button
                onClick={handleSaveName}
                className="px-3 py-1.5 rounded-lg bg-rose-500 text-white text-xs font-semibold"
              >
                Готово
              </button>
            </div>
          ) : (
            <p className="text-sm font-medium text-slate-100 bg-slate-900/60 px-3 py-2 rounded-lg border border-slate-800">
              «{memory.user_name || 'мой любимый'}»
            </p>
          )}
        </div>

        {/* Add Fact Form */}
        <form onSubmit={handleFactSubmit} className="flex gap-2">
          <input
            type="text"
            placeholder="Добавить факт (например: любит чай с мятой)"
            value={newFact}
            onChange={(e) => setNewFact(e.target.value)}
            className="flex-1 bg-slate-800/70 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-rose-500"
          />
          <button
            type="submit"
            disabled={!newFact.trim()}
            className="px-3.5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-medium transition-all disabled:opacity-50 flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Запомнить</span>
          </button>
        </form>

        {/* Facts List */}
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Запомненные факты ({memory.facts?.length || 0}):</span>
          </h3>

          {!memory.facts || memory.facts.length === 0 ? (
            <div className="p-5 rounded-xl border border-dashed border-slate-800 text-center text-xs text-slate-500">
              Хори ещё не записала фактов о тебе. Они будут автоматически добавляться во время разговора, или можно добавить вручную выше.
            </div>
          ) : (
            memory.facts.map((fact, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2.5 rounded-xl bg-slate-800/50 border border-slate-700/60 text-xs text-slate-200"
              >
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                  <span>{fact.text}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-500">{fact.time}</span>
                  <button
                    onClick={() => onRemoveFact(idx)}
                    className="text-slate-500 hover:text-rose-400 p-1"
                    title="Удалить факт"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
