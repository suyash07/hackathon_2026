"""Generate synthetic, KubeCon-style conference data into data/*.json.

All names, companies and sessions are fictional. A fixed seed makes the
output reproducible, so the demo always looks the same.

Run from the project root:  python src/generate_data.py
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = 42
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
VENUE_TZ = timezone(timedelta(hours=-7))  # Salt Lake City in November (MST)

NUM_SPEAKERS = 80
NUM_ATTENDEES = 120
CHECKED_IN_RATE = 0.7

DAYS = ["2026-11-09", "2026-11-10", "2026-11-11", "2026-11-12"]
SLOTS = ["10:30", "11:30", "13:30", "14:30", "15:45", "16:45"]
MAIN_ROOMS = [f"Room {n}" for n in range(1, 9)]
HANGOUT_AREAS = ["Expo Hall", "Hallway Track Lounge", "Coffee Bar", "Sponsor Showcase"]

# Day 1 is co-located events, each with its own room.
COLOCATED = {
    "CiliumCon": ("Room 1", "networking"),
    "ArgoCon": ("Room 2", "gitops"),
    "BackstageCon": ("Room 3", "platform"),
    "Cloud Native AI + Inference Day": ("Room 4", "inference"),
    "OpenTelemetry Community Day": ("Room 5", "observability"),
    "Cloud Native Security Day": ("Room 6", "runtime_security"),
}

FORMATS = ["talk"] * 14 + ["panel"] * 2 + ["lightning"] * 2 + ["workshop"] * 2
DURATION_MIN = {"talk": 35, "panel": 35, "lightning": 15, "workshop": 85}
LEVELS = ["beginner", "intermediate", "advanced"]

# Topic catalog. "plain" sentences avoid the obvious keywords on purpose,
# so semantic search can be shown beating keyword search.
TOPICS = {
    "runtime_security": {
        "track": "Security",
        "tags": ["eBPF", "security", "runtime", "Falco"],
        "subjects": [
            "Runtime Threat Detection",
            "Catching Container Escapes",
            "Syscall-Level Defense",
            "Detecting Cryptominers in Pods",
            "Kernel Tracing for Incident Response",
        ],
        "keyword": [
            "We use eBPF probes to detect suspicious behavior in containers.",
            "Falco rules flag shells spawned inside production pods.",
            "eBPF-based sensors watch every syscall with negligible overhead.",
        ],
        "plain": [
            "We watch what processes do deep inside the operating system and flag "
            "anything that looks like an attacker breaking out of a container.",
            "Kernel-level visibility let us spot privilege escalation in seconds, "
            "without installing heavyweight agents.",
            "Learn how to notice a compromised workload by its behavior rather than its signature.",
        ],
    },
    "supply_chain": {
        "track": "Security",
        "tags": ["supply-chain", "Sigstore", "SBOM", "security"],
        "subjects": [
            "Signing Everything",
            "SBOMs That Actually Help",
            "Provenance at Deploy Time",
            "Surviving a Dependency Compromise",
        ],
        "keyword": [
            "We sign images with Sigstore and verify SBOMs at admission.",
            "SLSA provenance blocks unverified builds from reaching production.",
        ],
        "plain": [
            "How do you prove the code running in production is the code you "
            "reviewed? We trace every artifact back to its source.",
            "A walkthrough of a poisoned third-party package and the checks that "
            "would have stopped it.",
        ],
    },
    "identity": {
        "track": "Security",
        "tags": ["zero-trust", "SPIFFE", "identity", "security"],
        "subjects": [
            "Zero Trust Between Services",
            "Workload Identity in Practice",
            "Killing Long-Lived Credentials",
        ],
        "keyword": [
            "SPIFFE identities replace static secrets for service-to-service auth.",
            "We rolled out zero trust networking across 40 clusters.",
        ],
        "plain": [
            "Every service proves who it is on every request, and nobody holds a "
            "password that lasts longer than an hour."
        ],
    },
    "networking": {
        "track": "Networking",
        "tags": ["Cilium", "eBPF", "networking", "service-mesh"],
        "subjects": [
            "Sidecar-Free Service Mesh",
            "Network Policy That Scales",
            "Debugging Dropped Packets",
            "XDP Load Balancing",
        ],
        "keyword": [
            "Cilium uses eBPF to enforce identity-aware network policy.",
            "We replaced kube-proxy with an eBPF datapath.",
        ],
        "plain": [
            "Packets get filtered before they ever reach the network stack, which "
            "cut our latency in half.",
            "Tracing traffic between services when the network plugin is someone else's code.",
        ],
    },
    "inference": {
        "track": "AI Inference + Agentic",
        "tags": ["LLM", "inference", "GPU", "AI"],
        "subjects": [
            "Serving LLMs on Kubernetes",
            "GPU Scheduling That Doesn't Waste Money",
            "Autoscaling Model Servers",
            "Low-Latency Inference at the Edge",
        ],
        "keyword": [
            "We serve LLM inference with vLLM and KServe on shared GPU pools.",
            "GPU partitioning and request batching tripled throughput.",
        ],
        "plain": [
            "Running large models for thousands of users without a separate "
            "accelerator for every team.",
            "What we learned keeping response times low when traffic to our model spiked tenfold.",
        ],
    },
    "agents": {
        "track": "AI Inference + Agentic",
        "tags": ["AI", "agents", "MCP", "LLM"],
        "subjects": [
            "Agents That Operate Clusters",
            "MCP Servers for Platform Teams",
            "Guardrails for Autonomous Ops",
            "AI-Assisted Incident Response",
        ],
        "keyword": [
            "LLM agents call Kubernetes tools through MCP with strict guardrails.",
            "We trace every agent step so we can audit what it changed.",
        ],
        "plain": [
            "Letting software make operational decisions on its own, safely, and "
            "knowing exactly why it did what it did.",
            "An assistant that reads alerts, gathers evidence and proposes a fix "
            "before the on-call engineer wakes up.",
        ],
    },
    "rag": {
        "track": "AI Inference + Agentic",
        "tags": ["RAG", "vector-search", "LLM", "AI"],
        "subjects": [
            "RAG Without Hallucinations",
            "Vector Search on Kubernetes",
            "Grounding Chatbots in Your Docs",
        ],
        "keyword": [
            "Hybrid BM25 and vector retrieval with a reranker improved RAG answers.",
            "We run a vector database as a stateful workload with operators.",
        ],
        "plain": [
            "Making an internal assistant answer only from trusted documents and "
            "cite where every answer came from."
        ],
    },
    "platform": {
        "track": "Platform Engineering",
        "tags": ["Backstage", "IDP", "platform", "developer-experience"],
        "subjects": [
            "Golden Paths That People Use",
            "Your Platform Is a Product",
            "Self-Service Environments",
            "Measuring Developer Happiness",
        ],
        "keyword": [
            "Our Backstage-based internal developer platform serves 900 engineers.",
            "Golden path templates cut new service setup to ten minutes.",
        ],
        "plain": [
            "Treating internal engineers as customers changed how we built everything.",
            "Developers get a working environment in minutes without filing a ticket.",
        ],
    },
    "gitops": {
        "track": "Platform Engineering",
        "tags": ["GitOps", "Argo CD", "Flux", "delivery"],
        "subjects": [
            "GitOps at 500 Clusters",
            "Progressive Delivery Done Right",
            "Rollbacks Nobody Notices",
        ],
        "keyword": [
            "Argo CD and Argo Rollouts drive canary releases across regions.",
            "Flux reconciles every cluster from a single repository.",
        ],
        "plain": [
            "Every change to production is a reviewed commit, and undoing a bad "
            "release is a revert away."
        ],
    },
    "observability": {
        "track": "Observability",
        "tags": ["OpenTelemetry", "tracing", "logging", "observability"],
        "subjects": [
            "Observability on a Budget",
            "Tracing Every Request",
            "Alerts That Mean Something",
            "Logs You Can Afford",
        ],
        "keyword": [
            "OpenTelemetry collectors with tail sampling cut our bill by 60%.",
            "Distributed tracing found the slow dependency in minutes.",
        ],
        "plain": [
            "We stopped storing everything and started keeping only the signals "
            "that help during an outage.",
            "Figuring out why one request in a thousand is slow.",
        ],
    },
    "finops": {
        "track": "Operations",
        "tags": ["FinOps", "autoscaling", "cost"],
        "subjects": [
            "Cutting the Cloud Bill",
            "Right-Sizing Without Tears",
            "Spot Instances in Production",
        ],
        "keyword": [
            "Karpenter and right-sizing recommendations cut compute cost 40%.",
            "Showback dashboards made each team own its spend.",
        ],
        "plain": [
            "Paying only for what we actually use, and showing every team what their services cost."
        ],
    },
    "data": {
        "track": "Operations",
        "tags": ["databases", "operators", "stateful"],
        "subjects": [
            "Postgres on Kubernetes, Honestly",
            "Operators for Stateful Apps",
            "Backups You Have Actually Restored",
        ],
        "keyword": [
            "We run Postgres with an operator, logical replication and PITR.",
            "Stateful workloads need careful storage class and anti-affinity design.",
        ],
        "plain": ["Keeping a database alive inside a system that loves to restart things."],
    },
}

HOOKS = [
    "Lessons from Production",
    "A Field Guide",
    "What We Got Wrong",
    "From Zero to Production",
    "Patterns and Pitfalls",
    "A Live Demo",
    "at Scale",
    "the Hard Way",
    "in 30 Minutes",
    "Beyond the Hype",
]
CLOSERS = [
    "Attendees leave with a working reference architecture.",
    "Includes a live demo and open-source code.",
    "We share benchmarks, failures and the fixes that stuck.",
    "No prior experience required.",
    "Expect real numbers from a large production environment.",
]

FIRST = [
    "Priya",
    "Marco",
    "Aisha",
    "Daniel",
    "Sofia",
    "Liam",
    "Neha",
    "Kenji",
    "Lena",
    "Tomás",
    "Amara",
    "Jonas",
    "Mei",
    "Ravi",
    "Elena",
    "Omar",
    "Hana",
    "Lucas",
    "Fatima",
    "Noah",
    "Ingrid",
    "Arjun",
    "Chloe",
    "Mateo",
    "Yuki",
    "Grace",
    "Samir",
    "Zara",
    "Felix",
    "Ananya",
    "Diego",
    "Freya",
    "Kwame",
    "Isla",
    "Hiro",
    "Nadia",
    "Ethan",
    "Leila",
    "Oscar",
    "Maya",
]
LAST = [
    "Raman",
    "Bianchi",
    "Okafor",
    "Kim",
    "Martinez",
    "O'Connor",
    "Joshi",
    "Tanaka",
    "Weber",
    "Silva",
    "Mensah",
    "Berg",
    "Chen",
    "Patel",
    "Novak",
    "Haddad",
    "Sato",
    "Moreau",
    "Noor",
    "Fischer",
    "Larsen",
    "Mehta",
    "Dubois",
    "Rossi",
    "Nakamura",
    "Liu",
    "Khan",
    "Abebe",
    "Schmidt",
    "Iyer",
    "Alvarez",
    "Lindqvist",
    "Asante",
    "Murphy",
    "Kobayashi",
    "Rahman",
    "Carter",
    "Farah",
    "Nilsson",
    "Reyes",
]
COMPANIES = [
    "KernelGuard",
    "NetScale",
    "TrustLayer",
    "VectorWorks",
    "Groundwork AI",
    "DataForge",
    "FinSight",
    "CloudNest",
    "Streamly",
    "EdgeLink",
    "PayNova",
    "Quantix",
    "LedgerCo",
    "SecureOS",
    "ShopWave",
    "OrbitOps",
    "Helmsman Labs",
    "PodPilot",
    "Skyforge",
    "Latticeworks",
    "Northwind Cloud",
    "BlueHarbor",
]

ROLES = {
    "SRE": ["observability", "finops", "agents"],
    "Platform Engineer": ["platform", "gitops", "networking"],
    "Security Engineer": ["runtime_security", "supply_chain", "identity"],
    "ML Engineer": ["inference", "rag", "agents"],
    "Data Engineer": ["data", "observability", "rag"],
    "Backend Engineer": ["gitops", "data", "rag"],
    "Network Engineer": ["networking", "runtime_security", "identity"],
    "Student": ["inference", "platform", "runtime_security"],
    "Product Manager": ["platform", "agents", "finops"],
}
WORKING_ON = {
    "runtime_security": [
        "Detecting cryptominers in Kubernetes pods by watching syscalls",
        "Building an eBPF sensor that flags container escapes",
        "Writing runtime detection rules for our production clusters",
    ],
    "supply_chain": [
        "Signing every container image and enforcing provenance at deploy",
        "Generating SBOMs and scanning third-party dependencies",
    ],
    "identity": [
        "Replacing static service passwords with short-lived workload identities",
        "Rolling out zero trust between microservices",
    ],
    "networking": [
        "Migrating to a sidecar-free service mesh",
        "Debugging packet drops in our CNI with eBPF tooling",
    ],
    "inference": [
        "Serving open-weight LLMs on a shared GPU cluster",
        "Autoscaling model servers to handle traffic spikes",
    ],
    "agents": [
        "An AI agent that triages alerts and suggests fixes",
        "MCP servers that let assistants safely query our clusters",
    ],
    "rag": [
        "A RAG chatbot over our internal runbooks that cites sources",
        "Hybrid keyword plus vector search for product documentation",
    ],
    "platform": [
        "An internal developer portal with golden path templates",
        "Self-service preview environments for every pull request",
    ],
    "gitops": [
        "Moving 200 clusters to GitOps with Argo CD",
        "Canary releases with automatic rollback",
    ],
    "observability": [
        "Cutting logging costs with OpenTelemetry tail sampling",
        "End-to-end tracing across 300 microservices",
    ],
    "finops": [
        "Right-sizing workloads to cut our cloud bill",
        "Showback dashboards so teams see their own spend",
    ],
    "data": [
        "Running Postgres on Kubernetes with an operator",
        "Reliable backups and restores for stateful workloads",
    ],
}
INTEREST_TEXT = {
    "runtime_security": "runtime security and kernel-level threat detection",
    "supply_chain": "software supply chain security",
    "identity": "zero trust and workload identity",
    "networking": "eBPF networking and service mesh",
    "inference": "running LLM inference on Kubernetes",
    "agents": "AI agents for operations",
    "rag": "RAG and vector search",
    "platform": "platform engineering and developer experience",
    "gitops": "GitOps and progressive delivery",
    "observability": "observability and OpenTelemetry",
    "finops": "cloud cost optimization",
    "data": "databases and stateful workloads on Kubernetes",
}
BIO_EXTRAS = [
    "maintainer of an open-source project",
    "speaks regularly at community events",
    "leads a platform team",
    "previously an SRE",
]
GOALS = [
    "learn",
    "hiring",
    "job-seeking",
    "find-contributors",
    "meet-maintainers",
    "evaluate-tools",
    "find-mentor",
    "share-work",
]
LEVEL_FOR = {"Student": "beginner"}


def iso(day: str, hhmm: str, plus_min: int = 0) -> str:
    """Return an ISO 8601 timestamp with the venue offset."""
    start = datetime.strptime(f"{day} {hhmm}", "%Y-%m-%d %H:%M").replace(tzinfo=VENUE_TZ)
    return (start + timedelta(minutes=plus_min)).isoformat()


def unique_name(rng: random.Random, used: set) -> str:
    """Pick a first + last name not used yet."""
    while True:
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        if name not in used:
            used.add(name)
            return name


def make_speakers(rng: random.Random, used_names: set) -> list:
    topics = list(TOPICS)
    speakers = []
    for i in range(NUM_SPEAKERS):
        topic = topics[i % len(topics)]  # every topic gets several experts
        speakers.append(
            {
                "id": f"s{i + 1:03d}",
                "name": unique_name(rng, used_names),
                "company": rng.choice(COMPANIES),
                "bio": f"Works on {INTEREST_TEXT[topic]}; {rng.choice(BIO_EXTRAS)}.",
                "_topic": topic,
            }
        )
    return speakers


def make_abstract(rng: random.Random, topic: dict, plain_only: bool) -> str:
    pool = topic["plain"] if plain_only else topic["plain"] + topic["keyword"]
    sentences = rng.sample(pool, k=min(2, len(pool)))
    return " ".join(sentences + [rng.choice(CLOSERS)])


def make_talks(rng: random.Random, speakers: list) -> list:
    by_topic = {}
    for s in speakers:
        by_topic.setdefault(s["_topic"], []).append(s)

    talks, titles = [], set()

    def add_talk(day, slot, room, topic_key, track=None, fmt=None):
        topic = TOPICS[topic_key]
        fmt = fmt or rng.choice(FORMATS)
        for _ in range(20):
            title = f"{rng.choice(topic['subjects'])}: {rng.choice(HOOKS)}"
            if title not in titles:
                break
        titles.add(title)
        n_speakers = 3 if fmt == "panel" else rng.choice([1, 1, 2])
        chosen = rng.sample(by_topic[topic_key], k=min(n_speakers, len(by_topic[topic_key])))
        talks.append(
            {
                "id": f"t{len(talks) + 1:03d}",
                "title": title,
                "abstract": make_abstract(rng, topic, plain_only=rng.random() < 0.3),
                "speakers": [s["name"] for s in chosen],
                "speaker_ids": [s["id"] for s in chosen],
                "track": track or topic["track"],
                "tags": rng.sample(topic["tags"], k=min(3, len(topic["tags"]))),
                "format": fmt,
                "level": rng.choice(LEVELS),
                "room": room,
                "start": iso(day, slot),
                "end": iso(day, slot, DURATION_MIN[fmt]),
                "day": day,
                "_topic": topic_key,  # internal only, stripped on write
            }
        )

    # Day 1: co-located events.
    for event, (room, topic_key) in COLOCATED.items():
        for slot in SLOTS:
            add_talk(DAYS[0], slot, room, topic_key, track=event)

    # Days 2-4: main conference, keynote + every room every slot.
    topic_keys = list(TOPICS)
    for day in DAYS[1:]:
        add_talk(day, "09:00", "Main Stage", rng.choice(topic_keys), track="Keynote", fmt="talk")
        for slot in SLOTS:
            # shuffled topics per slot => same-topic talks often overlap (agenda conflicts)
            for room, topic_key in zip(MAIN_ROOMS, rng.sample(topic_keys, k=len(MAIN_ROOMS))):
                add_talk(day, slot, room, topic_key)
    return talks


def pick_bookmarks(rng, talks_by_topic, topic, days, k):
    """Pick up to k talks on the topic, only on days the attendee is there."""
    options = [tid for tid, day in talks_by_topic[topic] if day in days]
    return sorted(rng.sample(options, k=min(k, len(options))))


def make_attendee(rng, idx, name, role, topics, talks_by_topic):
    checked_in = rng.random() < CHECKED_IN_RATE
    interests = [INTEREST_TEXT[t] for t in topics]
    days = sorted(rng.sample(DAYS, k=rng.randint(2, 4)))
    bookmarks = pick_bookmarks(rng, talks_by_topic, topics[0], days, rng.randint(0, 3))
    return {
        "id": f"a{idx:03d}",
        "name": name,
        "role": role,
        "company": rng.choice(COMPANIES),
        "experience_level": LEVEL_FOR.get(role, rng.choice(LEVELS)),
        "working_on": rng.choice(WORKING_ON[topics[0]]) + ".",
        "interests": "Interested in " + " and ".join(interests) + ".",
        "goals": rng.sample(GOALS, k=2),
        "available_days": days,
        "checked_in": checked_in,
        "current_location": rng.choice(MAIN_ROOMS + HANGOUT_AREAS) if checked_in else None,
        "bookmarked_talks": bookmarks,
    }


def make_attendees(rng: random.Random, talks: list, used_names: set) -> list:
    talks_by_topic = {}
    for t in talks:
        talks_by_topic.setdefault(t["_topic"], []).append((t["id"], t["day"]))

    attendees = []
    roles = list(ROLES)
    for i in range(NUM_ATTENDEES):
        role = roles[i % len(roles)]
        primary = rng.choice(ROLES[role])
        # ~30% cross-topic interests (e.g. security + AI) to show semantic matching
        second = rng.choice(list(TOPICS)) if rng.random() < 0.3 else rng.choice(ROLES[role])
        topics = [primary] if second == primary else [primary, second]
        attendees.append(
            make_attendee(rng, i + 1, unique_name(rng, used_names), role, topics, talks_by_topic)
        )

    # Demo user: clear, explainable results in every feature.
    demo_days = DAYS[1:3]
    demo_bookmarks = pick_bookmarks(rng, talks_by_topic, "runtime_security", demo_days, 2)
    attendees.insert(
        0,
        {
            "id": "demo-user",
            "name": "Demo User",
            "role": "Platform Engineer",
            "company": "Hackathon Team",
            "experience_level": "intermediate",
            "working_on": "Building eBPF-based runtime security for Kubernetes with an AI "
            "assistant that triages the alerts.",
            "interests": "Interested in runtime security and kernel-level threat detection "
            "and AI agents for operations.",
            "goals": ["learn", "find-contributors"],
            "available_days": demo_days,
            "checked_in": True,
            "current_location": "Hallway Track Lounge",
            "bookmarked_talks": demo_bookmarks,
        },
    )
    return attendees


def make_side_events(rng: random.Random) -> list:
    events = [
        (
            "Security Happy Hour",
            "Drinks with security track speakers. Bring your threat detection war stories.",
            "Rooftop Bar",
        ),
        (
            "AI Builders Breakfast",
            "Morning meetup for people building with LLMs, RAG and agents.",
            "Coffee Bar",
        ),
        (
            "eBPF Hands-On Workshop",
            "Write your first kernel tracing program. Laptop required.",
            "Lab A",
        ),
        (
            "Platform Engineering Roundtable",
            "Share what worked for your internal developer platform.",
            "Room 105",
        ),
        (
            "Women in Cloud Native Lunch",
            "Networking lunch for women across cloud native roles.",
            "Room 106",
        ),
        ("Job Fair", "Meet hiring teams from cloud, fintech and AI companies.", "Expo Hall"),
        (
            "First-Timers Orientation",
            "New to KubeCon? Learn how to get the most out of the week.",
            "Main Stage",
        ),
        (
            "GitOps Office Hours",
            "Bring your Argo CD and Flux questions to maintainers.",
            "Project Pavilion",
        ),
        (
            "Observability Game Night",
            "Debugging puzzles and board games with the OpenTelemetry community.",
            "Hallway Track Lounge",
        ),
        (
            "Contributor Meetup",
            "Find a project to contribute to and meet maintainers.",
            "Project Pavilion",
        ),
        (
            "Cost Optimization Clinic",
            "Bring your cloud bill; FinOps experts help you trim it.",
            "Room 107",
        ),
        (
            "Morning Fun Run",
            "Easy 5K around downtown Salt Lake City. All paces welcome.",
            "Main Entrance",
        ),
        ("Student Mixer", "Students meet mentors and recruiters.", "Coffee Bar"),
        (
            "Agents in Production Panel Drinks",
            "Informal follow-up to the agentic track.",
            "Rooftop Bar",
        ),
        ("Closing Party", "Celebrate the end of the conference.", "Expo Hall"),
    ]
    out = []
    for i, (name, desc, loc) in enumerate(events):
        day = rng.choice(DAYS)
        hhmm = rng.choice(["07:30", "08:00", "12:15", "17:30", "18:30", "19:00"])
        out.append(
            {
                "id": f"e{i + 1:03d}",
                "name": name,
                "description": desc,
                "start": iso(day, hhmm),
                "location": loc,
            }
        )
    return out


def write(name: str, docs: list) -> None:
    clean = [{k: v for k, v in d.items() if not k.startswith("_")} for d in docs]
    (DATA_DIR / f"{name}.json").write_text(json.dumps(clean, indent=2, ensure_ascii=False))
    print(f"{name}: {len(clean)}")


def main() -> None:
    rng = random.Random(SEED)
    DATA_DIR.mkdir(exist_ok=True)
    used_names: set = set()
    speakers = make_speakers(rng, used_names)
    talks = make_talks(rng, speakers)
    attendees = make_attendees(rng, talks, used_names)
    write("speakers", speakers)
    write("talks", talks)
    write("attendees", attendees)
    write("side_events", make_side_events(rng))


if __name__ == "__main__":
    main()
