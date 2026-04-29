const API = "http://localhost:8001";

export interface Entities {
  order_ids: string[];
  product_names: string[];
  dates_mentioned: string[];
  amount_mentioned: string | null;
  customer_name: string | null;
}

export interface TriageResult {
  intent: string;
  urgency: number;
  urgency_reasoning: string;
  sentiment: string;
  message_language: string;
  confidence: number;
  should_escalate: boolean;
  escalation_reason: string;
  suggested_action: string;
  suggested_reply_original_language: string;
  suggested_reply_english: string;
  grounded_on_data: boolean;
  tools_used: string[];
  extracted_entities: Entities;
}

export interface TriageResponse {
  result: TriageResult;
  meta: { provider: string; model: string; tools_used: string[] };
}

export async function runTriage(message: string, mode: string): Promise<TriageResponse> {
  const res = await fetch(`${API}/triage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, mode }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || "Triage failed");
  }
  return res.json();
}
