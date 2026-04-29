from __future__ import annotations

import re
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class ExtractedEntities(BaseModel):
    order_ids: List[str] = Field(default_factory=list, description="Order IDs found in message e.g. MW-10021")
    product_names: List[str] = Field(default_factory=list, description="Product names or IDs mentioned")
    dates_mentioned: List[str] = Field(default_factory=list, description="Any dates or time references")
    amount_mentioned: Optional[str] = Field(None, description="Any monetary amounts e.g. '200 AED'")
    customer_name: Optional[str] = Field(None, description="Customer's name if self-identified")

    @field_validator("amount_mentioned", mode="before")
    @classmethod
    def coerce_amount_to_str(cls, v) -> Optional[str]:
        if v is None:
            return None
        return str(v)  # model sometimes returns a number like 1650 instead of "1650 AED"


_VALID_LANGUAGES  = {"en", "ar", "mixed"}
_VALID_INTENTS    = {"return_request", "exchange_request", "refund_inquiry", "order_tracking",
                     "product_inquiry", "complaint", "warranty_claim", "other"}
_VALID_SENTIMENTS = {"positive", "neutral", "negative", "very_negative"}
_VALID_ACTIONS    = {"process_refund", "process_exchange", "provide_tracking", "provide_info",
                     "escalate_to_human", "apologize_and_resolve", "standard_response"}


def _pick_first_valid(value: str, valid: set, default: str) -> str:
    """If model returns 'a|b|c' or an invalid string, pick first token that matches."""
    if value in valid:
        return value
    for token in re.split(r"[|,/\s]+", value):
        token = token.strip().lower()
        if token in valid:
            return token
    return default


class TriageResult(BaseModel):
    message_language: Literal["en", "ar", "mixed"] = Field(
        description="Detected language of the customer message"
    )
    intent: Literal[
        "return_request",
        "exchange_request",
        "refund_inquiry",
        "order_tracking",
        "product_inquiry",
        "complaint",
        "warranty_claim",
        "other",
    ] = Field(description="Primary intent of the message")

    urgency: int = Field(ge=1, le=5, description="1=low, 5=critical (safety/very negative)")
    urgency_reasoning: str = Field(default="", description="One sentence explaining the urgency score")

    extracted_entities: ExtractedEntities

    sentiment: Literal["positive", "neutral", "negative", "very_negative"] = Field(
        description="Overall emotional tone of the message"
    )

    suggested_action: Literal[
        "process_refund",
        "process_exchange",
        "provide_tracking",
        "provide_info",
        "escalate_to_human",
        "apologize_and_resolve",
        "standard_response",
    ] = Field(description="Recommended CS action")

    confidence: float = Field(ge=0.0, le=1.0, description="Model confidence in this classification (0–1)")

    should_escalate: bool = Field(
        description="True if confidence < 0.6, urgency >= 4, or issue requires human judgment"
    )
    escalation_reason: Optional[str] = Field(None, description="Required when should_escalate is True")

    suggested_reply_original_language: str = Field(
        description="Draft reply in the SAME language as the customer's message"
    )
    suggested_reply_english: str = Field(
        description="English version of the reply (always required, for supervisor review)"
    )

    tools_used: List[str] = Field(default_factory=list, description="Names of tools called during triage")
    grounded_on_data: bool = Field(
        default=False, description="True only if reply references actual data returned by a tool"
    )

    @field_validator("message_language", mode="before")
    @classmethod
    def coerce_language(cls, v) -> str:
        return _pick_first_valid(str(v), _VALID_LANGUAGES, "en")

    @field_validator("intent", mode="before")
    @classmethod
    def coerce_intent(cls, v) -> str:
        return _pick_first_valid(str(v), _VALID_INTENTS, "other")

    @field_validator("sentiment", mode="before")
    @classmethod
    def coerce_sentiment(cls, v) -> str:
        return _pick_first_valid(str(v), _VALID_SENTIMENTS, "neutral")

    @field_validator("suggested_action", mode="before")
    @classmethod
    def coerce_action(cls, v) -> str:
        return _pick_first_valid(str(v), _VALID_ACTIONS, "standard_response")

    @field_validator("escalation_reason")
    @classmethod
    def escalation_reason_required_when_escalating(cls, v: Optional[str], info) -> Optional[str]:
        should_escalate = info.data.get("should_escalate", False)
        if should_escalate and not v:
            raise ValueError("escalation_reason is required when should_escalate is True")
        return v

    @field_validator("suggested_reply_original_language", "suggested_reply_english")
    @classmethod
    def reply_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Reply field cannot be empty")
        return v.strip()

    @model_validator(mode="after")
    def auto_escalate_low_confidence(self) -> TriageResult:
        # Enforce business rule: always escalate if confidence < 0.6 or urgency >= 4
        if self.confidence < 0.6 or self.urgency >= 4:
            self.should_escalate = True
            if not self.escalation_reason:
                if self.confidence < 0.6:
                    self.escalation_reason = f"Low confidence ({self.confidence:.0%}); human review needed"
                else:
                    self.escalation_reason = f"High urgency ({self.urgency}/5); human review needed"
        return self
