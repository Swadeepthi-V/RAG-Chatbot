import React, { useState, useEffect, useRef } from 'react';
import { 
  MessageSquare, 
  Send, 
  Sparkles, 
  AlertTriangle, 
  X, 
  ExternalLink, 
  ShieldAlert, 
  FileText, 
  TrendingUp,
  RefreshCw,
  ChevronRight
} from 'lucide-react';

// 17 HDFC Schemes from Phase 1 crawler for the interactive Factsheet Overlay
const HDFC_SCHEMES = [
  { name: "HDFC Small Cap Fund", category: "Equity - Small Cap", url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-small-cap-fund/direct" },
  { name: "HDFC Mid-Cap Opportunities", category: "Equity - Mid Cap", url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-mid-cap-opportunities-fund/direct" },
  { name: "HDFC Large and Mid-Cap Fund", category: "Equity - Large & Mid", url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-large-and-mid-cap-fund/direct" },
  { name: "HDFC Flexi Cap Fund", category: "Equity - Flexi Cap", url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund/direct" },
  { name: "HDFC Top 100 Fund", category: "Equity - Large Cap", url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-top-100-fund/direct" },
  { name: "HDFC Balanced Advantage Fund", category: "Hybrid - Dynamic", url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-balanced-advantage-fund/direct" },
  { name: "HDFC Hybrid Equity Fund", category: "Hybrid - Aggressive", url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-hybrid-equity-fund/direct" },
  { name: "HDFC Multi-Cap Fund", category: "Equity - Multi Cap", url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-multi-cap-fund/direct" },
  { name: "HDFC Infrastructure Fund", category: "Equity - Sectoral", url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-infrastructure-fund/direct" },
  { name: "HDFC Dividend Yield Fund", category: "Equity - Dividend", url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-dividend-yield-fund/direct" },
  { name: "HDFC ELSS Tax Saver", category: "Equity - ELSS (Tax)", url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-elss-tax-saver/direct" },
  { name: "HDFC Index Nifty 50 Plan", category: "Equity - Index", url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-index-fund-nifty-50-plan/direct" },
  { name: "HDFC Index Nifty Next 50 Plan", category: "Equity - Index", url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-index-fund-nifty-next-50-plan/direct" },
  { name: "HDFC Gold Fund", category: "Other - Gold", url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-gold-fund/direct" },
  { name: "HDFC Multi-Asset Allocation", category: "Hybrid - Multi Asset", url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-multi-asset-allocation-fund/direct" },
  { name: "HDFC Retirement Savings Fund", category: "Solution Oriented", url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-retirement-savings-fund-equity-plan/direct" },
  { name: "HDFC Children's Gift Fund", category: "Solution Oriented", url: "https://www.hdfcfund.com/explore/mutual-funds/hdfc-childrens-gift-fund/direct" }
];

const PRESETS = [
  "What is the exit load of HDFC Small Cap Fund?",
  "Who is the fund manager of HDFC Mid-Cap Opportunities?",
  "Show minimum SIP amount for HDFC Index Nifty 50 Plan"
];

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showFactsheets, setShowFactsheets] = useState(false);
  const [indexDate, setIndexDate] = useState("02-Jun-2026");
  const [corpusSize, setCorpusSize] = useState(17);
  
  const chatStreamRef = useRef(null);
  const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000";

  // Fetch health check on mount to get last indexed date dynamically
  useEffect(() => {
    fetch(`${apiBase}/health`)
      .then(res => res.json())
      .then(data => {
        if (data.last_updated) setIndexDate(data.last_updated);
        if (data.corpus_size) setCorpusSize(data.corpus_size);
      })
      .catch(err => console.warn("FastAPI offline. Using environment defaults.", err));
  }, []);

  // Auto-scroll to bottom of chat stream on new message
  useEffect(() => {
    if (chatStreamRef.current) {
      chatStreamRef.current.scrollTop = chatStreamRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const parseMessage = (text) => {
    // 1. Strip dynamic footer
    const footerRegex = /\n\nLast updated from sources:\s*(.+)$/;
    const footerMatch = text.match(footerRegex);
    let cleanText = text;
    if (footerMatch) {
      cleanText = text.replace(footerRegex, '').trim();
    }

    // 2. Extract markdown link [label](url)
    const markdownLinkRegex = /\[([^\]]+)\]\((https?:\/\/[^\)]+)\)/;
    const linkMatch = cleanText.match(markdownLinkRegex);
    let citationUrl = null;
    let citationLabel = null;

    if (linkMatch) {
      cleanText = cleanText.replace(markdownLinkRegex, '').trim();
      citationLabel = linkMatch[1];
      citationUrl = linkMatch[2];
      
      // Clean up trailing punctuation after removing link
      if (cleanText.endsWith('.') || cleanText.endsWith(',')) {
        cleanText = cleanText.substring(0, cleanText.length - 1).trim();
      }
    }

    return { cleanText, citationUrl, citationLabel };
  };

  const handleSend = async (textToSend) => {
    const queryText = textToSend || input;
    if (!queryText.trim() || loading) return;

    // Add user message to state
    const userMsg = { id: Date.now() + "-user", text: queryText, sender: "user" };
    setMessages(prev => [...prev, userMsg]);
    
    if (!textToSend) setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${apiBase}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText })
      });

      if (res.ok) {
        const data = await res.json();
        
        // Parse the generated text for citations and footers
        const parsed = parseMessage(data.response);

        const aiMsg = {
          id: Date.now() + "-ai",
          text: parsed.cleanText,
          sender: "assistant",
          category: data.category,
          status: data.status,
          citationUrl: parsed.citationUrl,
          citationLabel: parsed.citationLabel,
          chunks: data.chunks || []
        };
        
        setMessages(prev => [...prev, aiMsg]);

        // If query was blocked as a performance query, automatically show details or hint sheets
        if (data.category === 'performance') {
          // Keep a short delay, then suggest showing factsheet links
          setTimeout(() => {
            setShowFactsheets(true);
          }, 1500);
        }
      } else {
        throw new Error("Server returned non-200 status code.");
      }
    } catch (err) {
      console.error("Query request failed:", err);
      // Failsafe assistant response
      setMessages(prev => [...prev, {
        id: Date.now() + "-error",
        text: "I am unable to reach the API server. Please make sure the local FastAPI backend is running on port 8000.",
        sender: "assistant",
        category: "error"
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Header Bar */}
      <header className="header-bar">
        <div className="header-title-container">
          <h1 className="header-title">HDFC Mutual Fund FAQ</h1>
          <div className="header-subtitle">
            <span className="status-dot"></span>
            <span>Facts-Only Agent</span>
          </div>
        </div>
        
        <button 
          className="citation-pill" 
          onClick={() => setShowFactsheets(true)}
          style={{ marginTop: 0, padding: '5px 12px', background: 'transparent' }}
        >
          <FileText size={14} />
          <span>Factsheets</span>
        </button>
      </header>

      {/* Compliance Disclaimer Banner */}
      <div className="disclaimer-banner">
        <AlertTriangle size={16} style={{ flexShrink: 0 }} />
        <div>
          <span>Factual Grounding Guardrails Active:</span> This system answers strictly using verified documentation. It will refuse investment recommendations, advice, or comparisons.
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="chat-stream" ref={chatStreamRef}>
        {messages.length === 0 ? (
          <div className="empty-state">
            <Sparkles size={40} className="empty-logo" />
            <h2 className="empty-title">Ask a Factual Question</h2>
            <p className="empty-subtitle">
              Verify exit loads, scheme rules, fund managers, and lock-in periods from {corpusSize} official HDFC Mutual Fund documents.
            </p>
            
            <div className="preset-section">
              <span className="preset-title">Suggested Inquiries</span>
              <div className="preset-grid">
                {PRESETS.map((preset, idx) => (
                  <button 
                    key={idx} 
                    className="preset-chip" 
                    onClick={() => handleSend(preset)}
                  >
                    <span>{preset}</span>
                    <ChevronRight size={14} className="preset-chip-arrow" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map(msg => (
            <div key={msg.id} className={`message-row ${msg.sender}`}>
              <div className="message-bubble">
                {/* Highlight Icon based on block category */}
                {msg.category === 'pii' && (
                  <div style={{ display: 'flex', gap: '8px', color: 'var(--error)', marginBottom: '8px', fontWeight: 600, fontSize: '13px' }}>
                    <ShieldAlert size={16} />
                    <span>Security Alert</span>
                  </div>
                )}
                
                {msg.category === 'advisory' && (
                  <div style={{ display: 'flex', gap: '8px', color: 'var(--on-surface-muted)', marginBottom: '8px', fontWeight: 600, fontSize: '13px' }}>
                    <AlertTriangle size={16} style={{ color: 'orange' }} />
                    <span>Refusal (Regulation Compliance)</span>
                  </div>
                )}

                {msg.category === 'performance' && (
                  <div style={{ display: 'flex', gap: '8px', color: 'var(--accent)', marginBottom: '8px', fontWeight: 600, fontSize: '13px' }}>
                    <TrendingUp size={16} />
                    <span>Performance Bypass Intercepted</span>
                  </div>
                )}

                {/* Message Text */}
                <p>{msg.text}</p>
                
                {/* Citation Link Pill */}
                {msg.citationUrl && (
                  <a 
                    href={msg.citationUrl} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="citation-pill"
                  >
                    <ExternalLink size={12} />
                    <span>{msg.citationLabel || "Explore Page"}</span>
                  </a>
                )}
              </div>
            </div>
          ))
        )}

        {/* Loading Indicator */}
        {loading && (
          <div className="message-row assistant">
            <div className="message-bubble" style={{ borderRadius: 'var(--rounded-lg) var(--rounded-lg) var(--rounded-lg) 0' }}>
              <div className="loading-indicator">
                <span className="loading-dot"></span>
                <span className="loading-dot"></span>
                <span className="loading-dot"></span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Dynamic Input Panel */}
      <div className="input-panel">
        <form 
          className="input-container-capsule"
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
        >
          <input
            type="text"
            className="input-field"
            placeholder="Ask a factual question about HDFC mutual funds..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={!input.trim() || loading}
          >
            <Send size={16} />
          </button>
        </form>
        
        <footer className="input-footer">
          Last updated from sources: {indexDate} | Facts-only. No investment advice.
        </footer>
      </div>

      {/* Factsheets / Links List Overlay */}
      {showFactsheets && (
        <div className="factsheet-overlay">
          <div className="factsheet-header">
            <h2 className="factsheet-title">HDFC Fund Factsheets</h2>
            <button className="close-button" onClick={() => setShowFactsheets(false)}>
              <X size={20} />
            </button>
          </div>
          
          <div className="factsheet-content">
            <p className="factsheet-intro">
              Calculations, direct comparisons, and returns projections are bypassed under SEBI rules. Select a specific HDFC mutual fund below to review official daily sheets and disclosures.
            </p>
            
            <div className="factsheet-grid">
              {HDFC_SCHEMES.map((scheme, idx) => (
                <a 
                  key={idx} 
                  href={scheme.url} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="factsheet-card"
                >
                  <div className="factsheet-card-title">{scheme.name}</div>
                  <div className="factsheet-card-meta">
                    <span>{scheme.category}</span>
                    <ExternalLink size={12} className="factsheet-card-link-icon" />
                  </div>
                </a>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
