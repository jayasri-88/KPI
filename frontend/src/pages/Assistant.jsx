import React, { useState, useEffect, useRef } from "react";
import {
  Bot,
  Sparkles,
  Send,
  Terminal,
  Wrench,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Database,
  ArrowRight,
  TrendingUp,
  Store,
  Package,
  Users,
  Calendar,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import { sendAgentChat, clearAgentConversation } from "../services/api";

export default function Assistant() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "### Welcome to Autonomous AI Retail Analyst\n\nI am your enterprise intelligence assistant powered by **LangGraph**, **Gemini 3.5**, and direct **PostgreSQL / PostGIS** analytics tools. I do not invent or hallucinate metrics.\n\nEvery answer is computed from verified database transactions and predictive ML models.\n\nHow can I assist your retail operations today?",
      tools_used: [],
      data: [],
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [openRawDataIndices, setOpenRawDataIndices] = useState({});

  const messagesEndRef = useRef(null);

  const samplePrompts = [
    { text: "Which store generated the highest revenue?", icon: Store },
    { text: "Forecast sales for the next 30 days.", icon: TrendingUp },
    { text: "Which store has the lowest profit margin?", icon: AlertTriangle },
    { text: "Which products are performing poorly?", icon: Package },
    { text: "Compare Indiranagar and Bandra stores.", icon: Store },
    { text: "Why did revenue fall last month?", icon: Calendar },
    { text: "What were our sales last month?", icon: TrendingUp },
    { text: "Compare Vizag and Hyderabad stores.", icon: Store },
  ];

  const agentToolsCatalog = [
    { name: "get_sales_kpi", desc: "Queries real-time consolidated revenue, profit, margins, and AOV" },
    { name: "get_store_performance", desc: "Ranks physical retail stores by target achievement and metrics" },
    { name: "get_product_performance", desc: "Retrieves top and bottom performing product SKUs" },
    { name: "get_customer_metrics", desc: "Inspects VIP, Regular, and At-Risk cohort dynamics" },
    { name: "get_sales_trend", desc: "Aggregates daily, weekly, and monthly time-series buckets" },
    { name: "forecast_sales", desc: "Executes Prophet ML demand projection engine (7d & 30d)" },
    { name: "compare_stores", desc: "Executes head-to-head comparison between 2+ retail stores" },
    { name: "compare_periods", desc: "Computes period-over-period growth and variance analytics" },
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const toggleRawData = (idx) => {
    setOpenRawDataIndices((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const handleSendMessage = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    setError(null);
    setInput("");

    // Append user message immediately
    const userMsg = {
      role: "user",
      content: query.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const response = await sendAgentChat(query.trim(), conversationId);
      if (response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      const botMsg = {
        role: "assistant",
        content: response.answer,
        tools_used: response.tools_used || [],
        data: response.data || [],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error("AI Analyst Error:", err);
      const errText =
        err.response?.data?.detail ||
        err.message ||
        "Failed to reach AI Retail Analyst. Please check your backend connection.";
      setError(errText);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `⚠️ **Analyst Execution Error:** ${errText}\n\nPlease try again or select one of the verified sample questions.`,
          tools_used: [],
          data: [],
          isError: true,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleResetConversation = async () => {
    if (conversationId) {
      try {
        await clearAgentConversation(conversationId);
      } catch (e) {
        console.warn("Could not clear backend session:", e);
      }
    }
    setConversationId(null);
    setMessages([
      {
        role: "assistant",
        content:
          "### Conversation Reset Complete\n\nSession memory cleared. Ask me any retail intelligence question or choose from the suggested prompts below.",
        tools_used: [],
        data: [],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
  };

  // Helper function to render markdown-like text cleanly
  const renderFormattedContent = (content) => {
    if (!content) return null;

    const lines = content.split("\n");
    return (
      <div className="space-y-2 text-sm leading-relaxed">
        {lines.map((line, i) => {
          const trimmed = line.trim();

          // Heading 3 / Section Title
          if (trimmed.startsWith("### ")) {
            return (
              <h3
                key={i}
                className="text-base font-bold text-indigo-300 mt-3 mb-1 border-b border-slate-700/50 pb-1 flex items-center gap-2"
              >
                <Sparkles className="w-4 h-4 text-indigo-400" />
                {trimmed.replace("### ", "")}
              </h3>
            );
          }

          // Heading 2
          if (trimmed.startsWith("## ")) {
            return (
              <h2
                key={i}
                className="text-lg font-bold text-white mt-4 mb-2 flex items-center gap-2"
              >
                {trimmed.replace("## ", "")}
              </h2>
            );
          }

          // Bullet points
          if (trimmed.startsWith("* ") || trimmed.startsWith("- ")) {
            const text = trimmed.substring(2);
            return (
              <div key={i} className="flex items-start gap-2 pl-2 my-1">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-2 flex-shrink-0" />
                <span
                  className="text-slate-200"
                  dangerouslySetInnerHTML={{
                    __html: text.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>'),
                  }}
                />
              </div>
            );
          }

          // Numbered lists
          if (/^\d+\.\s/.test(trimmed)) {
            const match = trimmed.match(/^(\d+)\.\s(.*)/);
            return (
              <div key={i} className="flex items-start gap-2 pl-2 my-1">
                <span className="text-xs font-mono font-bold text-indigo-400 mt-0.5 flex-shrink-0">
                  {match[1]}.
                </span>
                <span
                  className="text-slate-200"
                  dangerouslySetInnerHTML={{
                    __html: match[2].replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>'),
                  }}
                />
              </div>
            );
          }

          // Empty line
          if (!trimmed) {
            return <div key={i} className="h-1.5" />;
          }

          // Regular paragraph with bold support
          return (
            <p
              key={i}
              className="text-slate-200"
              dangerouslySetInnerHTML={{
                __html: trimmed.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>'),
              }}
            />
          );
        })}
      </div>
    );
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-8">
      {/* Top Header Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Bot className="w-7 h-7 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white tracking-tight">Autonomous AI Retail Analyst</h1>
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                Live LangGraph + Gemini
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Grounded in live PostgreSQL queries, PostGIS geospatial distance, and Prophet forecasting. Zero hallucinations.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-end md:self-center">
          <button
            onClick={handleResetConversation}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-750 text-slate-300 hover:text-white rounded-lg text-xs font-medium border border-slate-700 transition-colors cursor-pointer"
            title="Clear conversation session"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reset Chat</span>
          </button>
        </div>
      </div>

      {/* Suggested Executive Prompts Carousel */}
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 shadow-md space-y-2.5">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Executive Prompts (Click to Run):
          </span>
          <span className="text-[11px] text-slate-500">Safe typed tool executions</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          {samplePrompts.map((p, idx) => {
            const Icon = p.icon;
            return (
              <button
                key={idx}
                onClick={() => handleSendMessage(p.text)}
                disabled={loading}
                className="p-2.5 bg-slate-950/80 hover:bg-indigo-950/40 border border-slate-800 hover:border-indigo-500/40 rounded-xl text-left text-xs text-slate-300 hover:text-white transition-all flex items-center justify-between group cursor-pointer disabled:opacity-50"
              >
                <div className="flex items-center gap-2 overflow-hidden">
                  <Icon className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                  <span className="truncate">{p.text}</span>
                </div>
                <ArrowRight className="w-3 h-3 text-slate-600 group-hover:text-indigo-400 transition-colors flex-shrink-0 ml-1" />
              </button>
            );
          })}
        </div>
      </div>

      {/* Chat Conversation Thread */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 sm:p-6 shadow-xl space-y-5 min-h-[460px] max-h-[640px] overflow-y-auto">
        {messages.map((msg, index) => {
          const isUser = msg.role === "user";
          return (
            <div
              key={index}
              className={`flex gap-3.5 ${isUser ? "flex-row-reverse" : "flex-row"}`}
            >
              {/* Avatar */}
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 text-sm font-semibold shadow-md ${
                  isUser
                    ? "bg-indigo-600 text-white"
                    : msg.isError
                    ? "bg-rose-600/20 text-rose-400 border border-rose-500/30"
                    : "bg-slate-800 text-indigo-400 border border-slate-700"
                }`}
              >
                {isUser ? "You" : <Bot className="w-5 h-5 text-indigo-400" />}
              </div>

              {/* Message Bubble Container */}
              <div
                className={`max-w-[85%] sm:max-w-[78%] space-y-2 ${
                  isUser ? "items-end text-right" : "items-start text-left"
                }`}
              >
                {/* Header (Role & Time) */}
                <div className={`flex items-center gap-2 text-[11px] text-slate-400 ${isUser ? "justify-end" : "justify-start"}`}>
                  <span className="font-semibold text-slate-300">
                    {isUser ? "You" : "Retail Analyst"}
                  </span>
                  <span>•</span>
                  <span>{msg.timestamp}</span>
                </div>

                {/* Message Body */}
                <div
                  className={`p-4 rounded-2xl text-left text-sm ${
                    isUser
                      ? "bg-indigo-600 text-white rounded-tr-none shadow-md"
                      : msg.isError
                      ? "bg-rose-950/30 border border-rose-800/60 text-rose-200 rounded-tl-none shadow-md"
                      : "bg-slate-950/80 border border-slate-800/80 text-slate-200 rounded-tl-none shadow-lg"
                  }`}
                >
                  {/* Tool invocation badges */}
                  {!isUser && msg.tools_used && msg.tools_used.length > 0 && (
                    <div className="mb-3 pb-3 border-b border-slate-800/80">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1 mr-1">
                          <Wrench className="w-3 h-3 text-indigo-400" /> Tools Called:
                        </span>
                        {msg.tools_used.map((tool, tIdx) => (
                          <span
                            key={tIdx}
                            className="px-2 py-0.5 rounded-md bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 font-mono text-[11px]"
                          >
                            {tool}()
                          </span>
                        ))}
                        {msg.data && msg.data.length > 0 && (
                          <button
                            onClick={() => toggleRawData(index)}
                            className="ml-auto text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center gap-1 hover:underline cursor-pointer"
                          >
                            <Database className="w-3 h-3" />
                            <span>{openRawDataIndices[index] ? "Hide Data" : "Inspect Data"}</span>
                            {openRawDataIndices[index] ? (
                              <ChevronUp className="w-3 h-3" />
                            ) : (
                              <ChevronDown className="w-3 h-3" />
                            )}
                          </button>
                        )}
                      </div>

                      {/* Collapsible raw data preview */}
                      {openRawDataIndices[index] && msg.data && (
                        <div className="mt-2.5 p-2.5 bg-slate-900 border border-slate-800 rounded-lg text-xs font-mono text-slate-300 max-h-48 overflow-y-auto">
                          <div className="flex items-center justify-between text-[10px] text-slate-400 mb-1 border-b border-slate-800 pb-1">
                            <span className="flex items-center gap-1">
                              <Terminal className="w-3 h-3 text-emerald-400" /> Live PostgreSQL Tool Output
                            </span>
                            <span>{msg.data.length} tool payloads</span>
                          </div>
                          <pre className="text-[11px] leading-tight text-emerald-400/90 whitespace-pre-wrap">
                            {JSON.stringify(msg.data, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Main message content */}
                  {isUser ? (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    renderFormattedContent(msg.content)
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {/* Loading / Thinking State */}
        {loading && (
          <div className="flex gap-3.5 items-start">
            <div className="w-9 h-9 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center flex-shrink-0">
              <Bot className="w-5 h-5 text-indigo-400 animate-bounce" />
            </div>
            <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-2xl rounded-tl-none space-y-2 shadow-lg max-w-[70%]">
              <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>LangGraph State Graph executing...</span>
              </div>
              <p className="text-[11px] text-slate-400 leading-normal">
                Selecting domain analytics tool → querying PostgreSQL / PostGIS → synthesizing verified metrics...
              </p>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div className="bg-indigo-500 h-full w-2/3 animate-pulse rounded-full"></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Composer Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSendMessage();
        }}
        className="relative"
      >
        <div className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder="Ask a question about your revenue, stores, products, or forecast (e.g., 'Which store generated the highest revenue?')..."
            className="w-full bg-slate-900 border border-slate-800 focus:border-indigo-500 rounded-2xl pl-5 pr-28 py-4 text-sm text-slate-100 placeholder-slate-500 shadow-xl transition-colors focus:outline-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="absolute right-3 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white disabled:text-slate-500 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md cursor-pointer disabled:cursor-not-allowed"
          >
            <span>{loading ? "Analyzing..." : "Ask Agent"}</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2 px-1">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Anti-hallucination policy active: queries strictly constrained to 8 database tools</span>
          </div>
          <span className="hidden sm:inline">Press Enter to submit</span>
        </div>
      </form>

      {/* Agent Tool Capability Overview */}
      <div className="bg-slate-900/40 border border-slate-800/60 rounded-2xl p-4">
        <span className="text-xs font-semibold text-slate-400 block mb-2.5">
          Available Deterministic Analytics Tools ({agentToolsCatalog.length}):
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2">
          {agentToolsCatalog.map((t) => (
            <div key={t.name} className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800/80 text-xs">
              <span className="font-mono text-[11px] font-bold text-indigo-400 block mb-0.5">
                {t.name}()
              </span>
              <span className="text-[11px] text-slate-400 leading-tight block">
                {t.desc}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
