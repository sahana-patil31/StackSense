"""Phase 4 risk and incident intelligence tables

Revision ID: d2b3c4e5f6a7
Revises: c1a2b3c4d5e6
Create Date: 2026-08-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "d2b3c4e5f6a7"
down_revision = "c1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deployment_risk_analyses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("deployment_id", sa.String(length=36), nullable=False),
        sa.Column("model_version", sa.String(length=100), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_level", sa.String(length=20), nullable=False, server_default="LOW"),
        sa.Column("failure_probability", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("feature_snapshot", sa.JSON(), nullable=False),
        sa.Column("contributing_factors", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["deployment_id"], ["deployments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_deployment_risk_analyses_deployment_id", "deployment_risk_analyses", ["deployment_id"])
    op.create_index("ix_deployment_risk_level", "deployment_risk_analyses", ["risk_level"])

    op.create_table(
        "anomalies",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("service_name", sa.String(length=255), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("anomaly_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_anomaly", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("metrics_snapshot", sa.JSON(), nullable=False),
        sa.Column("detection_method", sa.String(length=100), nullable=False, server_default="IsolationForest"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_anomalies_service_name", "anomalies", ["service_name"])
    op.create_index("ix_anomalies_is_anomaly", "anomalies", ["is_anomaly"])
    op.create_index("ix_anomalies_service_window", "anomalies", ["service_name", "window_start"])

    op.create_table(
        "root_cause_analyses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("anomaly_id", sa.String(length=36), nullable=False),
        sa.Column("candidate_type", sa.String(length=50), nullable=False),
        sa.Column("candidate_id", sa.String(length=255), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["anomaly_id"], ["anomalies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_root_cause_analyses_anomaly_id", "root_cause_analyses", ["anomaly_id"])
    op.create_index("ix_root_cause_anomaly_candidate", "root_cause_analyses", ["anomaly_id", "candidate_id"])

    op.create_table(
        "incidents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="detected"),
        sa.Column("severity", sa.String(length=50), nullable=False, server_default="medium"),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("primary_anomaly_id", sa.String(length=36), nullable=False),
        sa.Column("probable_cause", sa.String(length=512), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["primary_anomaly_id"], ["anomalies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incidents_primary_anomaly_id", "incidents", ["primary_anomaly_id"])
    op.create_index("ix_incidents_status_severity", "incidents", ["status", "severity"])


def downgrade() -> None:
    op.drop_table("incidents")
    op.drop_table("root_cause_analyses")
    op.drop_table("anomalies")
    op.drop_table("deployment_risk_analyses")
