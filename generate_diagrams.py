import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUT_DIR = "report_assets"
os.makedirs(OUT_DIR, exist_ok=True)

# 1. Use Case Diagram
def create_use_case_diagram():
    fig, ax = plt.subplots(figsize=(10, 11), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 13)
    ax.axis("off")
    
    # System boundary
    rect = patches.FancyBboxPatch((2.2, 0.5), 5.6, 11.8, boxstyle="round,pad=0.2",
                                  linewidth=1.5, edgecolor="#2563eb", facecolor="#f8fafc")
    ax.add_patch(rect)
    ax.text(5.0, 12.0, "ShieldScan Detection System", ha="center", va="center", fontsize=14, fontweight="bold", color="#1e3a8a")
    
    use_cases = [
        ("Login / Authentication", 11.2),
        ("User Registration", 10.4),
        ("Quick Text & URL Scan", 9.6),
        ("Website Crawler Analysis", 8.8),
        ("Connect Gmail (OAuth 2.0)", 8.0),
        ("Manual Gmail Sync", 7.2),
        ("View Threat & Risk Reports", 6.4),
        ("Manage Domain Whitelist/Blacklist", 5.6),
        ("Inspect Audit Logs", 4.8),
        ("Retrain & Deploy ML Models", 4.0),
        ("Automated Gmail Sync (Cron)", 3.2),
        ("Feature Extraction & Scoring", 2.4),
        ("Hybrid ML Prediction", 1.6),
        ("Sign Out", 0.9)
    ]
    
    for text, y in use_cases:
        ellipse = patches.Ellipse((5.0, y), 3.8, 0.6, edgecolor="#3b82f6", facecolor="#ffffff", linewidth=1.2)
        ax.add_patch(ellipse)
        ax.text(5.0, y, text, ha="center", va="center", fontsize=9.5, fontweight="500", color="#0f172a")

    # Stick figure helper
    def draw_actor(x, y, name, color="#1e293b"):
        ax.plot(x, y + 0.35, "o", markersize=14, color=color, fillstyle="none", markeredgewidth=2)
        ax.plot([x, x], [y + 0.23, y - 0.25], color=color, linewidth=2)
        ax.plot([x - 0.25, x + 0.25], [y + 0.05, y + 0.05], color=color, linewidth=2)
        ax.plot([x, x - 0.22], [y - 0.25, y - 0.65], color=color, linewidth=2)
        ax.plot([x, x + 0.22], [y - 0.25, y - 0.65], color=color, linewidth=2)
        ax.text(x, y - 0.85, name, ha="center", va="top", fontsize=11, fontweight="bold", color=color)

    # Actors
    draw_actor(0.9, 9.2, "End User\n(Student/Staff)", "#1e40af")
    draw_actor(0.9, 5.0, "System Admin", "#b91c1c")
    draw_actor(9.1, 7.5, "System Core\n(Detection Engine)", "#047857")
    draw_actor(9.1, 2.5, "Google Cloud\n(Gmail & OAuth API)", "#d97706")

    # Lines User -> Use cases
    user_targets = [11.2, 10.4, 9.6, 8.8, 8.0, 7.2, 6.4, 0.9]
    for y in user_targets:
        ax.annotate("", xy=(3.1, y), xytext=(1.15, 9.2),
                    arrowprops=dict(arrowstyle="->", color="#3b82f6", lw=1.1, alpha=0.85))

    # Lines Admin -> Use cases
    admin_targets = [11.2, 5.6, 4.8, 4.0, 6.4, 0.9]
    for y in admin_targets:
        ax.annotate("", xy=(3.1, y), xytext=(1.15, 5.0),
                    arrowprops=dict(arrowstyle="->", color="#ef4444", lw=1.1, alpha=0.85))

    # Lines System Core -> Use cases
    system_targets = [9.6, 8.8, 3.2, 2.4, 1.6, 6.4]
    for y in system_targets:
        ax.annotate("", xy=(6.9, y), xytext=(8.85, 7.5),
                    arrowprops=dict(arrowstyle="->", color="#10b981", lw=1.1, alpha=0.85))

    # Lines Google API -> Use cases
    api_targets = [8.0, 7.2, 3.2]
    for y in api_targets:
        ax.annotate("", xy=(6.9, y), xytext=(8.85, 2.5),
                    arrowprops=dict(arrowstyle="->", color="#f59e0b", lw=1.1, alpha=0.85))

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "use_case_diagram.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print("Created use_case_diagram.png")

# 2. System Architecture Diagram
def create_architecture_diagram():
    fig, ax = plt.subplots(figsize=(11, 8.5), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 9.5)
    ax.axis("off")

    tiers = [
        ("Presentation Layer (Client Browser UI)", 7.6, 1.4, "#eff6ff", "#1d4ed8", [
            "HTML5 & Jinja2 Templates", "Bootstrap 5 Styling", "Chart.js Visualizations",
            "Dashboard Quick Scan UI", "Website Link Analyzer UI", "Admin Control Panel"
        ]),
        ("Application & Routing Layer (Flask 3.x WSGI / Serverless)", 5.2, 1.7, "#f0fdf4", "#15803d", [
            "Auth Blueprint (/auth)", "Dashboard Blueprint (/)", "Crawler Blueprint (/crawler)",
            "Gmail OAuth & Sync (/gmail)", "Admin Blueprint (/admin)", "Session & CSRF Handler"
        ]),
        ("Security & Machine Learning Inference Engine", 2.7, 1.8, "#faf5ff", "#7e22ce", [
            "URL Heuristic Feature Extractor", "TF-IDF + Multinomial Naive Bayes (Spam)",
            "Random Forest Classifier (Phishing)", "Multi-Factor Risk Assessment Engine",
            "Trusted / Blocked Domain Validator", "HTML Page Link Analyzer"
        ]),
        ("Data Persistence & External Services Layer", 0.4, 1.6, "#fffbeb", "#b45309", [
            "MongoDB Atlas Cluster / Local MongoDB (Users, Scans, Logs)",
            "Scikit-Learn Pre-trained Models (.joblib / .pkl)",
            "Google Gmail API v1 (Readonly OAuth 2.0)",
            "Vercel Serverless Hosting Platform"
        ])
    ]

    for title, y, h, bg, border, items in tiers:
        rect = patches.FancyBboxPatch((0.5, y), 10.0, h, boxstyle="round,pad=0.15",
                                      linewidth=1.8, edgecolor=border, facecolor=bg)
        ax.add_patch(rect)
        ax.text(0.8, y + h - 0.25, title, fontsize=11.5, fontweight="bold", color=border)
        
        # Sub items
        cols = 3
        for idx, item in enumerate(items):
            col = idx % cols
            row = idx // cols
            item_x = 0.8 + col * 3.3
            item_y = y + h - 0.65 - row * 0.42
            ax.text(item_x, item_y, f"•  {item}", fontsize=9.2, color="#1e293b")

    # Connectors
    for y_pos in [7.6, 5.2, 2.7]:
        ax.annotate("", xy=(5.5, y_pos), xytext=(5.5, y_pos + 0.3),
                    arrowprops=dict(arrowstyle="<|-|>", color="#475569", lw=2))

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "architecture_diagram.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print("Created architecture_diagram.png")

# 3. Class Diagram
def create_class_diagram():
    fig, ax = plt.subplots(figsize=(11, 8.5), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 9)
    ax.axis("off")

    classes = [
        ("User (Document)", 0.5, 5.2, 2.8, 3.2, "#eff6ff", "#1e40af", [
            "- id: ObjectId", "- username: String", "- email: String",
            "- password_hash: String", "- gmail_connected: Boolean",
            "- gmail_credentials: Dict", "- created_at: DateTime",
            "---------------------------", "+ set_password(pwd)", "+ check_password(pwd)",
            "+ update_gmail_sync()"
        ]),
        ("Scan (Document)", 4.1, 5.2, 3.0, 3.2, "#f0fdf4", "#166534", [
            "- id: ObjectId", "- user_id: String", "- input_text: String",
            "- input_type: String", "- label: String", "- confidence: Float",
            "- threat_level: String", "- risk_score: Float", "- reasons_json: String",
            "---------------------------", "+ save()", "+ to_dict()"
        ]),
        ("AdminUser (Document)", 7.7, 5.2, 2.8, 3.2, "#fef2f2", "#991b1b", [
            "- id: ObjectId", "- username: String", "- email: String",
            "- password_hash: String", "- is_active: Boolean",
            "- created_at: DateTime",
            "---------------------------", "+ set_password(pwd)", "+ check_password(pwd)"
        ]),
        ("CrawlerLog (Document)", 0.5, 0.8, 2.8, 3.4, "#fdf4ff", "#86198f", [
            "- id: ObjectId", "- user_id: String", "- seed_url: String",
            "- pages_crawled: Int", "- links_found: Int", "- report_json: String",
            "- status: String", "- created_at: DateTime",
            "---------------------------", "+ get_summary()"
        ]),
        ("SystemLog (Document)", 4.1, 0.8, 3.0, 3.4, "#fff7ed", "#9a3412", [
            "- id: ObjectId", "- level: String", "- category: String",
            "- message: String", "- details: String", "- created_at: DateTime",
            "---------------------------", "+ write_log(level, msg)"
        ]),
        ("ModelManager (Service)", 7.7, 0.8, 2.8, 3.4, "#f8fafc", "#334155", [
            "- spam_pipeline: Pipeline", "- phishing_rf: Model",
            "- url_extractor: Extractor",
            "---------------------------", "+ predict(input_data)", "+ compute_risk()",
            "+ retrain_spam_model()", "+ retrain_phishing_model()"
        ])
    ]

    for name, x, y, w, h, bg, border, fields in classes:
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                                      linewidth=1.5, edgecolor=border, facecolor=bg)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h - 0.25, name, ha="center", va="center", fontsize=10, fontweight="bold", color=border)
        ax.plot([x, x + w], [y + h - 0.45, y + h - 0.45], color=border, lw=1)
        
        for idx, field in enumerate(fields):
            ax.text(x + 0.15, y + h - 0.7 - idx * 0.24, field, fontsize=8.2, color="#0f172a", family="monospace")

    # Connectors
    ax.annotate("1..* scans", xy=(4.1, 6.8), xytext=(3.3, 6.8),
                arrowprops=dict(arrowstyle="->", color="#1e40af", lw=1.5))
    ax.annotate("1..* crawls", xy=(1.9, 4.2), xytext=(1.9, 5.2),
                arrowprops=dict(arrowstyle="->", color="#1e40af", lw=1.5))

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "class_diagram.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print("Created class_diagram.png")

# 4. Sequence Diagram
def create_sequence_diagram():
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 9)
    ax.axis("off")

    lifelines = [
        ("User Client", 1.2),
        ("Flask Route (/scan)", 3.5),
        ("ML Inference Engine", 6.0),
        ("MongoDB Atlas", 8.8)
    ]

    for name, x in lifelines:
        rect = patches.FancyBboxPatch((x - 0.9, 8.2), 1.8, 0.6, boxstyle="round,pad=0.08",
                                      linewidth=1.2, edgecolor="#1e3a8a", facecolor="#dbeafe")
        ax.add_patch(rect)
        ax.text(x, 8.5, name, ha="center", va="center", fontsize=9.5, fontweight="bold", color="#1e3a8a")
        ax.plot([x, x], [8.2, 0.5], "--", color="#94a3b8", lw=1.2)

    messages = [
        (1.2, 3.5, 7.6, "1: POST /scan (input_data)", True),
        (3.5, 6.0, 6.8, "2: run_prediction(input_data)", True),
        (6.0, 6.0, 6.0, "3: extract_features() + classify()", False),
        (6.0, 6.0, 5.3, "4: calculate_risk_score()", False),
        (6.0, 3.5, 4.6, "5: return {type, label, threat_level}", False),
        (3.5, 8.8, 3.8, "6: Scan.save(user_id, result)", True),
        (8.8, 3.5, 3.0, "7: return success ObjectId", False),
        (3.5, 1.2, 2.2, "8: HTTP 200 JSON {ok: true, result, stats}", False)
    ]

    for x1, x2, y, msg, is_fwd in messages:
        if x1 == x2:
            # Self call loop
            rect = patches.FancyBboxPatch((x1 - 0.1, y - 0.15), 1.6, 0.35, boxstyle="round,pad=0.05",
                                          edgecolor="#8b5cf6", facecolor="#ede9fe", lw=1)
            ax.add_patch(rect)
            ax.text(x1 + 0.7, y, msg, fontsize=8.2, color="#4c1d95")
        else:
            linestyle = "-" if is_fwd else "--"
            color = "#2563eb" if is_fwd else "#059669"
            ax.annotate("", xy=(x2, y), xytext=(x1, y),
                        arrowprops=dict(arrowstyle="->", color=color, lw=1.3, linestyle=linestyle))
            ax.text((x1 + x2)/2, y + 0.12, msg, ha="center", va="bottom", fontsize=8.4, color="#0f172a")

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "sequence_diagram.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print("Created sequence_diagram.png")

# 5. Activity Diagram
def create_activity_diagram():
    fig, ax = plt.subplots(figsize=(9, 10), dpi=300)
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 11)
    ax.axis("off")

    # Start node
    circle = patches.Circle((4.5, 10.3), 0.22, color="#0f172a")
    ax.add_patch(circle)
    ax.text(4.5, 10.7, "User Initiates Scan Request", ha="center", fontsize=10, fontweight="bold")

    nodes = [
        ("Input Validation & Sanitization", 9.3, "#eff6ff", "#1d4ed8"),
        ("Detect Content Type (URL vs Text)", 8.2, "#fef3c7", "#d97706"),
        ("Extract URL Lexical & Host Features\n(IP, Entropy, Subdomains, TLD)", 6.7, "#f0fdf4", "#166534"),
        ("Tokenize & TF-IDF Vectorization\n(N-Grams, Lowercase, Lemmatize)", 6.7, "#faf5ff", "#7e22ce"),
        ("Random Forest Phishing Classifier", 5.2, "#f0fdf4", "#166534"),
        ("Multinomial Naive Bayes Spam Classifier", 5.2, "#faf5ff", "#7e22ce"),
        ("Heuristic & Domain Whitelist Cross-Check", 3.8, "#eff6ff", "#1d4ed8"),
        ("Compute Unified Threat Level & Risk Score\n(Safe / Suspicious / Dangerous)", 2.4, "#fff7ed", "#ea580c"),
        ("Persist Scan Record to MongoDB Atlas", 1.2, "#f8fafc", "#334155")
    ]

    # Node 1
    rect = patches.FancyBboxPatch((2.2, 9.0), 4.6, 0.6, boxstyle="round,pad=0.08", edgecolor="#1d4ed8", facecolor="#eff6ff", lw=1.4)
    ax.add_patch(rect)
    ax.text(4.5, 9.3, nodes[0][0], ha="center", va="center", fontsize=9.2, fontweight="500")
    ax.annotate("", xy=(4.5, 9.6), xytext=(4.5, 10.05), arrowprops=dict(arrowstyle="->", lw=1.3))

    # Decision Diamond
    diamond = patches.Polygon([[4.5, 8.6], [6.2, 8.1], [4.5, 7.6], [2.8, 8.1]], closed=True, edgecolor="#d97706", facecolor="#fef3c7", lw=1.5)
    ax.add_patch(diamond)
    ax.text(4.5, 8.1, "Is Input a URL?", ha="center", va="center", fontsize=9.2, fontweight="bold", color="#78350f")
    ax.annotate("", xy=(4.5, 8.6), xytext=(4.5, 9.0), arrowprops=dict(arrowstyle="->", lw=1.3))

    # Branches (Left = URL, Right = Text)
    # Left: URL Feature Extraction
    rect_url = patches.FancyBboxPatch((0.5, 6.3), 3.4, 0.8, boxstyle="round,pad=0.08", edgecolor="#166534", facecolor="#f0fdf4", lw=1.3)
    ax.add_patch(rect_url)
    ax.text(2.2, 6.7, nodes[2][0], ha="center", va="center", fontsize=8.2, fontweight="500")
    ax.annotate("", xy=(2.2, 7.1), xytext=(2.8, 8.1), arrowprops=dict(arrowstyle="->", lw=1.3))
    ax.text(2.4, 7.7, "[Yes: URL]", fontsize=8.5, fontweight="bold", color="#166534")

    # Right: Text Preprocessing
    rect_txt = patches.FancyBboxPatch((5.1, 6.3), 3.4, 0.8, boxstyle="round,pad=0.08", edgecolor="#7e22ce", facecolor="#faf5ff", lw=1.3)
    ax.add_patch(rect_txt)
    ax.text(6.8, 6.7, nodes[3][0], ha="center", va="center", fontsize=8.2, fontweight="500")
    ax.annotate("", xy=(6.8, 7.1), xytext=(6.2, 8.1), arrowprops=dict(arrowstyle="->", lw=1.3))
    ax.text(6.4, 7.7, "[No: Text]", fontsize=8.5, fontweight="bold", color="#7e22ce")

    # Left Model
    rect_rf = patches.FancyBboxPatch((0.5, 4.9), 3.4, 0.6, boxstyle="round,pad=0.08", edgecolor="#166534", facecolor="#f0fdf4", lw=1.3)
    ax.add_patch(rect_rf)
    ax.text(2.2, 5.2, nodes[4][0], ha="center", va="center", fontsize=8.5, fontweight="500")
    ax.annotate("", xy=(2.2, 5.5), xytext=(2.2, 6.3), arrowprops=dict(arrowstyle="->", lw=1.3))

    # Right Model
    rect_nb = patches.FancyBboxPatch((5.1, 4.9), 3.4, 0.6, boxstyle="round,pad=0.08", edgecolor="#7e22ce", facecolor="#faf5ff", lw=1.3)
    ax.add_patch(rect_nb)
    ax.text(6.8, 5.2, nodes[5][0], ha="center", va="center", fontsize=8.5, fontweight="500")
    ax.annotate("", xy=(6.8, 5.5), xytext=(6.8, 6.3), arrowprops=dict(arrowstyle="->", lw=1.3))

    # Merge at Risk Evaluation
    rect_wl = patches.FancyBboxPatch((2.0, 3.5), 5.0, 0.6, boxstyle="round,pad=0.08", edgecolor="#1d4ed8", facecolor="#eff6ff", lw=1.3)
    ax.add_patch(rect_wl)
    ax.text(4.5, 3.8, nodes[6][0], ha="center", va="center", fontsize=9.0, fontweight="500")
    ax.annotate("", xy=(4.0, 4.1), xytext=(2.2, 4.9), arrowprops=dict(arrowstyle="->", lw=1.3))
    ax.annotate("", xy=(5.0, 4.1), xytext=(6.8, 4.9), arrowprops=dict(arrowstyle="->", lw=1.3))

    # Unified Threat
    rect_thr = patches.FancyBboxPatch((1.6, 2.0), 5.8, 0.8, boxstyle="round,pad=0.08", edgecolor="#ea580c", facecolor="#fff7ed", lw=1.4)
    ax.add_patch(rect_thr)
    ax.text(4.5, 2.4, nodes[7][0], ha="center", va="center", fontsize=9.2, fontweight="bold", color="#9a3412")
    ax.annotate("", xy=(4.5, 2.8), xytext=(4.5, 3.5), arrowprops=dict(arrowstyle="->", lw=1.3))

    # Persist
    rect_db = patches.FancyBboxPatch((2.2, 0.8), 4.6, 0.6, boxstyle="round,pad=0.08", edgecolor="#334155", facecolor="#f8fafc", lw=1.3)
    ax.add_patch(rect_db)
    ax.text(4.5, 1.1, nodes[8][0], ha="center", va="center", fontsize=9.0, fontweight="500")
    ax.annotate("", xy=(4.5, 1.4), xytext=(4.5, 2.0), arrowprops=dict(arrowstyle="->", lw=1.3))

    # End Node
    circle_outer = patches.Circle((4.5, 0.25), 0.22, color="#0f172a", fill=False, lw=1.8)
    circle_inner = patches.Circle((4.5, 0.25), 0.14, color="#0f172a")
    ax.add_patch(circle_outer)
    ax.add_patch(circle_inner)
    ax.annotate("", xy=(4.5, 0.47), xytext=(4.5, 0.8), arrowprops=dict(arrowstyle="->", lw=1.3))

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "activity_diagram.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print("Created activity_diagram.png")

# 6. Component Diagram
def create_component_diagram():
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8.5)
    ax.axis("off")

    comps = [
        ("Web Frontend Component\n(Bootstrap / Chart.js)", 1.0, 5.5, "#dbeafe", "#1e40af"),
        ("Flask Core Controller\n(Blueprints & Auth)", 4.0, 5.5, "#dcfce7", "#15803d"),
        ("Crawler & Link Analyzer\n(BeautifulSoup / Requests)", 7.0, 5.5, "#fef3c7", "#b45309"),
        ("Spam Classifier Component\n(TF-IDF + Naive Bayes)", 1.0, 2.2, "#f3e8ff", "#6b21a8"),
        ("Phishing URL Classifier\n(Random Forest Model)", 4.0, 2.2, "#ffe4e6", "#be123c"),
        ("Risk Assessment Engine\n(Multi-Factor Scorer)", 7.0, 2.2, "#ffedd5", "#c2410c"),
        ("MongoDB Atlas Connector\n(MongoEngine ORM)", 4.0, 0.4, "#f1f5f9", "#334155")
    ]

    for title, x, y, bg, border in comps:
        rect = patches.FancyBboxPatch((x, y), 2.4, 1.4, boxstyle="square,pad=0.1",
                                      edgecolor=border, facecolor=bg, lw=1.5)
        ax.add_patch(rect)
        # Component icon tabs
        tab1 = patches.Rectangle((x - 0.15, y + 0.8), 0.3, 0.25, edgecolor=border, facecolor="#ffffff", lw=1)
        tab2 = patches.Rectangle((x - 0.15, y + 0.3), 0.3, 0.25, edgecolor=border, facecolor="#ffffff", lw=1)
        ax.add_patch(tab1)
        ax.add_patch(tab2)
        ax.text(x + 1.2, y + 0.7, title, ha="center", va="center", fontsize=8.8, fontweight="bold", color=border)

    # Connector lines
    ax.annotate("", xy=(3.9, 6.2), xytext=(3.4, 6.2), arrowprops=dict(arrowstyle="<|-|>", lw=1.4))
    ax.annotate("", xy=(6.9, 6.2), xytext=(6.4, 6.2), arrowprops=dict(arrowstyle="<|-|>", lw=1.4))
    ax.annotate("", xy=(2.2, 3.7), xytext=(4.5, 5.4), arrowprops=dict(arrowstyle="<|-|>", lw=1.4))
    ax.annotate("", xy=(5.2, 3.7), xytext=(5.2, 5.4), arrowprops=dict(arrowstyle="<|-|>", lw=1.4))
    ax.annotate("", xy=(8.2, 3.7), xytext=(5.9, 5.4), arrowprops=dict(arrowstyle="<|-|>", lw=1.4))
    ax.annotate("", xy=(5.2, 1.9), xytext=(5.2, 2.1), arrowprops=dict(arrowstyle="<|-|>", lw=1.4))

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "component_diagram.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print("Created component_diagram.png")

# 7. Deployment Diagram
def create_deployment_diagram():
    fig, ax = plt.subplots(figsize=(10, 7.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")

    nodes = [
        ("<<device>>\nClient Workstation\n\n[ Web Browser ]\n(Chrome / Edge / Firefox)\nHTTPS TLS 1.3", 0.6, 3.5, 2.6, 3.4, "#eff6ff", "#1d4ed8"),
        ("<<cloud>>\nVercel Serverless Cloud\n\n[ Python 3.12 Lambda Runtime ]\n• Flask WSGI Application\n• Scikit-Learn Inference Engine\n• Pre-trained ML Artifacts (.joblib)", 3.8, 3.2, 3.0, 4.0, "#f0fdf4", "#15803d"),
        ("<<cloud database>>\nMongoDB Atlas Managed Cluster\n\n[ MongoDB 7.0 ReplicaSet ]\n• Users & Admin Collections\n• Scan History & Stats\n• Domain Lists & Audit Logs", 7.2, 4.6, 2.5, 3.0, "#fffbeb", "#b45309"),
        ("<<external SaaS>>\nGoogle Cloud Platform\n\n[ Google Workspace APIs ]\n• OAuth 2.0 Auth Server\n• Gmail API v1 (Readonly Mail)", 7.2, 0.8, 2.5, 3.0, "#faf5ff", "#7e22ce")
    ]

    for title, x, y, w, h, bg, border in nodes:
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                                      edgecolor=border, facecolor=bg, lw=1.6)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, title, ha="center", va="center", fontsize=8.6, fontweight="500", color="#0f172a")

    # Connectors
    ax.annotate("HTTPS / WSS\n(Port 443)", xy=(3.7, 5.2), xytext=(3.3, 5.2),
                arrowprops=dict(arrowstyle="<|-|>", color="#1d4ed8", lw=1.6), fontsize=8.0, ha="center")
    ax.annotate("MongoDB Wire Protocol\nTLS / mongodb+srv", xy=(7.1, 6.0), xytext=(6.9, 6.0),
                arrowprops=dict(arrowstyle="<|-|>", color="#b45309", lw=1.6), fontsize=8.0, ha="center")
    ax.annotate("REST / OAuth 2.0\nToken Exchange", xy=(7.1, 2.3), xytext=(6.3, 3.3),
                arrowprops=dict(arrowstyle="<|-|>", color="#7e22ce", lw=1.6), fontsize=8.0, ha="center")

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "deployment_diagram.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print("Created deployment_diagram.png")

if __name__ == "__main__":
    create_use_case_diagram()
    create_architecture_diagram()
    create_class_diagram()
    create_sequence_diagram()
    create_activity_diagram()
    create_component_diagram()
    create_deployment_diagram()
