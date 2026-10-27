"use client";

import {
  UploadCloud,
  LayoutDashboard,
  LineChart,
  Lightbulb,
  Calculator,
  X,
} from "lucide-react";

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onRefresh?: () => void;
  isOpen?: boolean;
  onClose?: () => void;
}

export default function Sidebar({
  activeTab,
  setActiveTab,
  isOpen = false,
  onClose,
}: SidebarProps) {
  const navItems = [
    { id: "upload", label: "Upload Data", icon: UploadCloud, badge: "CSV / XLSX" },
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "analytics", label: "Analytics", icon: LineChart, badge: "ML Models" },
    { id: "insights", label: "Insights", icon: Lightbulb, badge: "Savings" },
    { id: "tariff", label: "Tariff Calculator", icon: Calculator, badge: "Slabs" },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden transition-opacity"
        />
      )}

      <aside
        className={`fixed md:sticky top-0 left-0 z-50 h-screen w-72 bg-slate-950/95 backdrop-blur-xl border-r border-white/10 p-6 flex flex-col justify-between transition-transform duration-300 ease-in-out ${
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        <div>
          {/* Top Header & Branding */}
          <div className="flex items-center justify-between pb-5 border-b border-white/10 mb-8">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-500 flex items-center justify-center font-bold text-lg text-white shadow-lg shadow-sky-500/25">
                ⚡
              </div>
              <div>
                <div className="font-bold text-slate-100 text-sm tracking-wide">
                  Smart Energy AI
                </div>
                <div className="text-xs text-sky-400 font-medium">Campus Analytics</div>
              </div>
            </div>
            {onClose && (
              <button
                onClick={onClose}
                aria-label="Close sidebar"
                className="p-1.5 rounded-lg text-slate-400 hover:text-white md:hidden"
              >
                <X size={20} />
              </button>
            )}
          </div>

          {/* Navigation Section */}
          <div>
            <div className="text-xs uppercase tracking-wider font-semibold text-slate-400 mb-4 px-2">
              Navigation
            </div>
            <nav className="flex flex-col gap-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      setActiveTab(item.id);
                      if (onClose) onClose();
                    }}
                    className={`flex items-center justify-between px-4 py-3 rounded-xl font-medium text-sm transition-all duration-200 ${
                      isActive
                        ? "bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-md shadow-sky-500/10 font-semibold"
                        : "text-slate-300 hover:text-white hover:bg-white/5 border border-transparent"
                    }`}
                  >
                    <div className="flex items-center gap-3.5">
                      <Icon size={19} className={isActive ? "text-sky-400" : "text-slate-400"} />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                          isActive
                            ? "bg-sky-500/20 text-sky-300"
                            : "bg-white/5 text-slate-400"
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Clean Balanced Footer */}
        <div className="pt-5 border-t border-white/10 text-center text-xs text-slate-400">
          Smart Campus AI • Next.js & FastAPI
        </div>
      </aside>
    </>
  );
}
