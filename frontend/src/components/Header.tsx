"use client";

import { Menu } from "lucide-react";
import NotificationBell from "./NotificationBell";

interface HeaderProps {
  onToggleSidebar?: () => void;
  onNotificationAction?: () => void;
}

export default function Header({ onToggleSidebar, onNotificationAction }: HeaderProps) {
  return (
    <header className="mb-8 flex items-center justify-between pb-6 border-b border-white/10 gap-4">
      <div className="flex items-center gap-4 min-w-0">
        {onToggleSidebar && (
          <button
            onClick={onToggleSidebar}
            aria-label="Toggle navigation menu"
            className="p-2 md:hidden rounded-lg bg-white/5 hover:bg-white/10 text-sky-400 border border-white/10 transition-colors shrink-0"
          >
            <Menu size={20} />
          </button>
        )}
        <div className="min-w-0">
          <h1 className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-sky-400 via-cyan-300 to-indigo-300 tracking-tight truncate">
            ⚡ Smart Campus Energy AI Dashboard
          </h1>
          <p className="text-slate-400 text-xs sm:text-sm mt-0.5 font-normal truncate">
            Predict • Analyze • Optimize Energy Usage
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 shrink-0">
        <NotificationBell onNotificationAction={onNotificationAction} />
      </div>
    </header>
  );
}

