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

const TOPIC_BY_ID = Object.fromEntries(ALL_TOPICS.map(t => [t.id, t]));

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

  const COMM_TEMPLATES = {
    thought_leadership: {
      label: "💡 Thought Leadership",
      cssVar: "--bills-thought-leadership",
      channels: ["LinkedIn Article", "Substack Post", "Blog"],
      cadence: "Weekly",
      template: (bill) => `📢 California's ${bill.title} (${bill.id}) is moving through the legislature — and it matters for every values-driven business leader.\n\nHere's what it means for your organization:\n→ [Insert 2–3 implications]\n\nMy take: [Insert your perspective grounded in human-first AI principles]\n\nWhat questions are you asking about this? Let's talk.\n\n#AIPolicy #CaliforniaLegislation #HumanFirstAI #SynergiAI`
    },
    client_alert: {
      label: "🔔 Client Alert",
      cssVar: "--bills-client-alert",
      channels: ["Email", "Client Portal", "Slack/Teams"],
      cadence: "Within 48hrs of stage change",
      template: (bill) => `Subject: Legislative Alert — ${bill.id} | Action May Be Required\n\nDear [Client Name],\n\nI want to bring your attention to ${bill.title} (${bill.id}), currently at the "${bill.status}" stage in the California legislature.\n\nWhy this matters to you:\n• [Specific impact on their business]\n• [Timeline and urgency]\n• [Recommended action or preparation]\n\nI'll be monitoring this closely and will update you as it progresses. If you'd like to discuss implications for your strategy, let's schedule time this week.\n\nBest,\nJB`
    },
    legislative_engagement: {
      label: "🏛️ Legislative Engagement",
      cssVar: "--bills-legislative",
      channels: ["Public Comment", "Committee Testimony", "Direct Outreach"],
      cadence: "At committee hearing / public comment windows",
      template: (bill) => `Re: ${bill.id} — ${bill.title}\nSubmitted by: JB Herrera, Founder/CEO, Synergi AI LLC\n\nChair [Name] and Members of the Committee,\n\nI write as an AI consultant serving small and mid-sized businesses across California. [Bill ID] addresses [issue] — a matter I engage with daily in my practice.\n\nI [support/oppose] this bill because:\n1. [Evidence-based argument #1 grounded in SMB impact]\n2. [Evidence-based argument #2 grounded in human-first AI principles]\n3. [Proposed amendment or alternative if opposing]\n\nCalifornia has an opportunity to lead with both innovation and integrity. I urge the committee to [specific ask].\n\nRespectfully,\nJB Herrera | Synergi AI LLC | jb@synergiai.io | 916-314-7617`
    }
  };

  // Comm-type button uses its assigned brand CSS var as background
  const commBtnStyle = (cssVar) => ({
    background: `var(${cssVar})`,
    color: "#fff"
  });

  const TABS = [
    { id: "dashboard", label: "Dashboard" },
    { id: "topics",    label: "Topic Selector" },
    { id: "bills",     label: "Bill Tracker" },
    { id: "comms",     label: "Comm Strategy" },
  ];

  return (
    <div>
      {/* KPI row + tab nav */}
      <div className="bills-kpi-row">
        <div className="bills-kpi high">
          <div className="bills-kpi-value">{highCount}</div>
          <div className="bills-kpi-label">High</div>
        </div>
        <div className="bills-kpi medium">
          <div className="bills-kpi-value">{medCount}</div>
          <div className="bills-kpi-label">Medium</div>
        </div>
        <div className="bills-kpi low">
          <div className="bills-kpi-value">{lowCount}</div>
          <div className="bills-kpi-label">Low</div>
        </div>
        <div className="bills-kpi topics">
          <div className="bills-kpi-value">{selectedTopics.length}</div>
          <div className="bills-kpi-label">Topics</div>
        </div>
      </div>

      <div style={{ marginTop: "var(--space-8)" }}>
        <nav className="bills-tabs" role="tablist">
          {TABS.map(tab => (
            <button
              key={tab.id}
              className={`bills-tab${activeTab === tab.id ? " active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
              role="tab"
              aria-selected={activeTab === tab.id}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* DASHBOARD TAB */}
        {activeTab === "dashboard" && (
          <div>
            <div className="card">
              <div className="bills-card-header">
                <div>
                  <h2 className="text-h3">Legislative Pipeline</h2>
                  <p>Tracked bills by stage in the California legislative process.</p>
                </div>
              </div>
              <div className="bills-pipeline">
                {STAGES.map((stage, i) => {
                  const count = relevantBills.filter(b => b.stage === i + 1).length;
                  return (
                    <div key={stage} className="bills-pipeline-stage" data-intensity={i + 1}>
                      <div className="bills-pipeline-count">{count}</div>
                      <div className="bills-pipeline-label">{stage}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="card">
              <div className="bills-card-header">
                <div>
                  <h2 className="text-h3">Most Relevant Bills</h2>
                  <p>Top matches from your selected topics. Click a card to expand.</p>
                </div>
              </div>
              <div className="bills-grid">
                {relevantBills.slice(0, 6).map(bill => (
                  <div
                    key={bill.id}
                    className={`bills-bill-card${expandedBill === bill.id ? " expanded" : ""}`}
                    onClick={() => setExpandedBill(expandedBill === bill.id ? null : bill.id)}
                  >
                    <div className="bills-bill-head">
                      <div className="bills-bill-head-meta">
                        <span className="bills-id">{bill.id}</span>
                        <span className={`badge badge-urgency-${bill.urgency}`}>{bill.urgency.toUpperCase()}</span>
                      </div>
                    </div>
                    <div className="bills-bill-title">{bill.title}</div>
                    <div className="bills-topic-chips">
                      {bill.topics.slice(0, 2).map(t => {
                        const topic = TOPIC_BY_ID[t];
                        if (!topic) return null;
                        return (
                          <span key={t} className="bills-topic-chip">
                            {topic.icon} {topic.label.split(" ").slice(0, 3).join(" ")}
                          </span>
                        );
                      })}
                    </div>
                    <div className="bills-bill-meta-row">
                      <span>📌 {bill.status}</span>
                      <span>by {bill.sponsor}</span>
                    </div>
                    {expandedBill === bill.id && (
                      <div className="bills-bill-expand">
                        <div className="bills-bill-expand-meta">
                          Introduced {bill.introduced} · {bill.chamber}
                        </div>
                        <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap" }}>
                          <button
                            className="btn btn-sm"
                            style={commBtnStyle("--bills-client-alert")}
                            onClick={e => {
                              e.stopPropagation();
                              setActiveTab("comms");
                              setCommStrategy({ bill, type: "client_alert" });
                              showToast("Opening comm strategy…");
                            }}
                          >
                            🔔 Alert Clients
                          </button>
                          <button
                            className="btn btn-sm"
                            style={commBtnStyle("--bills-thought-leadership")}
                            onClick={e => {
                              e.stopPropagation();
                              setActiveTab("comms");
                              setCommStrategy({ bill, type: "thought_leadership" });
                              showToast("Opening comm strategy…");
                            }}
                          >
                            💡 Post Insight
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <div className="bills-card-header">
                <div>
                  <h2 className="text-h3">Recommended Monitoring Sources</h2>
                  <p>Where to watch for bill movement and policy signal.</p>
                </div>
              </div>
              <div className="bills-sources-grid">
                {[
                  { name: "leginfo.legislature.ca.gov", desc: "Official CA bill text & status", type: "Primary", icon: "🏛️" },
                  { name: "calmatters.org", desc: "Non-partisan CA policy journalism", type: "News", icon: "📰" },
                  { name: "FiscalNote / LegiScan", desc: "AI-powered bill tracking & alerts", type: "Tool", icon: "🔍" },
                  { name: "CalChamber", desc: "Business impact analysis & job killers list", type: "Advocacy", icon: "💼" },
                  { name: "CTIA / TechNet CA", desc: "Tech industry policy positions", type: "Industry", icon: "🤖" },
                  { name: "Google Alerts", desc: "Custom keyword monitoring", type: "Free Tool", icon: "🔔" },
                ].map(s => (
                  <div key={s.name} className="bills-source-tile">
                    <div className="bills-source-icon">{s.icon}</div>
                    <div className="bills-source-name">{s.name}</div>
                    <div className="bills-source-desc">{s.desc}</div>
                    <span className="tag">{s.type}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TOPIC SELECTOR TAB */}
        {activeTab === "topics" && (
          <div>
            <div className="card">
              <div className="bills-card-header">
                <div>
                  <h2 className="text-h3">Select Your Monitored Topics</h2>
                  <p>{selectedTopics.length} of {ALL_TOPICS.length} topics selected · {relevantBills.length} matching bills</p>
                </div>
                <div style={{ display: "flex", gap: "var(--space-2)" }}>
                  <button className="btn btn-secondary btn-sm" onClick={() => setSelectedTopics(ALL_TOPICS.map(t => t.id))}>
                    Select All
                  </button>
                  <button className="btn btn-secondary btn-sm" onClick={() => setSelectedTopics([])}>
                    Clear All
                  </button>
                </div>
              </div>

              <div className="bills-cat-chips">
                {["All", ...CATEGORIES].map(cat => (
                  <button
                    key={cat}
                    className={`bills-cat-chip${selectedCategory === cat ? " active" : ""}`}
                    onClick={() => setSelectedCategory(cat)}
                  >
                    {cat}
                  </button>
                ))}
                <input
                  className="input bills-cat-search"
                  value={topicSearch}
                  onChange={e => setTopicSearch(e.target.value)}
                  placeholder="Search topics…"
                />
              </div>

              <div className="bills-topic-grid">
                {filteredTopics.map(topic => {
                  const sel = selectedTopics.includes(topic.id);
                  return (
                    <div
                      key={topic.id}
                      className={`bills-topic-tile${sel ? " selected" : ""}`}
                      onClick={() => toggleTopic(topic.id)}
                    >
                      <div className="bills-check">{sel ? "✓" : ""}</div>
                      <span className="bills-topic-icon">{topic.icon}</span>
                      <div>
                        <div className="bills-topic-label-strong">{topic.label}</div>
                        <div className="bills-topic-cat">{topic.category}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {selectedTopics.length > 0 && (
              <div className="bills-selected-panel">
                <h3 className="text-h3" style={{ marginBottom: "var(--space-3)" }}>Your Selected Topics</h3>
                <div className="bills-selected-pills">
                  {selectedTopics.map(id => {
                    const t = TOPIC_BY_ID[id];
                    if (!t) return null;
                    return (
                      <span key={id} className="bills-selected-pill">
                        {t.icon} {t.label.split(" ").slice(0, 4).join(" ")}
                        <button
                          aria-label={`Remove ${t.label}`}
                          onClick={() => toggleTopic(id)}
                        >×</button>
                      </span>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* BILL TRACKER TAB */}
        {activeTab === "bills" && (
          <div>
            <div className="card">
              <div className="bills-filter-bar">
                <input
                  className="input search"
                  value={searchTerm}
                  onChange={e => setSearchTerm(e.target.value)}
                  placeholder="🔍 Search bills by title or ID…"
                />
                <select
                  className="select"
                  value={filterUrgency}
                  onChange={e => setFilterUrgency(e.target.value)}
                >
                  <option value="all">All Urgency</option>
                  <option value="high">🔴 High</option>
                  <option value="medium">🟡 Medium</option>
                  <option value="low">🟢 Low</option>
                </select>
                <select
                  className="select"
                  value={filterStatus}
                  onChange={e => setFilterStatus(e.target.value)}
                >
                  <option value="all">All Status</option>
                  {STAGES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
                <span className="bills-filter-count">{displayBills.length} bills</span>
              </div>
            </div>

            <div className="bills-card-row">
              {displayBills.map(bill => (
                <div
                  key={bill.id}
                  className={`bills-bill-card list-style urgency-${bill.urgency}`}
                >
                  <div className="bills-bill-head">
                    <div className="bills-bill-head-meta">
                      <span className="bills-id">{bill.id}</span>
                      <span className={`badge badge-urgency-${bill.urgency}`}>{bill.urgency.toUpperCase()}</span>
                      <span className="bills-chamber">{bill.chamber}</span>
                    </div>
                    <span style={{ color: "var(--color-text-secondary)", fontSize: 12 }}>
                      Introduced {bill.introduced}
                    </span>
                  </div>
                  <div className="bills-bill-title">{bill.title}</div>
                  <div className="bills-topic-chips">
                    {bill.topics.map(t => {
                      const topic = TOPIC_BY_ID[t];
                      if (!topic) return null;
                      return (
                        <span key={t} className="bills-topic-chip">
                          {topic.icon} {topic.label}
                        </span>
                      );
                    })}
                  </div>
                  <div className="bills-bill-meta-row">
                    <div>
                      <span>📌 {bill.status}</span>
                      <span style={{ marginLeft: 12 }}>· Sponsor: {bill.sponsor}</span>
                    </div>
                    <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap" }}>
                      {Object.entries(COMM_TEMPLATES).map(([key, tmpl]) => (
                        <button
                          key={key}
                          className="btn btn-sm"
                          style={commBtnStyle(tmpl.cssVar)}
                          onClick={() => {
                            setCommStrategy({ bill, type: key });
                            setActiveTab("comms");
                            showToast(`Strategy loaded for ${bill.id}`);
                          }}
                        >
                          {tmpl.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* COMM STRATEGY TAB */}
        {activeTab === "comms" && (
          <div className="bills-comms-layout">
            <div className="bills-comms-side">
              <div className="card">
                <h3 className="text-h3" style={{ marginBottom: "var(--space-3)" }}>Select a Bill</h3>
                {relevantBills.map(bill => {
                  const sel = commStrategy?.bill?.id === bill.id;
                  return (
                    <div
                      key={bill.id}
                      className={`bills-pick-item${sel ? " selected" : ""}`}
                      onClick={() => setCommStrategy(prev => ({ ...prev, bill }))}
                    >
                      <div className="bills-pick-head">
                        <span className="bills-pick-id">{bill.id}</span>
                        <span className={`badge badge-urgency-${bill.urgency}`}>{bill.urgency}</span>
                      </div>
                      <div className="bills-pick-title">{bill.title.slice(0, 60)}{bill.title.length > 60 ? "…" : ""}</div>
                    </div>
                  );
                })}
              </div>

              <div className="card">
                <h3 className="text-h3" style={{ marginBottom: "var(--space-3)" }}>Communication Type</h3>
                {Object.entries(COMM_TEMPLATES).map(([key, tmpl]) => {
                  const sel = commStrategy?.type === key;
                  return (
                    <div
                      key={key}
                      className={`bills-pick-item${sel ? " selected" : ""}`}
                      style={sel ? { borderColor: `var(${tmpl.cssVar})` } : undefined}
                      onClick={() => setCommStrategy(prev => ({ ...prev, type: key }))}
                    >
                      <div style={{ fontSize: 13, fontWeight: 600, color: "var(--color-text)", marginBottom: 4 }}>
                        {tmpl.label}
                      </div>
                      <div style={{ fontSize: 11, color: "var(--color-text-secondary)", marginBottom: 6 }}>
                        📅 {tmpl.cadence}
                      </div>
                      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                        {tmpl.channels.map(ch => (
                          <span key={ch} className="tag">{ch}</span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div>
              {commStrategy?.bill && commStrategy?.type ? (
                <div>
                  <div className="card bills-comm-template-card">
                    <div className="bills-template-head">
                      <div>
                        <h2 className="text-h3">{COMM_TEMPLATES[commStrategy.type].label}</h2>
                        <p style={{ color: "var(--color-text-secondary)", fontSize: 13, marginTop: 4 }}>
                          Template for {commStrategy.bill.id} · {commStrategy.bill.title}
                        </p>
                      </div>
                      <button
                        className="btn btn-sm"
                        style={commBtnStyle(COMM_TEMPLATES[commStrategy.type].cssVar)}
                        onClick={() => {
                          navigator.clipboard?.writeText(COMM_TEMPLATES[commStrategy.type].template(commStrategy.bill));
                          showToast("✅ Copied to clipboard!");
                        }}
                      >
                        📋 Copy Template
                      </button>
                    </div>
                    <div className="bills-template-body">
                      {COMM_TEMPLATES[commStrategy.type].template(commStrategy.bill)}
                    </div>
                  </div>

                  <div className="card">
                    <h3 className="text-h3" style={{ marginBottom: "var(--space-4)" }}>Cadence &amp; Channel Matrix</h3>
                    <div className="bills-cadence-grid">
                      {[
                        { phase: "Bill Introduced", action: "Internal note + add to tracker", channel: "Notion / Task", timing: "Within 24hrs" },
                        { phase: "Committee Hearing", action: "Submit public comment", channel: "Legislature.ca.gov", timing: "Before hearing date" },
                        { phase: "Passes Committee", action: "Client alert email", channel: "Email / CRM", timing: "Within 48hrs" },
                        { phase: "Passes One Chamber", action: "LinkedIn thought leadership", channel: "LinkedIn + Substack", timing: "Within 72hrs" },
                        { phase: "Passes Both Chambers", action: "Full client briefing + webinar invite", channel: "Email + Zoom", timing: "Within 1 week" },
                        { phase: "Signed by Governor", action: "Compliance guide + service offering", channel: "All channels", timing: "Within 2 weeks" },
                      ].map(row => (
                        <div key={row.phase} className="bills-cadence-tile">
                          <div className="bills-cadence-phase">{row.phase}</div>
                          <div className="bills-cadence-action">{row.action}</div>
                          <div className="bills-cadence-meta">📍 {row.channel}</div>
                          <div className="bills-cadence-meta">⏱ {row.timing}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="card bills-empty">
                  <div className="bills-empty-icon">📣</div>
                  <h3>Select a Bill + Communication Type</h3>
                  <p>Choose from the left panel to generate your communication template.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Toast */}
      {toast && (
        <div className="toast info show">
          {toast}
        </div>
      )}
    </div>
  );
}
