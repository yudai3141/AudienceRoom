from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FeedbackMetric(Base):
    __tablename__ = "feedback_metrics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    feedback_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("session_feedback.id"), nullable=False
    )
    metric_key: Mapped[str] = mapped_column(String(50), nullable=False)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    metric_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metric_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    feedback = relationship("SessionFeedback", backref="metrics", lazy="select")
