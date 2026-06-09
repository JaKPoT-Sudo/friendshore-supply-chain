"""models.py — SQLAlchemy ORM models."""

from __future__ import annotations

import datetime as _dt
import json

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class SupplyChainAnalysis(Base):
    """Top-level record for one uploaded BOM / supply chain analysis session."""
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    created_at: Mapped[_dt.datetime] = mapped_column(DateTime, server_default=func.now())
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    graph_image_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Claude's overall risk summary
    risk_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bottom_line: Mapped[str | None] = mapped_column(Text, nullable=True)

    # JSON-encoded lists
    _single_points_of_failure: Mapped[str | None] = mapped_column("single_points_of_failure", Text, nullable=True)
    _alternative_suggestions: Mapped[str | None] = mapped_column("alternative_suggestions", Text, nullable=True)

    nodes: Mapped[list[SupplierNode]] = relationship("SupplierNode", back_populates="analysis", cascade="all, delete-orphan")
    edges: Mapped[list[SupplyEdge]] = relationship("SupplyEdge", back_populates="analysis", cascade="all, delete-orphan")

    @property
    def single_points_of_failure(self) -> list:
        return json.loads(self._single_points_of_failure) if self._single_points_of_failure else []

    @property
    def alternative_suggestions(self) -> list:
        return json.loads(self._alternative_suggestions) if self._alternative_suggestions else []

    @property
    def high_risk_nodes(self) -> list[SupplierNode]:
        return [n for n in self.nodes if n.risk_score >= 40]


class SupplierNode(Base):
    """A single company / entity in the supply chain graph."""
    __tablename__ = "supplier_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(Integer, ForeignKey("analyses.id"))
    name: Mapped[str] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(Text, nullable=True)
    tier: Mapped[int] = mapped_column(Integer, default=1)
    component: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    is_high_risk_country: Mapped[bool] = mapped_column(default=False)
    is_focal_company: Mapped[bool] = mapped_column(default=False)

    analysis: Mapped[SupplyChainAnalysis] = relationship("SupplyChainAnalysis", back_populates="nodes")

    @property
    def risk_level(self) -> str:
        if self.risk_score >= 60:
            return "High"
        if self.risk_score >= 30:
            return "Medium"
        return "Low"


class SupplyEdge(Base):
    """A directed relationship: supplier → customer."""
    __tablename__ = "supply_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(Integer, ForeignKey("analyses.id"))
    supplier_name: Mapped[str] = mapped_column(Text)
    customer_name: Mapped[str] = mapped_column(Text)
    component: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysis: Mapped[SupplyChainAnalysis] = relationship("SupplyChainAnalysis", back_populates="edges")
