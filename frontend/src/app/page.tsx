"use client";

import { useState } from "react";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import DashboardView from "../components/DashboardView";
import AnalyticsView from "../components/AnalyticsView";
import InsightsView from "../components/InsightsView";
import UploadView from "../components/UploadView";
import TariffView from "../components/TariffView";

export default function Home() {
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [refreshKey, setRefreshKey] = useState<number>(0);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false);

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <div className="flex min-h-screen bg-slate-950">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onRefresh={handleRefresh}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 p-4 sm:p-6 lg:p-8 overflow-y-auto">
        <Header
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          onNotificationAction={handleRefresh}
        />

        <div className="flex-1">
          {activeTab === "upload" && <UploadView onDataImported={handleRefresh} />}
          {activeTab === "dashboard" && <DashboardView refreshTrigger={refreshKey} />}
          {activeTab === "analytics" && <AnalyticsView refreshTrigger={refreshKey} />}
          {activeTab === "insights" && <InsightsView refreshTrigger={refreshKey} />}
          {activeTab === "tariff" && <TariffView onTariffUpdated={handleRefresh} />}
        </div>

        <footer className="mt-12 pt-6 border-t border-white/10 text-center text-xs text-slate-400">
          🚀 AI-Powered Smart Campus Energy Analytics System &nbsp;|&nbsp; Next.js Frontend & FastAPI Backend
        </footer>
      </main>
    </div>
  );
}
