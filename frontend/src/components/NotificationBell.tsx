"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import {
  Bell,
  Check,
  CheckCheck,
  AlertTriangle,
  AlertCircle,
  Info,
  RefreshCw,
  X,
  Building2,
  Calendar,
  Zap,
  ShieldCheck,
  ChevronRight
} from "lucide-react";
import { api } from "../lib/api";
import { NotificationItem, NotificationSeverity } from "../types/api";

interface NotificationBellProps {
  onNotificationAction?: () => void;
}

export default function NotificationBell({ onNotificationAction }: NotificationBellProps) {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [scanning, setScanning] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "unread" | "critical" | "anomalies">("all");
  const panelRef = useRef<HTMLDivElement>(null);

  // Fetch unread count for badge
  const fetchUnreadCount = useCallback(async () => {
    const res = await api.getUnreadCount();
    if (res.data) {
      setUnreadCount(res.data.unread_count);
    }
  }, []);

  // Fetch notifications list
  const fetchNotifications = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true);
    setError(null);
    try {
      const res = await api.getNotifications({ limit: 40 });
      if (res.data) {
        setNotifications(res.data.items);
        setUnreadCount(res.data.unread_count);
      } else if (res.error) {
        setError(res.error);
      }
    } catch (e: any) {
      setError(e?.message || "Failed to load notifications");
    } finally {
      if (showLoading) setLoading(false);
    }
  }, []);

  // Initial load and periodic 30-second polling
  useEffect(() => {
    fetchUnreadCount();
    const intervalId = setInterval(() => {
      fetchUnreadCount();
      if (isOpen) {
        fetchNotifications(false);
      }
    }, 30000);

    return () => clearInterval(intervalId);
  }, [fetchUnreadCount, fetchNotifications, isOpen]);

  // When panel opens, fetch latest list
  useEffect(() => {
    if (isOpen) {
      fetchNotifications(true);
    }
  }, [isOpen, fetchNotifications]);

  // Handle outside click & escape key
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  // Run manual scan
  const handleRunScan = async () => {
    setScanning(true);
    setError(null);
    try {
      const res = await api.runNotificationCheck({ peak_threshold_pct: 30.0, surge_std_dev: 2.0 });
      if (res.data) {
        await fetchNotifications(false);
        if (onNotificationAction) onNotificationAction();
      } else if (res.error) {
        setError(res.error);
      }
    } catch (e: any) {
      setError(e?.message || "Scan failed");
    } finally {
      setScanning(false);
    }
  };

  // Mark single notification as read
  const handleMarkAsRead = async (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    try {
      const res = await api.markNotificationAsRead(id);
      if (res.data && res.data.success) {
        setNotifications((prev) =>
          prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
        );
        setUnreadCount(res.data.unread_count);
        if (onNotificationAction) onNotificationAction();
      }
    } catch (_) {}
  };

  // Mark all as read
  const handleMarkAllAsRead = async () => {
    try {
      const res = await api.markAllNotificationsAsRead();
      if (res.data && res.data.success) {
        setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
        setUnreadCount(0);
        if (onNotificationAction) onNotificationAction();
      }
    } catch (_) {}
  };

  // Filtered notifications
  const filteredNotifications = notifications.filter((item) => {
    if (filter === "unread") return !item.is_read;
    if (filter === "critical") return item.severity === "critical";
    if (filter === "anomalies") return item.notification_type === "anomaly";
    return true;
  });

  const getSeverityBadge = (severity: NotificationSeverity) => {
    switch (severity) {
      case "critical":
        return {
          icon: <AlertTriangle size={15} className="text-rose-400 shrink-0" />,
          border: "border-rose-500/30",
          bg: "bg-rose-950/25",
          badge: "bg-rose-500/20 text-rose-300 border-rose-500/40",
          dot: "bg-rose-500 shadow-rose-500/50",
        };
      case "warning":
        return {
          icon: <AlertCircle size={15} className="text-amber-400 shrink-0" />,
          border: "border-amber-500/30",
          bg: "bg-amber-950/25",
          badge: "bg-amber-500/20 text-amber-300 border-amber-500/40",
          dot: "bg-amber-500 shadow-amber-500/50",
        };
      default:
        return {
          icon: <Info size={15} className="text-sky-400 shrink-0" />,
          border: "border-sky-500/30",
          bg: "bg-sky-950/25",
          badge: "bg-sky-500/20 text-sky-300 border-sky-500/40",
          dot: "bg-sky-400 shadow-sky-400/50",
        };
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case "high_consumption":
        return "Campus Peak";
      case "baseline_surge":
        return "Baseline Surge";
      default:
        return "Anomaly Alert";
    }
  };

  return (
    <div className="relative" ref={panelRef}>
      {/* Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-label="View notifications and energy alerts"
        className={`relative p-2.5 rounded-xl border transition-all duration-200 flex items-center justify-center ${
          isOpen
            ? "bg-sky-500/20 border-sky-400/50 text-sky-300 shadow-lg shadow-sky-500/10"
            : "bg-slate-900/60 hover:bg-slate-800/80 border-white/10 text-slate-300 hover:text-white"
        }`}
      >
        <Bell size={20} className={unreadCount > 0 ? "animate-pulse text-sky-400" : ""} />

        {/* Unread badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1.5 -right-1.5 min-w-[20px] h-5 px-1.5 text-[11px] font-bold rounded-full bg-gradient-to-r from-rose-500 to-amber-500 text-white flex items-center justify-center shadow-md shadow-rose-500/30 ring-2 ring-slate-950">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Notifications Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-3 w-[92vw] sm:w-[460px] md:w-[500px] max-h-[85vh] flex flex-col rounded-2xl bg-slate-950/95 backdrop-blur-2xl border border-white/15 shadow-2xl shadow-black/60 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
          {/* Header */}
          <div className="p-4 border-b border-white/10 bg-gradient-to-r from-slate-900/90 to-slate-950 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
                <Zap size={18} />
              </div>
              <div>
                <h3 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                  Energy Alerts
                  {unreadCount > 0 ? (
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30">
                      {unreadCount} unread
                    </span>
                  ) : (
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      All clear
                    </span>
                  )}
                </h3>
                <p className="text-[11px] text-slate-400">
                  Campus anomaly & consumption monitors
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1.5">
              {/* Scan Now button */}
              <button
                onClick={handleRunScan}
                disabled={scanning}
                title="Run real-time alert scan across campus data"
                className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white border border-white/10 text-xs flex items-center gap-1.5 transition-all disabled:opacity-50"
              >
                <RefreshCw size={13} className={scanning ? "animate-spin text-sky-400" : ""} />
                <span className="hidden sm:inline text-[11px]">Scan</span>
              </button>

              {/* Mark All Read button */}
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllAsRead}
                  title="Mark all notifications as read"
                  className="p-1.5 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 border border-sky-500/30 text-xs flex items-center gap-1 transition-all"
                >
                  <CheckCheck size={14} />
                  <span className="hidden sm:inline text-[11px]">Mark All Read</span>
                </button>
              )}

              {/* Close button */}
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
              >
                <X size={15} />
              </button>
            </div>
          </div>

          {/* Filter Pills */}
          <div className="px-4 py-2.5 border-b border-white/5 bg-slate-900/50 flex items-center gap-1.5 overflow-x-auto scrollbar-none text-xs">
            <button
              onClick={() => setFilter("all")}
              className={`px-3 py-1 rounded-full font-medium transition-colors ${
                filter === "all"
                  ? "bg-sky-500 text-white shadow-sm shadow-sky-500/30"
                  : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-slate-200"
              }`}
            >
              All ({notifications.length})
            </button>
            <button
              onClick={() => setFilter("unread")}
              className={`px-3 py-1 rounded-full font-medium transition-colors ${
                filter === "unread"
                  ? "bg-sky-500 text-white shadow-sm shadow-sky-500/30"
                  : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-slate-200"
              }`}
            >
              Unread ({unreadCount})
            </button>
            <button
              onClick={() => setFilter("critical")}
              className={`px-3 py-1 rounded-full font-medium transition-colors ${
                filter === "critical"
                  ? "bg-rose-500 text-white shadow-sm shadow-rose-500/30"
                  : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-slate-200"
              }`}
            >
              Critical ({notifications.filter((n) => n.severity === "critical").length})
            </button>
            <button
              onClick={() => setFilter("anomalies")}
              className={`px-3 py-1 rounded-full font-medium transition-colors ${
                filter === "anomalies"
                  ? "bg-indigo-500 text-white shadow-sm shadow-indigo-500/30"
                  : "bg-white/5 text-slate-400 hover:bg-white/10 hover:text-slate-200"
              }`}
            >
              Anomalies ({notifications.filter((n) => n.notification_type === "anomaly").length})
            </button>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="mx-4 my-2 p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center justify-between">
              <span>{error}</span>
              <button
                onClick={() => fetchNotifications(true)}
                className="underline hover:text-white font-semibold ml-2"
              >
                Retry
              </button>
            </div>
          )}

          {/* Notification List Scroll Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2.5 max-h-[55vh] divide-y divide-white/5">
            {loading ? (
              // Loading Skeleton
              <div className="space-y-3 py-2">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="p-3.5 rounded-xl bg-white/5 border border-white/5 animate-pulse space-y-2"
                  >
                    <div className="flex justify-between items-center">
                      <div className="h-4 bg-white/10 rounded w-1/3"></div>
                      <div className="h-3 bg-white/10 rounded w-1/5"></div>
                    </div>
                    <div className="h-3 bg-white/10 rounded w-full"></div>
                    <div className="h-3 bg-white/10 rounded w-2/3"></div>
                  </div>
                ))}
              </div>
            ) : filteredNotifications.length === 0 ? (
              // Empty State
              <div className="py-10 text-center flex flex-col items-center justify-center space-y-2.5">
                <div className="p-3.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <ShieldCheck size={28} />
                </div>
                <h4 className="text-sm font-semibold text-white">
                  No {filter !== "all" ? `${filter} ` : ""}alerts found
                </h4>
                <p className="text-xs text-slate-400 max-w-xs">
                  {filter === "unread"
                    ? "All campus energy alerts have been reviewed."
                    : "Campus energy consumption is operating within standard baseline thresholds."}
                </p>
                {notifications.length === 0 && (
                  <button
                    onClick={handleRunScan}
                    disabled={scanning}
                    className="mt-2 px-3 py-1.5 rounded-lg bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-500/40 text-xs font-medium transition-all"
                  >
                    Run Detection Check
                  </button>
                )}
              </div>
            ) : (
              // Notification items
              filteredNotifications.map((item) => {
                const s = getSeverityBadge(item.severity);
                return (
                  <div
                    key={item.id}
                    onClick={() => !item.is_read && handleMarkAsRead(item.id)}
                    className={`pt-2.5 first:pt-0 group relative p-3 rounded-xl border transition-all duration-200 cursor-pointer ${
                      s.border
                    } ${s.bg} ${
                      !item.is_read
                        ? "shadow-sm hover:border-sky-400/50 ring-1 ring-white/10"
                        : "opacity-75 hover:opacity-100 hover:border-white/20"
                    }`}
                  >
                    {/* Top Row: Severity, Type, Building, Date */}
                    <div className="flex items-start justify-between gap-2 mb-1.5">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {s.icon}
                        <span
                          className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${s.badge}`}
                        >
                          {item.severity}
                        </span>
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-white/10 text-slate-300 border border-white/10">
                          {getTypeLabel(item.notification_type)}
                        </span>
                        <span className="text-xs font-semibold text-white flex items-center gap-1">
                          <Building2 size={12} className="text-slate-400" />
                          {item.building}
                        </span>
                      </div>

                      <div className="flex items-center gap-1.5 shrink-0">
                        {item.detection_date && (
                          <span className="text-[11px] text-slate-400 flex items-center gap-1">
                            <Calendar size={11} />
                            {item.detection_date}
                          </span>
                        )}
                        {!item.is_read ? (
                          <button
                            onClick={(e) => handleMarkAsRead(item.id, e)}
                            title="Mark as read"
                            className="p-1 rounded-md bg-white/5 hover:bg-sky-500/20 text-slate-400 hover:text-sky-300 transition-colors"
                          >
                            <Check size={13} />
                          </button>
                        ) : (
                          <span className="text-[10px] text-slate-500 font-medium">Read</span>
                        )}
                      </div>
                    </div>

                    {/* Title */}
                    <h5 className="text-xs sm:text-sm font-semibold text-slate-100 group-hover:text-sky-300 transition-colors">
                      {item.title}
                    </h5>

                    {/* Message */}
                    <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                      {item.message}
                    </p>

                    {/* Metrics / Observed Deviation footer */}
                    {(item.observed_kwh != null || item.metric_deviation_pct != null) && (
                      <div className="mt-2.5 pt-2 border-t border-white/5 flex items-center gap-3 text-[11px] text-slate-400 flex-wrap">
                        {item.observed_kwh != null && (
                          <span>
                            Observed:{" "}
                            <strong className="text-slate-200">
                              {item.observed_kwh.toLocaleString()} kWh
                            </strong>
                          </span>
                        )}
                        {item.baseline_kwh != null && (
                          <span>
                            Baseline:{" "}
                            <span className="text-slate-300">
                              {item.baseline_kwh.toLocaleString()} kWh
                            </span>
                          </span>
                        )}
                        {item.metric_deviation_pct != null && (
                          <span
                            className={
                              item.metric_deviation_pct > 0
                                ? "text-rose-400 font-semibold"
                                : "text-emerald-400 font-semibold"
                            }
                          >
                            {item.metric_deviation_pct > 0 ? "+" : ""}
                            {item.metric_deviation_pct.toFixed(1)}% variance
                          </span>
                        )}
                        {item.metadata?.detection_method && (
                          <span className="text-slate-500 text-[10px] italic">
                            via {item.metadata.detection_method}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>

          {/* Footer */}
          <div className="p-3 border-t border-white/10 bg-slate-900/80 text-center text-[11px] text-slate-400 flex items-center justify-between">
            <span>Deduplicated anomaly & campus threshold monitor</span>
            <span className="text-slate-500 text-[10px]">Updates every 30s</span>
          </div>
        </div>
      )}
    </div>
  );
}
