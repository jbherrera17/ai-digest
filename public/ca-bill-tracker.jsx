const { useState, useEffect } = React;

const ALL_TOPICS = [
  { id: "ai_automation", label: "Artificial Intelligence & Automation", icon: "🤖", category: "Technology" },
  { id: "data_privacy", label: "Data Privacy & Consumer Protection", icon: "🔒", category: "Technology" },
  { id: "cybersecurity", label: "Cybersecurity", icon: "🛡️", category: "Technology" },
  { id: "digital_infrastructure", label: "Digital Infrastructure & Broadband", icon: "🌐", category: "Technology" },
  { id: "tech_regulation", label: "Tech Platform Regulation", icon: "⚙️", category: "Technology" },
  { id: "biometric_data", label: "Biometric Data & Facial Recognition", icon: "👁️", category: "Technology" },
  { id: "healthcare_tech", label: "Healthcare Technology & Telehealth", icon: "🏥", category: "Healthcare" },
  { id: "medical_ai", label: "Medical AI & Diagnostics", icon: "🧬", category: "Healthcare" },
  { id: "mental_health", label: "Mental Health Services", icon: "🧠", category: "Healthcare" },
  { id: "health_data", label: "Health Data & HIPAA", icon: "📋", category: "Healthcare" },
  { id: "biotech", label: "Biotech & Life Sciences", icon: "🔬", category: "Healthcare" },
  { id: "smb_support", label: "Small Business Support & Incentives", icon: "🏪", category: "Business" },
  { id: "tax_policy", label: "Business Tax Policy", icon: "💰", category: "Business" },
  { id: "licensing", label: "Professional Licensing & Regulation", icon: "📜", category: "Business" },
  { id: "startup_ecosystem", label: "Startup & Innovation Ecosystem", icon: "🚀", category: "Business" },
  { id: "procurement", label: "Government Procurement & Contracts", icon: "🤝", category: "Business" },
  { id: "employment_law", label: "Employment Law & Worker Classification", icon: "👷", category: "Employment" },
  { id: "gig_economy", label: "Gig Economy & Independent Contractors", icon: "📱", category: "Employment" },
  { id: "remote_work", label: "Remote Work & Hybrid Policies", icon: "🏠", category: "Employment" },
  { id: "minimum_wage", label: "Minimum Wage & Compensation", icon: "💵", category: "Employment" },
  { id: "workplace_ai", label: "AI in the Workplace", icon: "💼", category: "Employment" },
  { id: "education_workforce", label: "Education & Workforce Development", icon: "🎓", category: "Employment" },
  { id: "climate", label: "Climate & Environmental Policy", icon: "🌿", category: "Environment" },
  { id: "energy", label: "Energy & Clean Technology", icon: "⚡", category: "Environment" },
  { id: "sustainability", label: "Sustainability & ESG Requirements", icon: "♻️", category: "Environment" },
  { id: "housing", label: "Housing & Real Estate", icon: "🏘️", category: "Society" },
  { id: "equity_dei", label: "Equity, DEI & Civil Rights", icon: "⚖️", category: "Society" },
  { id: "immigration", label: "Immigration & Workforce", icon: "🌎", category: "Society" },
  { id: "finance_banking", label: "Finance, Banking & Fintech", icon: "🏦", category: "Finance" },
  { id: "crypto", label: "Cryptocurrency & Digital Assets", icon: "₿", category: "Finance" },
  { id: "insurance", label: "Insurance Regulation", icon: "🛟", category: "Finance" },
  { id: "public_safety", label: "Public Safety & Law Enforcement Tech", icon: "🚔", category: "Governance" },
  { id: "election", label: "Election & Democracy", icon: "🗳️", category: "Governance" },
  { id: "state_budget", label: "State Budget & Fiscal Policy", icon: "📊", category: "Governance" },
  { id: "local_govt", label: "Local Government & Municipalities", icon: "🏛️", category: "Governance" },
];

const SAMPLE_BILLS = [
  { id: "AB-1234", title: "Automated Decision Systems Accountability Act", status: "Committee", chamber: "Assembly", topics: ["ai_automation", "data_privacy"], introduced: "Jan 15, 2026", sponsor: "Ting", urgency: "high", stage: 2 },
  { id: "SB-567", title: "Healthcare AI Transparency and Patient Rights", status: "Passed Senate", chamber: "Senate", topics: ["medical_ai", "healthcare_tech", "health_data"], introduced: "Jan 22, 2026", sponsor: "Wiener", urgency: "high", stage: 3 },
  { id: "AB-892", title: "Small Business AI Adoption Tax Credit", status: "Introduced", chamber: "Assembly", topics: ["smb_support", "ai_automation", "tax_policy"], introduced: "Feb 3, 2026", sponsor: "Muratsuchi", urgency: "medium", stage: 1 },
  { id: "SB-234", title: "Gig Worker Algorithmic Transparency Act", status: "Governor Review", chamber: "Senate", topics: ["gig_economy", "workplace_ai", "employment_law"], introduced: "Dec 10, 2025", sponsor: "Durazo", urgency: "high", stage: 4 },
  { id: "AB-445", title: "Biometric Privacy Enhancement Act", status: "Committee", chamber: "Assembly", topics: ["biometric_data", "data_privacy"], introduced: "Feb 14, 2026", sponsor: "Wicks", urgency: "medium", stage: 2 },
  { id: "SB-789", title: "Cybersecurity Standards for Critical Infrastructure", status: "Introduced", chamber: "Senate", topics: ["cybersecurity", "tech_regulation"], introduced: "Feb 20, 2026", sponsor: "Becker", urgency: "low", stage: 1 },
  { id: "AB-301", title: "Remote Work Employee Rights Act", status: "Passed Assembly", chamber: "Assembly", topics: ["remote_work", "employment_law"], introduced: "Jan 8, 2026", sponsor: "Haney", urgency: "medium", stage: 3 },
  { id: "SB-112", title: "Fintech Consumer Protection & Crypto Disclosure", status: "Committee", chamber: "Senate", topics: ["crypto", "finance_banking", "data_privacy"], introduced: "Jan 30, 2026", sponsor: "Bradford", urgency: "low", stage: 2 },
];

const STAGES = ["Introduced", "In Committee", "Passed One Chamber", "Passed Both Chambers", "Signed/Vetoed"];

const CATEGORIES = [...new Set(ALL_TOPICS.map(t => t.category))];

const URGENCY_COLOR = {
  high: { bg: "#fee2e2", text: "#991b1b", dot: "#ef4444" },
  medium: { bg: "#fef9c3", text: "#854d0e", dot: "#eab308" },
  low: { bg: "#dcfce7", text: "#166534", dot: "#22c55e" },
};

const STAGE_COLOR = ["#e0e7ff","#ddd6fe","#c4b5fd","#a78bfa","#7c3aed"];

function CABillTracker() {
  const [selectedTopics, setSelectedTopics] = useState(["ai_automation","data_privacy","medical_ai","smb_support","workplace_ai","employment_law"]);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [filterUrgency, setFilterUrgency] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedBill, setExpandedBill] = useState(null);
  const [topicSearch, setTopicSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [commStrategy, setCommStrategy] = useState(null);
  const [toast, setToast] = useState(null);

  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  };

  const toggleTopic = (id) => {
    setSelectedTopics(prev =>
      prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]
    );
  };

  const filteredTopics = ALL_TOPICS.filter(t =>
    (selectedCategory === "All" || t.category === selectedCategory) &&
    t.label.toLowerCase().includes(topicSearch.toLowerCase())
  );

  const relevantBills = SAMPLE_BILLS.filter(b =>
    b.topics.some(t => selectedTopics.includes(t))
  );

  const displayBills = relevantBills.filter(b => {
    const urgencyMatch = filterUrgency === "all" || b.urgency === filterUrgency;
    const statusMatch = filterStatus === "all" || b.status === filterStatus;
    const searchMatch = !searchTerm || b.title.toLowerCase().includes(searchTerm.toLowerCase()) || b.id.toLowerCase().includes(searchTerm.toLowerCase());
    return urgencyMatch && statusMatch && searchMatch;
  });

  const highCount = relevantBills.filter(b => b.urgency === "high").length;
  const medCount = relevantBills.filter(b => b.urgency === "medium").length;
  const lowCount = relevantBills.filter(b => b.urgency === "low").length;

  const getTopicLabel = (id) => ALL_TOPICS.find(t => t.id === id)?.label || id;

  const COMM_TEMPLATES = {
    thought_leadership: {
      label: "💡 Thought Leadership",
      color: "#b78bd3",
      channels: ["LinkedIn Article", "Substack Post", "Blog"],
      cadence: "Weekly",
      template: (bill) => `📢 California's ${bill.title} (${bill.id}) is moving through the legislature — and it matters for every values-driven business leader.\n\nHere's what it means for your organization:\n→ [Insert 2–3 implications]\n\nMy take: [Insert your perspective grounded in human-first AI principles]\n\nWhat questions are you asking about this? Let's talk.\n\n#AIPolicy #CaliforniaLegislation #HumanFirstAI #SynergiAI`
    },
    client_alert: {
      label: "🔔 Client Alert",
      color: "#77bde0",
      channels: ["Email", "Client Portal", "Slack/Teams"],
      cadence: "Within 48hrs of stage change",
      template: (bill) => `Subject: Legislative Alert — ${bill.id} | Action May Be Required\n\nDear [Client Name],\n\nI want to bring your attention to ${bill.title} (${bill.id}), currently at the "${bill.status}" stage in the California legislature.\n\nWhy this matters to you:\n• [Specific impact on their business]\n• [Timeline and urgency]\n• [Recommended action or preparation]\n\nI'll be monitoring this closely and will update you as it progresses. If you'd like to discuss implications for your strategy, let's schedule time this week.\n\nBest,\nJB`
    },
    legislative_engagement: {
      label: "🏛️ Legislative Engagement",
      color: "#dc9171",
      channels: ["Public Comment", "Committee Testimony", "Direct Outreach"],
      cadence: "At committee hearing / public comment windows",
      template: (bill) => `Re: ${bill.id} — ${bill.title}\nSubmitted by: JB Herrera, Founder/CEO, Synergi AI LLC\n\nChair [Name] and Members of the Committee,\n\nI write as an AI consultant serving small and mid-sized businesses across California. [Bill ID] addresses [issue] — a matter I engage with daily in my practice.\n\nI [support/oppose] this bill because:\n1. [Evidence-based argument #1 grounded in SMB impact]\n2. [Evidence-based argument #2 grounded in human-first AI principles]\n3. [Proposed amendment or alternative if opposing]\n\nCalifornia has an opportunity to lead with both innovation and integrity. I urge the committee to [specific ask].\n\nRespectfully,\nJB Herrera | Synergi AI LLC | jb@synergiai.io | 916-314-7617`
    }
  };

  return (
    <div style={{ fontFamily: "'Poppins', sans-serif", background: "#f8f7ff", minHeight: "100vh", color: "#1a1a2e" }}>
      {/* Header */}
      <div style={{ background: "linear-gradient(135deg, #1a1a2e 0%, #2d1b69 60%, #6A00F6 100%)", padding: "0", position: "relative", overflow: "hidden" }}>
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, backgroundImage: "radial-gradient(circle at 20% 50%, rgba(183,139,211,0.15) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(119,189,224,0.1) 0%, transparent 40%)" }} />
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "28px 32px", position: "relative" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
                <span style={{ fontSize: 28 }}>🏛️</span>
                <h1 style={{ margin: 0, fontSize: 26, fontWeight: 700, color: "#fff", letterSpacing: "-0.5px" }}>CA Legislative Intelligence</h1>
              </div>
              <p style={{ margin: 0, color: "rgba(255,255,255,0.6)", fontSize: 13 }}>Synergi AI · Bill Monitoring & Communication Strategy Platform</p>
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              {[
                { label: "🔴 High", val: highCount, bg: "rgba(239,68,68,0.2)", border: "rgba(239,68,68,0.4)" },
                { label: "🟡 Medium", val: medCount, bg: "rgba(234,179,8,0.2)", border: "rgba(234,179,8,0.4)" },
                { label: "🟢 Low", val: lowCount, bg: "rgba(34,197,94,0.2)", border: "rgba(34,197,94,0.4)" },
              ].map(s => (
                <div key={s.label} style={{ background: s.bg, border: `1px solid ${s.border}`, borderRadius: 10, padding: "8px 16px", textAlign: "center" }}>
                  <div style={{ color: "#fff", fontSize: 20, fontWeight: 700 }}>{s.val}</div>
                  <div style={{ color: "rgba(255,255,255,0.7)", fontSize: 11 }}>{s.label}</div>
                </div>
              ))}
              <div style={{ background: "rgba(183,139,211,0.2)", border: "1px solid rgba(183,139,211,0.4)", borderRadius: 10, padding: "8px 16px", textAlign: "center" }}>
                <div style={{ color: "#fff", fontSize: 20, fontWeight: 700 }}>{selectedTopics.length}</div>
                <div style={{ color: "rgba(255,255,255,0.7)", fontSize: 11 }}>Topics</div>
              </div>
            </div>
          </div>
          {/* Tabs */}
          <div style={{ display: "flex", gap: 4, marginTop: 20 }}>
            {[
              { id: "dashboard", label: "📊 Dashboard" },
              { id: "topics", label: "🏷️ Topic Selector" },
              { id: "bills", label: "📋 Bill Tracker" },
              { id: "comms", label: "📣 Comm Strategy" },
            ].map(tab => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                style={{ background: activeTab === tab.id ? "rgba(255,255,255,0.15)" : "transparent", border: activeTab === tab.id ? "1px solid rgba(255,255,255,0.3)" : "1px solid transparent", color: activeTab === tab.id ? "#fff" : "rgba(255,255,255,0.55)", borderRadius: "8px 8px 0 0", padding: "8px 18px", cursor: "pointer", fontSize: 13, fontWeight: 600, fontFamily: "Poppins, sans-serif", transition: "all 0.2s" }}>
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "28px 32px" }}>

        {/* DASHBOARD TAB */}
        {activeTab === "dashboard" && (
          <div>
            {/* Pipeline Viz */}
            <div style={{ background: "#fff", borderRadius: 16, padding: 24, marginBottom: 24, boxShadow: "0 2px 12px rgba(106,0,246,0.06)" }}>
              <h2 style={{ margin: "0 0 20px", fontSize: 16, fontWeight: 700, color: "#1a1a2e" }}>📍 Legislative Pipeline — Tracked Bills</h2>
              <div style={{ display: "flex", gap: 0 }}>
                {STAGES.map((stage, i) => {
                  const count = relevantBills.filter(b => b.stage === i + 1).length;
                  return (
                    <div key={stage} style={{ flex: 1, position: "relative" }}>
                      <div style={{ background: STAGE_COLOR[i], borderRadius: i === 0 ? "10px 0 0 10px" : i === 4 ? "0 10px 10px 0" : 0, padding: "14px 12px", textAlign: "center", marginRight: i < 4 ? 2 : 0 }}>
                        <div style={{ fontSize: 22, fontWeight: 800, color: i >= 3 ? "#fff" : "#4c1d95" }}>{count}</div>
                        <div style={{ fontSize: 10, color: i >= 3 ? "rgba(255,255,255,0.85)" : "#6d28d9", marginTop: 2, lineHeight: 1.3 }}>{stage}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Bills Grid */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
              {relevantBills.slice(0, 6).map(bill => {
                const urg = URGENCY_COLOR[bill.urgency];
                return (
                  <div key={bill.id} onClick={() => { setExpandedBill(expandedBill === bill.id ? null : bill.id); }}
                    style={{ background: "#fff", borderRadius: 14, padding: 20, boxShadow: "0 2px 12px rgba(106,0,246,0.06)", cursor: "pointer", border: expandedBill === bill.id ? "2px solid #b78bd3" : "2px solid transparent", transition: "all 0.2s" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                      <span style={{ background: "#ede9fe", color: "#5b21b6", fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 20 }}>{bill.id}</span>
                      <span style={{ background: urg.bg, color: urg.text, fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 20, textTransform: "uppercase" }}>{bill.urgency}</span>
                    </div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: "#1a1a2e", marginBottom: 8, lineHeight: 1.4 }}>{bill.title}</div>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
                      {bill.topics.slice(0, 2).map(t => (
                        <span key={t} style={{ background: "#f3f0ff", color: "#7c3aed", fontSize: 10, padding: "2px 8px", borderRadius: 12 }}>{ALL_TOPICS.find(x => x.id === t)?.icon} {ALL_TOPICS.find(x => x.id === t)?.label.split(" ").slice(0,3).join(" ")}</span>
                      ))}
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#888" }}>
                      <span>📌 {bill.status}</span>
                      <span>by {bill.sponsor}</span>
                    </div>
                    {expandedBill === bill.id && (
                      <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid #f0eaff" }}>
                        <div style={{ fontSize: 12, color: "#555", marginBottom: 8 }}>Introduced: {bill.introduced} · {bill.chamber}</div>
                        <div style={{ display: "flex", gap: 8 }}>
                          <button onClick={e => { e.stopPropagation(); setActiveTab("comms"); setCommStrategy({ bill, type: "client_alert" }); showToast("Opening comm strategy..."); }}
                            style={{ background: "#77bde0", color: "#fff", border: "none", borderRadius: 8, padding: "6px 12px", fontSize: 11, fontWeight: 600, cursor: "pointer", fontFamily: "Poppins, sans-serif" }}>
                            🔔 Alert Clients
                          </button>
                          <button onClick={e => { e.stopPropagation(); setActiveTab("comms"); setCommStrategy({ bill, type: "thought_leadership" }); showToast("Opening comm strategy..."); }}
                            style={{ background: "#b78bd3", color: "#fff", border: "none", borderRadius: 8, padding: "6px 12px", fontSize: 11, fontWeight: 600, cursor: "pointer", fontFamily: "Poppins, sans-serif" }}>
                            💡 Post Insight
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Monitoring Sources */}
            <div style={{ background: "#fff", borderRadius: 16, padding: 24, boxShadow: "0 2px 12px rgba(106,0,246,0.06)" }}>
              <h2 style={{ margin: "0 0 16px", fontSize: 16, fontWeight: 700 }}>📡 Recommended Monitoring Sources</h2>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
                {[
                  { name: "leginfo.legislature.ca.gov", desc: "Official CA bill text & status", type: "Primary", icon: "🏛️" },
                  { name: "calmatters.org", desc: "Non-partisan CA policy journalism", type: "News", icon: "📰" },
                  { name: "FiscalNote / LegiScan", desc: "AI-powered bill tracking & alerts", type: "Tool", icon: "🔍" },
                  { name: "CalChamber", desc: "Business impact analysis & job killers list", type: "Advocacy", icon: "💼" },
                  { name: "CTIA / TechNet CA", desc: "Tech industry policy positions", type: "Industry", icon: "🤖" },
                  { name: "Google Alerts", desc: "Custom keyword monitoring", type: "Free Tool", icon: "🔔" },
                ].map(s => (
                  <div key={s.name} style={{ background: "#faf8ff", border: "1px solid #ede9fe", borderRadius: 12, padding: 14 }}>
                    <div style={{ fontSize: 20, marginBottom: 6 }}>{s.icon}</div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: "#1a1a2e", marginBottom: 2 }}>{s.name}</div>
                    <div style={{ fontSize: 11, color: "#888", marginBottom: 6 }}>{s.desc}</div>
                    <span style={{ background: "#ede9fe", color: "#7c3aed", fontSize: 10, padding: "2px 8px", borderRadius: 10, fontWeight: 600 }}>{s.type}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TOPIC SELECTOR TAB */}
        {activeTab === "topics" && (
          <div>
            <div style={{ background: "#fff", borderRadius: 16, padding: 24, marginBottom: 20, boxShadow: "0 2px 12px rgba(106,0,246,0.06)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <div>
                  <h2 style={{ margin: "0 0 4px", fontSize: 18, fontWeight: 700 }}>🏷️ Select Your Monitored Topics</h2>
                  <p style={{ margin: 0, color: "#888", fontSize: 13 }}>{selectedTopics.length} of {ALL_TOPICS.length} topics selected · Bills matching your selection: {relevantBills.length}</p>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button onClick={() => setSelectedTopics(ALL_TOPICS.map(t => t.id))}
                    style={{ background: "#ede9fe", color: "#7c3aed", border: "none", borderRadius: 8, padding: "8px 16px", fontSize: 12, fontWeight: 600, cursor: "pointer", fontFamily: "Poppins, sans-serif" }}>Select All</button>
                  <button onClick={() => setSelectedTopics([])}
                    style={{ background: "#fee2e2", color: "#991b1b", border: "none", borderRadius: 8, padding: "8px 16px", fontSize: 12, fontWeight: 600, cursor: "pointer", fontFamily: "Poppins, sans-serif" }}>Clear All</button>
                </div>
              </div>
              <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
                {["All", ...CATEGORIES].map(cat => (
                  <button key={cat} onClick={() => setSelectedCategory(cat)}
                    style={{ background: selectedCategory === cat ? "#b78bd3" : "#f3f0ff", color: selectedCategory === cat ? "#fff" : "#7c3aed", border: "none", borderRadius: 20, padding: "6px 14px", fontSize: 12, fontWeight: 600, cursor: "pointer", fontFamily: "Poppins, sans-serif" }}>
                    {cat}
                  </button>
                ))}
                <input value={topicSearch} onChange={e => setTopicSearch(e.target.value)} placeholder="Search topics..."
                  style={{ marginLeft: "auto", border: "1px solid #e0d9ff", borderRadius: 20, padding: "6px 14px", fontSize: 12, outline: "none", fontFamily: "Poppins, sans-serif", width: 180 }} />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
                {filteredTopics.map(topic => {
                  const sel = selectedTopics.includes(topic.id);
                  return (
                    <div key={topic.id} onClick={() => toggleTopic(topic.id)}
                      style={{ display: "flex", alignItems: "center", gap: 10, padding: "12px 14px", borderRadius: 12, border: sel ? "2px solid #b78bd3" : "2px solid #f0eaff", background: sel ? "#faf5ff" : "#fdfcff", cursor: "pointer", transition: "all 0.15s" }}>
                      <div style={{ width: 18, height: 18, borderRadius: 5, border: sel ? "none" : "2px solid #c4b5fd", background: sel ? "#b78bd3" : "transparent", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                        {sel && <span style={{ color: "#fff", fontSize: 11, fontWeight: 700 }}>✓</span>}
                      </div>
                      <span style={{ fontSize: 16 }}>{topic.icon}</span>
                      <div>
                        <div style={{ fontSize: 12, fontWeight: sel ? 700 : 500, color: sel ? "#5b21b6" : "#444", lineHeight: 1.3 }}>{topic.label}</div>
                        <div style={{ fontSize: 10, color: "#aaa" }}>{topic.category}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            <div style={{ background: "linear-gradient(135deg, #faf5ff, #f0f9ff)", border: "1px solid #e0d9ff", borderRadius: 14, padding: 20 }}>
              <h3 style={{ margin: "0 0 10px", fontSize: 14, fontWeight: 700, color: "#5b21b6" }}>✅ Your Selected Topics</h3>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {selectedTopics.map(id => {
                  const t = ALL_TOPICS.find(x => x.id === id);
                  return t ? (
                    <span key={id} style={{ background: "#b78bd3", color: "#fff", fontSize: 11, fontWeight: 600, padding: "4px 12px", borderRadius: 20, display: "flex", alignItems: "center", gap: 4 }}>
                      {t.icon} {t.label.split(" ").slice(0,4).join(" ")}
                      <span onClick={() => toggleTopic(id)} style={{ cursor: "pointer", marginLeft: 4, opacity: 0.7 }}>×</span>
                    </span>
                  ) : null;
                })}
              </div>
            </div>
          </div>
        )}

        {/* BILL TRACKER TAB */}
        {activeTab === "bills" && (
          <div>
            <div style={{ background: "#fff", borderRadius: 16, padding: 20, marginBottom: 20, boxShadow: "0 2px 12px rgba(106,0,246,0.06)", display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
              <input value={searchTerm} onChange={e => setSearchTerm(e.target.value)} placeholder="🔍 Search bills by title or ID..."
                style={{ flex: 1, minWidth: 200, border: "1px solid #e0d9ff", borderRadius: 10, padding: "10px 14px", fontSize: 13, outline: "none", fontFamily: "Poppins, sans-serif" }} />
              <select value={filterUrgency} onChange={e => setFilterUrgency(e.target.value)}
                style={{ border: "1px solid #e0d9ff", borderRadius: 10, padding: "10px 14px", fontSize: 13, background: "#fff", fontFamily: "Poppins, sans-serif", outline: "none" }}>
                <option value="all">All Urgency</option>
                <option value="high">🔴 High</option>
                <option value="medium">🟡 Medium</option>
                <option value="low">🟢 Low</option>
              </select>
              <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
                style={{ border: "1px solid #e0d9ff", borderRadius: 10, padding: "10px 14px", fontSize: 13, background: "#fff", fontFamily: "Poppins, sans-serif", outline: "none" }}>
                <option value="all">All Status</option>
                {STAGES.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
              <span style={{ color: "#888", fontSize: 13 }}>{displayBills.length} bills</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {displayBills.map(bill => {
                const urg = URGENCY_COLOR[bill.urgency];
                return (
                  <div key={bill.id} style={{ background: "#fff", borderRadius: 14, padding: 20, boxShadow: "0 2px 12px rgba(106,0,246,0.06)", borderLeft: `4px solid ${urg.dot}` }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                        <span style={{ background: "#ede9fe", color: "#5b21b6", fontSize: 12, fontWeight: 700, padding: "4px 12px", borderRadius: 20 }}>{bill.id}</span>
                        <span style={{ background: urg.bg, color: urg.text, fontSize: 11, fontWeight: 700, padding: "4px 10px", borderRadius: 20 }}>{bill.urgency.toUpperCase()}</span>
                        <span style={{ background: "#f0f9ff", color: "#0369a1", fontSize: 11, padding: "4px 10px", borderRadius: 20 }}>{bill.chamber}</span>
                      </div>
                      <span style={{ color: "#888", fontSize: 12 }}>Introduced {bill.introduced}</span>
                    </div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: "#1a1a2e", marginBottom: 8 }}>{bill.title}</div>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
                      {bill.topics.map(t => (
                        <span key={t} style={{ background: "#f3f0ff", color: "#7c3aed", fontSize: 11, padding: "3px 10px", borderRadius: 12 }}>{ALL_TOPICS.find(x => x.id === t)?.icon} {ALL_TOPICS.find(x => x.id === t)?.label}</span>
                      ))}
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ fontSize: 12, color: "#555" }}>📌 {bill.status}</span>
                        <span style={{ fontSize: 12, color: "#888" }}>· Sponsor: {bill.sponsor}</span>
                      </div>
                      <div style={{ display: "flex", gap: 8 }}>
                        {Object.entries(COMM_TEMPLATES).map(([key, tmpl]) => (
                          <button key={key} onClick={() => { setCommStrategy({ bill, type: key }); setActiveTab("comms"); showToast(`Strategy loaded for ${bill.id}`); }}
                            style={{ background: tmpl.color, color: "#fff", border: "none", borderRadius: 8, padding: "6px 12px", fontSize: 11, fontWeight: 600, cursor: "pointer", fontFamily: "Poppins, sans-serif" }}>
                            {tmpl.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* COMM STRATEGY TAB */}
        {activeTab === "comms" && (
          <div>
            <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20 }}>
              <div>
                <div style={{ background: "#fff", borderRadius: 16, padding: 20, marginBottom: 16, boxShadow: "0 2px 12px rgba(106,0,246,0.06)" }}>
                  <h3 style={{ margin: "0 0 14px", fontSize: 15, fontWeight: 700 }}>Select a Bill</h3>
                  {relevantBills.map(bill => {
                    const sel = commStrategy?.bill?.id === bill.id;
                    const urg = URGENCY_COLOR[bill.urgency];
                    return (
                      <div key={bill.id} onClick={() => setCommStrategy(prev => ({ ...prev, bill }))}
                        style={{ padding: "10px 12px", borderRadius: 10, border: sel ? "2px solid #b78bd3" : "2px solid transparent", background: sel ? "#faf5ff" : "#f9f8ff", cursor: "pointer", marginBottom: 8, transition: "all 0.15s" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                          <span style={{ fontSize: 12, fontWeight: 700, color: "#5b21b6" }}>{bill.id}</span>
                          <span style={{ fontSize: 10, color: urg.text, background: urg.bg, padding: "1px 6px", borderRadius: 10 }}>{bill.urgency}</span>
                        </div>
                        <div style={{ fontSize: 11, color: "#444", lineHeight: 1.4 }}>{bill.title.slice(0, 55)}...</div>
                      </div>
                    );
                  })}
                </div>
                <div style={{ background: "#fff", borderRadius: 16, padding: 20, boxShadow: "0 2px 12px rgba(106,0,246,0.06)" }}>
                  <h3 style={{ margin: "0 0 14px", fontSize: 15, fontWeight: 700 }}>Communication Type</h3>
                  {Object.entries(COMM_TEMPLATES).map(([key, tmpl]) => (
                    <div key={key} onClick={() => setCommStrategy(prev => ({ ...prev, type: key }))}
                      style={{ padding: "12px 14px", borderRadius: 10, border: commStrategy?.type === key ? `2px solid ${tmpl.color}` : "2px solid transparent", background: commStrategy?.type === key ? "#faf5ff" : "#f9f8ff", cursor: "pointer", marginBottom: 8, transition: "all 0.15s" }}>
                      <div style={{ fontSize: 13, fontWeight: 700, color: "#1a1a2e", marginBottom: 4 }}>{tmpl.label}</div>
                      <div style={{ fontSize: 11, color: "#888" }}>📅 {tmpl.cadence}</div>
                      <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginTop: 6 }}>
                        {tmpl.channels.map(ch => (
                          <span key={ch} style={{ background: "#f3f0ff", color: "#7c3aed", fontSize: 10, padding: "2px 6px", borderRadius: 8 }}>{ch}</span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                {commStrategy?.bill && commStrategy?.type ? (
                  <div>
                    <div style={{ background: "#fff", borderRadius: 16, padding: 24, marginBottom: 16, boxShadow: "0 2px 12px rgba(106,0,246,0.06)" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
                        <div>
                          <h2 style={{ margin: "0 0 4px", fontSize: 18, fontWeight: 700 }}>{COMM_TEMPLATES[commStrategy.type].label}</h2>
                          <p style={{ margin: 0, color: "#888", fontSize: 13 }}>Template for {commStrategy.bill.id} · {commStrategy.bill.title}</p>
                        </div>
                        <button onClick={() => { navigator.clipboard?.writeText(COMM_TEMPLATES[commStrategy.type].template(commStrategy.bill)); showToast("✅ Copied to clipboard!"); }}
                          style={{ background: COMM_TEMPLATES[commStrategy.type].color, color: "#fff", border: "none", borderRadius: 10, padding: "10px 20px", fontSize: 13, fontWeight: 600, cursor: "pointer", fontFamily: "Poppins, sans-serif" }}>
                          📋 Copy Template
                        </button>
                      </div>
                      <div style={{ background: "#f9f8ff", borderRadius: 12, padding: 20, fontFamily: "monospace", fontSize: 13, lineHeight: 1.7, color: "#333", whiteSpace: "pre-wrap", border: "1px solid #ede9fe", maxHeight: 380, overflowY: "auto" }}>
                        {COMM_TEMPLATES[commStrategy.type].template(commStrategy.bill)}
                      </div>
                    </div>
                    <div style={{ background: "#fff", borderRadius: 16, padding: 24, boxShadow: "0 2px 12px rgba(106,0,246,0.06)" }}>
                      <h3 style={{ margin: "0 0 16px", fontSize: 15, fontWeight: 700 }}>📅 Cadence & Channel Matrix</h3>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
                        {[
                          { phase: "Bill Introduced", action: "Internal note + add to tracker", channel: "Notion / Task", timing: "Within 24hrs" },
                          { phase: "Committee Hearing", action: "Submit public comment", channel: "Legislature.ca.gov", timing: "Before hearing date" },
                          { phase: "Passes Committee", action: "Client alert email", channel: "Email / CRM", timing: "Within 48hrs" },
                          { phase: "Passes One Chamber", action: "LinkedIn thought leadership", channel: "LinkedIn + Substack", timing: "Within 72hrs" },
                          { phase: "Passes Both Chambers", action: "Full client briefing + webinar invite", channel: "Email + Zoom", timing: "Within 1 week" },
                          { phase: "Signed by Governor", action: "Compliance guide + service offering", channel: "All channels", timing: "Within 2 weeks" },
                        ].map(row => (
                          <div key={row.phase} style={{ background: "#faf8ff", border: "1px solid #ede9fe", borderRadius: 12, padding: 14 }}>
                            <div style={{ fontSize: 11, fontWeight: 700, color: "#7c3aed", marginBottom: 6 }}>{row.phase}</div>
                            <div style={{ fontSize: 12, color: "#333", marginBottom: 4 }}>{row.action}</div>
                            <div style={{ fontSize: 11, color: "#888" }}>📍 {row.channel}</div>
                            <div style={{ fontSize: 11, color: "#888" }}>⏱ {row.timing}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={{ background: "#fff", borderRadius: 16, padding: 40, textAlign: "center", boxShadow: "0 2px 12px rgba(106,0,246,0.06)", color: "#888" }}>
                    <div style={{ fontSize: 48, marginBottom: 16 }}>📣</div>
                    <h3 style={{ margin: "0 0 8px", color: "#444" }}>Select a Bill + Communication Type</h3>
                    <p style={{ margin: 0, fontSize: 14 }}>Choose from the left panel to generate your communication template</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Toast */}
      {toast && (
        <div style={{ position: "fixed", bottom: 30, right: 30, background: "#1a1a2e", color: "#fff", padding: "12px 24px", borderRadius: 12, fontSize: 14, fontWeight: 600, boxShadow: "0 8px 32px rgba(0,0,0,0.3)", zIndex: 1000 }}>
          {toast}
        </div>
      )}
    </div>
  );
}
