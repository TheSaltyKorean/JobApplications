"""
Randy Walker's profile data extracted from his 4 resumes.
This is the single source of truth for all Q&A answering and form filling.
"""

# ─────────────────────────────────────────────────────────
# CONTACT INFO
# ─────────────────────────────────────────────────────────
CONTACT = {
    "first_name": "Randy",
    "last_name": "Walker",
    "full_name": "Randy Walker",
    "email_primary": "randy.walker@live.com",
    "email_screening": "jobs.randywalker@outlook.com",   # Used for Indian firm screening
    "phone_primary": "(469) 679-3575",
    "phone_screening": "(479) 871-2172",                 # Used for Indian firm screening
    "city": "Austin",
    "state": "TX",
    "state_full": "Texas",
    "zip": "78759",
    "location": "Austin, TX 78759",
    "linkedin": "https://www.linkedin.com/in/randywalker",
    "github": "https://github.com/randywalker",
    "website": "https://randywalker.com",
    "authorized_to_work": True,
    "requires_sponsorship": False,
    "willing_to_relocate": False,
    "preferred_work_type": "Hybrid or Remote",
}

# ─────────────────────────────────────────────────────────
# RESUME FILES  (relative to app root)
# ─────────────────────────────────────────────────────────
RESUMES = {
    "executive":  "resumes/2025 Randy Walker - IT Executive.pdf",
    "it_manager": "resumes/2025 Randy Walker - Tech Leader.pdf",
    "cloud":      "resumes/2025 Randy Walker - Cloud.pdf",
    "contract":   "resumes/2025 Randy Walker - Cloud Contract.pdf",  # Indian firm screening
}

# ─────────────────────────────────────────────────────────
# EDUCATION
# ─────────────────────────────────────────────────────────
EDUCATION = [
    {
        "school": "University of Arkansas",
        "degree": "Computer Science",
        "degree_type": "Some College",
        "field": "Computer Science",
        "start_year": 1992,
        "end_year": 1995,
        "graduated": False,
        "gpa": None,
    }
]

# ─────────────────────────────────────────────────────────
# CERTIFICATIONS
# ─────────────────────────────────────────────────────────
CERTIFICATIONS = [
    {"name": "AZ-900: Azure Fundamentals", "issuer": "Microsoft", "year": None},
    {"name": "DP-900: Azure Data Fundamentals", "issuer": "Microsoft", "year": None},
]

# ─────────────────────────────────────────────────────────
# SKILLS  (used for job matching)
# ─────────────────────────────────────────────────────────
SKILLS = [
    # Cloud
    "Azure", "Microsoft Azure", "Azure IaaS", "Azure PaaS", "Azure VMs",
    "Azure Functions", "Azure App Services", "Azure SQL", "Azure AD",
    "Azure Active Directory", "Azure DevOps", "Azure Monitor", "Azure Synapse",
    "Azure Service Bus", "Azure CDN", "Azure Policy", "Azure Cost Management",
    "IBM Cloud", "Cloud Architecture", "Cloud Strategy", "Cloud Operations",
    "Cloud Governance", "Cloud Migration", "Cloud Transformation",
    "Multi-Cloud", "Hybrid Cloud", "Cloud Center of Excellence",
    # DevOps / Infrastructure
    "DevOps", "CI/CD", "Terraform", "Infrastructure as Code", "IaC",
    "GitHub", "GitHub Actions", "Azure Pipelines", "DevSecOps",
    "Containerization", "Docker", "Kubernetes", "PaaS", "SaaS",
    "Zero Trust", "Zero Trust Architecture",
    # IT Leadership / Management
    "IT Strategy", "IT Operations", "IT Infrastructure", "IT Governance",
    "IT Management", "Technology Leadership", "Digital Transformation",
    "Enterprise Architecture", "Solution Architecture",
    "Budget Management", "FinOps", "Cost Optimization", "TCO",
    "Vendor Management", "Contract Management", "SLA Management",
    # Security / Compliance
    "Cybersecurity", "Information Security", "Security",
    "HIPAA", "HITRUST", "PCI-DSS", "ISO27001", "NIST",
    "Compliance", "Risk Management", "Governance",
    "Ransomware Recovery", "Incident Response",
    # Development / Software
    ".NET", ".NET Core", "C#", "MVC", "REST API",
    "ETL", "Data Integration", "Power BI", "SQL",
    "Azure Data Warehouse", "Synapse Analytics",
    "SDLC", "Agile", "Scrum", "Waterfall",
    # Business / Leadership
    "Cross-functional Leadership", "Team Leadership", "Team Building",
    "Mentoring", "Stakeholder Management", "Executive Communication",
    "Project Management", "Program Management", "Change Management",
    "Business Alignment", "Strategic Planning",
    "Microsoft 365", "M365", "Office 365", "SharePoint", "Teams",
    "MDM", "Intune", "Microsoft Intune",
]

# ─────────────────────────────────────────────────────────
# WORK HISTORY  (chronological, most recent first)
# ─────────────────────────────────────────────────────────
WORK_HISTORY = [
    {
        "title": "Vice President of IT Strategy & Infrastructure",
        "company": "Bizzz Buzzz Technology & Consulting",
        "start": "May 2024",
        "end": "Present",
        "current": True,
        "years": 1,
        "summary": (
            "Led strategic consulting engagements for healthcare and enterprise clients, "
            "including modernization of mission-critical legacy platforms and infrastructure governance. "
            "Architected a multi-phase cloud migration roadmap for a core healthcare platform "
            "resulting in a projected $9M ROI."
        ),
    },
    {
        "title": "Head of Cloud Architecture and Operations",
        "company": "Performance Food Group",
        "start": "Oct 2021",
        "end": "Feb 2024",
        "current": False,
        "years": 2.5,
        "summary": (
            "Directed enterprise-wide cloud transformation for a Fortune 80 company with $50B+ revenue. "
            "Oversaw a $12MM annual cloud infrastructure budget and led architects and engineers across "
            "security, DevOps, and operations. Migrated 1,200+ servers to Azure and IBM Cloud. "
            "Founded and led the Cloud Center of Excellence."
        ),
    },
    {
        "title": "Cloud Operations Leader",
        "company": "Advanced Solutions International, Inc.",
        "start": "Oct 2020",
        "end": "Sep 2021",
        "current": False,
        "years": 1,
        "summary": (
            "Modernized and secured global cloud operations, transforming a legacy IT environment "
            "into a resilient, security-first Azure ecosystem. Led ransomware remediation, established "
            "security action team, coordinated PCI-DSS and ISO27001 audits."
        ),
    },
    {
        "title": "Azure Architect Director",
        "company": "Cognizant / TriZetto Provider Solutions",
        "start": "Aug 2019",
        "end": "Aug 2020",
        "current": False,
        "years": 1,
        "summary": (
            "Directed Azure architecture and security strategy for healthcare technology division. "
            "Managed $5M annual Azure budget and 7.4 million cloud assets. "
            "Ensured HIPAA and HITRUST compliance across PHI workloads."
        ),
    },
    {
        "title": "Founder & President",
        "company": "Harvest Data Corp",
        "start": "Oct 2005",
        "end": "Sep 2019",
        "current": False,
        "years": 14,
        "summary": (
            "Built and scaled a Micro ISV delivering automated data integration and BI solutions "
            "for major retailers including Walmart and Dollar General. Led product strategy, "
            "cloud architecture, development, and operations. Selected as Microsoft Azure Advisor. "
            "Awarded $460K+ in Microsoft BizSpark grants."
        ),
    },
    {
        "title": "Co-Founder & President",
        "company": "EZ Family Health",
        "start": "Jun 2016",
        "end": "Jun 2018",
        "current": False,
        "years": 2,
        "summary": (
            "Co-founded a healthcare patient portal startup. Built mobile-friendly cloud-based platform "
            "with end-to-end encryption, HIPAA compliance, and Angular frontend."
        ),
    },
]

YEARS_OF_EXPERIENCE = 20   # Total career years
MANAGEMENT_YEARS = 10      # Years in management roles
BUDGET_MANAGED = "$12MM"   # Largest budget managed
TEAM_SIZE_MAX = 30         # Largest team led

# ─────────────────────────────────────────────────────────
# AWARDS & ACTIVITIES
# ─────────────────────────────────────────────────────────
AWARDS = [
    "ASP Insider (2016 – present)",
    "Microsoft MVP Award (2008 – 2017)",
    "Microsoft Azure Advisor – Early adopter providing critical feedback (NDA-only group)",
    "$460,000+ Microsoft BizSpark grants recognizing technical innovation and startup excellence",
]

ACTIVITIES = [
    "Northwest Arkansas Developer Group, Co-founder & Board Member (2005 – 2020)",
    "INETA (International .NET Association), Membership Mentor & Board Member (2007 – 2009)",
    "Conference Speaker – local, regional, and national events including Microsoft TechEd (2007 – present)",
]

# ─────────────────────────────────────────────────────────
# COMMON QUESTION ANSWERS  (pre-built for automation)
# ─────────────────────────────────────────────────────────
COMMON_ANSWERS = {
    # Salary / compensation
    "salary_expectation": "180000",           # Update in settings
    "salary_min": "150000",
    "salary_max": "250000",
    "hourly_rate": "120",                     # For contract roles

    # Work preferences
    "start_date": "2 weeks",
    "notice_period": "2 weeks",
    "willing_to_relocate": "No",
    "remote_preference": "Remote or Hybrid",
    "work_authorization": "Yes, I am authorized to work in the United States",
    "sponsorship_required": "No",
    "veteran_status": "I am not a veteran",
    "disability_status": "I choose not to disclose",
    "gender": "Male",
    "ethnicity": "I choose not to disclose",

    # Professional
    "years_of_experience": "20",
    "management_experience": "Yes, I have 10+ years of management experience",
    "largest_team": "25-30 engineers and architects",
    "largest_budget": "$12 million annually",
    "highest_education": "Some College – Computer Science, University of Arkansas",

    # Cover letter snippets
    "why_interested_template": (
        "I am excited about this opportunity because it aligns well with my 20 years of experience "
        "in cloud architecture, IT strategy, and leading high-performing infrastructure teams. "
        "My background managing enterprise-scale Azure environments, including a $12MM annual budget "
        "at a Fortune 80 company, positions me to deliver immediate value in this role."
    ),

    # Common behavioral answers
    "greatest_strength": (
        "My ability to bridge technical strategy with business outcomes. I translate complex infrastructure "
        "decisions into language executives understand, while keeping engineering teams aligned and motivated."
    ),
    "greatest_weakness": (
        "I sometimes take on too much ownership of projects. I have learned to delegate more effectively "
        "by investing in team development and building strong centers of excellence."
    ),
    "leadership_style": (
        "I lead by building trust and clarity. I align teams around shared goals, remove blockers, "
        "and invest in developing people. I have a founder's mindset – I move fast, hold people accountable, "
        "and always tie technology decisions back to business impact."
    ),
}

# ─────────────────────────────────────────────────────────
# PROFESSIONAL SUMMARY (by resume type)
# ─────────────────────────────────────────────────────────
SUMMARIES = {
    "executive": (
        "Experienced IT executive with a founder's mindset and a strong track record of translating "
        "business goals into scalable, secure, and cost-effective technology solutions. Deep expertise "
        "in Azure, Microsoft 365, DevOps, and governance, with industry experience spanning healthcare, "
        "finance, CPG, and the public sector."
    ),
    "it_manager": (
        "Seasoned IT leader with over a decade of experience aligning technology strategies with business "
        "goals. Proven track record in managing IT infrastructure, driving digital transformation, and "
        "leading cross-functional teams to deliver scalable, secure, and innovative solutions."
    ),
    "cloud": (
        "Cloud Leader with nearly two decades of expertise in cloud architecture, governance, and "
        "infrastructure optimization. Demonstrates mastery in Azure, the Microsoft Stack, and .NET, "
        "with a proven track record leading high-performing teams and implementing DevOps best practices."
    ),
    "contract": (
        "Cloud Leader with nearly two decades of expertise in cloud architecture, governance, and "
        "infrastructure optimization. Demonstrates mastery in Azure, the Microsoft Stack, and .NET, "
        "with a proven track record leading high-performing teams and implementing DevOps best practices."
    ),
}
