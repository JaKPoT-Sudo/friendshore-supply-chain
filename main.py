"""main.py — FriendShore FastAPI application."""

from __future__ import annotations

import json
import os

from fastapi import Depends, FastAPI, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from claude_agent import AgentError, parse_bom, suggest_alternatives
from config import APP_TITLE, DEMO_BANNER, DEMO_MODE, GRAPH_OUTPUT_DIR
from database import get_db, init_db
from graph_engine import EdgeData, SupplierData, build_and_analyze
from models import SupplyChainAnalysis, SupplyEdge, SupplierNode

app = FastAPI(title=APP_TITLE)

# Static files
os.makedirs("static/graphs", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def startup():
    init_db()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ctx(request: Request, extra: dict | None = None) -> dict:
    base = {"request": request, "app_title": APP_TITLE,
            "demo_mode": DEMO_MODE, "demo_banner": DEMO_BANNER}
    if extra:
        base.update(extra)
    return base


def _run_full_analysis(
    source_text: str,
    db: Session,
    analysis_name: str | None = None,
) -> SupplyChainAnalysis:
    """Parse BOM → score graph → get alternatives → persist everything."""

    # 1. Parse BOM with Claude
    parsed = parse_bom(source_text)
    company_name: str = parsed.get("company_name", "Unknown Company")
    raw_nodes: list[dict] = parsed.get("nodes", [])
    raw_edges: list[dict] = parsed.get("edges", [])

    # 2. Create analysis record
    record = SupplyChainAnalysis(
        name=analysis_name or f"Analysis — {company_name}",
        source_text=source_text[:4000],
    )
    db.add(record)
    db.flush()  # get record.id

    # 3. Persist nodes and edges
    db_nodes: list[SupplierNode] = []
    for n in raw_nodes:
        node = SupplierNode(
            analysis_id=record.id,
            name=n.get("name", "?"),
            country=n.get("country"),
            tier=int(n.get("tier", 1)),
            component=n.get("component"),
            is_focal_company=bool(n.get("is_focal", False)) or int(n.get("tier", 1)) == 0,
        )
        db.add(node)
        db_nodes.append(node)

    db_edges: list[SupplyEdge] = []
    for e in raw_edges:
        edge = SupplyEdge(
            analysis_id=record.id,
            supplier_name=e.get("supplier", "?"),
            customer_name=e.get("customer", "?"),
            component=e.get("component"),
        )
        db.add(edge)
        db_edges.append(edge)

    db.flush()

    # 4. Build graph engine objects
    ge_nodes = [
        SupplierData(
            name=n.name,
            country=n.country,
            tier=n.tier,
            component=n.component,
            is_focal_company=n.is_focal_company,
        )
        for n in db_nodes
    ]
    ge_edges = [
        EdgeData(supplier=e.supplier_name, customer=e.customer_name,
                 component=e.component)
        for e in db_edges
    ]

    # 5. Run graph analysis + render PNG
    focal_company = company_name
    result = build_and_analyze(ge_nodes, ge_edges, focal_company, record.id)

    # 6. Update node risk scores and SPF flags
    spf_set = set(result.single_points_of_failure)
    node_scores = result.risk_scores
    for db_node in db_nodes:
        db_node.risk_score = node_scores.get(db_node.name, 0)
        db_node.is_high_risk_country = any(
            h.lower() in (db_node.country or "").lower()
            for h in ["China", "PRC", "Russia", "Iran", "North Korea", "DPRK", "Belarus", "Venezuela"]
        )

    # 7. Compute overall risk score = average of node scores, weighted by tier
    all_scores = list(node_scores.values())
    overall = int(sum(all_scores) / len(all_scores)) if all_scores else 0

    # 8. Get alternative suggestions for high-risk suppliers
    high_risk = [
        {"name": n.name, "country": n.country, "component": n.component}
        for n in db_nodes
        if n.is_high_risk_country
    ]
    try:
        alternatives = suggest_alternatives(high_risk, focal_company)
    except AgentError:
        alternatives = []

    # 9. Build risk summary
    spf_names = ", ".join(spf_set) if spf_set else "None identified"
    high_risk_names = ", ".join(n["name"] for n in high_risk) if high_risk else "None"
    risk_summary = (
        f"High-risk country suppliers: {high_risk_names}. "
        f"Single points of failure: {spf_names}. "
        f"Overall supply chain risk score: {overall}/100."
    )

    bottom_line = (
        f"Supply chain contains {len(high_risk)} high-risk supplier(s) and "
        f"{len(spf_set)} single point(s) of failure. "
        f"{'Immediate reshoring action recommended.' if overall >= 60 else 'Moderate risk — monitor and diversify.'}"
    )

    # 10. Update analysis record
    graph_image_path = os.path.join(GRAPH_OUTPUT_DIR, f"graph_{record.id}.png")
    record.graph_image_path = graph_image_path
    record.overall_risk_score = overall
    record.risk_summary = risk_summary
    record.bottom_line = bottom_line
    record._single_points_of_failure = json.dumps(list(spf_set))
    record._alternative_suggestions = json.dumps(alternatives)

    db.commit()
    db.refresh(record)
    return record


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", _ctx(request))


@app.post("/analyze")
async def analyze(
    request: Request,
    db: Session = Depends(get_db),
    bom_text: str = Form(default=""),
    analysis_name: str = Form(default=""),
    file: UploadFile | None = None,
):
    # Collect input text
    source_text = ""
    if file and file.filename:
        contents = await file.read()
        try:
            source_text = contents.decode("utf-8")
        except UnicodeDecodeError:
            source_text = contents.decode("latin-1", errors="replace")
    if not source_text:
        source_text = bom_text.strip()

    if not source_text:
        return templates.TemplateResponse(
            "index.html",
            _ctx(request, {"error": "Please paste BOM text or upload a file."}),
            status_code=400,
        )

    try:
        record = _run_full_analysis(source_text, db, analysis_name or None)
    except AgentError as exc:
        return templates.TemplateResponse(
            "index.html",
            _ctx(request, {"error": f"Analysis failed: {exc}"}),
            status_code=500,
        )

    return RedirectResponse(f"/analysis/{record.id}", status_code=303)


@app.get("/analysis/{analysis_id}", response_class=HTMLResponse)
def view_analysis(request: Request, analysis_id: int, db: Session = Depends(get_db)):
    record = db.get(SupplyChainAnalysis, analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")

    graph_url = (
        f"/static/graphs/graph_{record.id}.png"
        if record.graph_image_path and os.path.exists(record.graph_image_path)
        else None
    )

    return templates.TemplateResponse(
        "analysis.html",
        _ctx(request, {
            "record": record,
            "graph_url": graph_url,
        }),
    )


@app.get("/history", response_class=HTMLResponse)
def history(request: Request, db: Session = Depends(get_db)):
    records = db.query(SupplyChainAnalysis).order_by(
        SupplyChainAnalysis.created_at.desc()
    ).all()
    return templates.TemplateResponse("history.html", _ctx(request, {"records": records}))


@app.post("/seed")
def seed(db: Session = Depends(get_db)):
    """Load demo data."""
    from seed_data import DEMO_ANALYSES

    added = 0
    for demo in DEMO_ANALYSES:
        # Check if already seeded
        existing = db.query(SupplyChainAnalysis).filter_by(name=demo["name"]).first()
        if existing:
            continue

        record = SupplyChainAnalysis(
            name=demo["name"],
            source_text=demo.get("source_text", ""),
            overall_risk_score=demo.get("overall_risk_score"),
            risk_summary=demo.get("risk_summary", ""),
            bottom_line=demo.get("bottom_line", ""),
            _single_points_of_failure=json.dumps(demo.get("single_points_of_failure", [])),
            _alternative_suggestions=json.dumps(demo.get("alternative_suggestions", [])),
        )
        db.add(record)
        db.flush()

        from graph_engine import SupplierData as GENode, EdgeData as GEEdge

        ge_nodes = []
        for n in demo.get("nodes", []):
            db_node = SupplierNode(
                analysis_id=record.id,
                name=n["name"],
                country=n.get("country"),
                tier=n.get("tier", 1),
                component=n.get("component"),
                is_focal_company=n.get("is_focal", False),
                is_high_risk_country=any(
                    h.lower() in (n.get("country") or "").lower()
                    for h in ["China", "PRC", "Russia", "Iran", "North Korea", "DPRK", "Belarus"]
                ),
            )
            db.add(db_node)
            ge_nodes.append(GENode(
                name=n["name"], country=n.get("country"),
                tier=n.get("tier", 1), component=n.get("component"),
                is_focal_company=n.get("is_focal", False),
            ))

        ge_edges = []
        for e in demo.get("edges", []):
            db_edge = SupplyEdge(
                analysis_id=record.id,
                supplier_name=e["supplier"],
                customer_name=e["customer"],
                component=e.get("component"),
            )
            db.add(db_edge)
            ge_edges.append(GEEdge(supplier=e["supplier"], customer=e["customer"],
                                   component=e.get("component")))

        db.flush()

        # Render the graph PNG
        focal = demo.get("nodes", [{}])[0].get("name", "Company")
        try:
            result = build_and_analyze(ge_nodes, ge_edges, focal, record.id)
            record.graph_image_path = os.path.join(GRAPH_OUTPUT_DIR, f"graph_{record.id}.png")

            # Update node risk scores from graph engine
            db_nodes_for_record = db.query(SupplierNode).filter_by(analysis_id=record.id).all()
            for db_n in db_nodes_for_record:
                db_n.risk_score = result.risk_scores.get(db_n.name, 0)
        except Exception:
            pass

        added += 1

    db.commit()
    return RedirectResponse("/history", status_code=303)
