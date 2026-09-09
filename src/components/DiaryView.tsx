import React, { useState } from 'react';
import { BookOpen, Plus, Sparkles, Calendar, Heart, Feather } from 'lucide-react';
import { DiaryEntry } from '../types';

interface DiaryViewProps {
  entries: DiaryEntry[];
  onAddEntry: (entry: Omit<DiaryEntry, 'id'>) => Promise<void>;
  onGenerateDiaryThought: () => Promise<void>;
  isGenerating: boolean;
}

export const DiaryView: React.FC<DiaryViewProps> = ({
  entries,
  onAddEntry,
  onGenerateDiaryThought,
  isGenerating,
}) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newText, setNewText] = useState('');
  const [newMood, setNewMood] = useState('Тёплое');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newText.trim()) return;

    await onAddEntry({
      title: newTitle.trim() || 'Запись без названия',
      text: newText.trim(),
      mood: newMood,
      date: new Date().toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }),
      time: new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }),
    });

    setNewTitle('');
    setNewText('');
    setShowAddForm(false);
  };

  return (
    <div id="diary-view-panel" className="h-full flex flex-col bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl overflow-hidden backdrop-blur-md">
      {/* Header */}
      <div className="px-5 py-3.5 border-b border-slate-800/80 bg-slate-950/40 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-100">Личный дневник Хори</h2>
            <p className="text-xs text-slate-400">Сокровенные мысли, впечатления за день и заметки</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            id="btn-ask-hori-diary"
            onClick={onGenerateDiaryThought}
            disabled={isGenerating}
            className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-rose-500/20 to-amber-500/20 border border-rose-500/40 text-rose-200 text-xs font-medium hover:from-rose-500/30 hover:to-amber-500/30 transition-all flex items-center gap-1.5 disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Пусть Хори напишет</span>
          </button>

          <button
            id="btn-new-diary-entry"
            onClick={() => setShowAddForm(!showAddForm)}
            className="p-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 transition-all"
            title="Добавить запись"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {showAddForm && (
          <form onSubmit={handleSubmit} className="p-4 rounded-xl bg-slate-800/80 border border-slate-700 space-y-3">
            <h3 className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
              <Feather className="w-3.5 h-3.5 text-rose-400" />
              <span>Новая запись в дневник</span>
            </h3>

            <input
              type="text"
              placeholder="Заголовок (например: Сегодняшний ужин)"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-rose-500"
            />

            <textarea
              placeholder="О чем думает Хори сегодня..."
              rows={3}
              value={newText}
              onChange={(e) => setNewText(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-rose-500"
            />

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-[11px] text-slate-400">Настроение:</span>
                <select
                  value={newMood}
                  onChange={(e) => setNewMood(e.target.value)}
                  className="bg-slate-900 border border-slate-700 text-xs text-slate-200 rounded-lg px-2 py-1 focus:outline-none"
                >
                  <option value="Тёплое">Тёплое 🌸</option>
                  <option value="Задумчивое">Задумчивое 💭</option>
                  <option value="Радостное">Радостное ✨</option>
                  <option value="Уставшее">Уставшее ☕</option>
                  <option value="Смущённое">Смущённое 😳</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-3 py-1 rounded-lg text-xs text-slate-400 hover:text-slate-200"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  disabled={!newText.trim()}
                  className="px-3 py-1 rounded-lg text-xs font-semibold bg-rose-500 text-white hover:bg-rose-600 disabled:opacity-50"
                >
                  Сохранить
                </button>
              </div>
            </div>
          </form>
        )}

        {entries.length === 0 ? (
          <div className="h-48 flex flex-col items-center justify-center text-center p-6 text-slate-400">
            <BookOpen className="w-8 h-8 text-slate-600 mb-2" />
            <p className="text-xs text-slate-400">В дневнике пока нет записей.</p>
            <p className="text-[11px] text-slate-500 mt-1">
              Нажми «Пусть Хори напишет», чтобы она поделилась своими мыслями!
            </p>
          </div>
        ) : (
          entries.map((entry, idx) => (
            <div
              key={entry.id || idx}
              className="p-4 rounded-xl bg-slate-800/60 border border-slate-700/70 hover:border-slate-600 transition-all space-y-2"
            >
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-semibold text-slate-100">{entry.title}</h4>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20">
                  {entry.mood}
                </span>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap font-sans">
                {entry.text}
              </p>

              <div className="flex items-center justify-between pt-2 border-t border-slate-700/50 text-[10px] text-slate-500">
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  <span>{entry.date} {entry.time ? `• ${entry.time}` : ''}</span>
                </div>
                <div className="flex items-center gap-1 text-rose-400/80">
                  <Heart className="w-3 h-3 fill-rose-500/20" />
                  <span>Хори</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
