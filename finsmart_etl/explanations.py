"""
LLM Explanations: Generate human-readable explanations for anomalies.

Uses OpenAI's API to create Turkish and English explanations.
"""

import json
import os
from datetime import date
from typing import Optional
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from openai import OpenAI

from .config import get_config
from .contributors import get_contributors_for_anomaly, get_evidence_transactions


# Turkish month names
MONTH_NAMES_TR = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
    5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
    9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
}

# Metric names in Turkish
METRIC_NAMES_TR = {
    "net_sales": "net satışlar",
    "local_sales": "yurtiçi satışlar",
    "global_sales": "yurtdışı satışlar",
    "returns": "satış iadeleri",
    "advisory_expense": "danışmanlık giderleri",
    "software_expense": "yazılım giderleri",
    "payroll": "personel giderleri",
    "marketing": "pazarlama giderleri",
    "hospitality": "temsil ağırlama giderleri",
    "office_rent": "kira giderleri",
    "car_expenses": "araç giderleri",
    "food_expenses": "yemek giderleri",
    "travel_expenses": "seyahat giderleri",
    "interest_income": "faiz gelirleri",
    "total_revenue": "toplam gelir",
    "total_expenses": "toplam giderler",
}


def month_label_tr(month_date: date) -> str:
    """
    Return Turkish month label (e.g., 'Eylül 2025').
    
    Args:
        month_date: Date representing the month
    
    Returns:
        str: Turkish month label
    """
    month_name = MONTH_NAMES_TR.get(month_date.month, str(month_date.month))
    return f"{month_name} {month_date.year}"


def metric_name_tr(metric_name: str) -> str:
    """
    Return Turkish name for a metric.
    
    Args:
        metric_name: English metric name
    
    Returns:
        str: Turkish metric name
    """
    return METRIC_NAMES_TR.get(metric_name, metric_name)


def format_amount_tr(amount: float) -> str:
    """
    Format amount in Turkish style (e.g., '82k TL').
    
    Args:
        amount: Amount to format
    
    Returns:
        str: Formatted amount
    """
    abs_amount = abs(amount)
    if abs_amount >= 1_000_000:
        return f"{abs_amount/1_000_000:.1f}M TL"
    elif abs_amount >= 1_000:
        return f"{abs_amount/1_000:.0f}k TL"
    else:
        return f"{abs_amount:.0f} TL"


def build_anomaly_payload(
    conn: psycopg.Connection,
    anomaly: dict,
    include_evidence: bool = True
) -> dict:
    """
    Build structured payload for LLM prompt.
    
    Args:
        conn: Database connection
        anomaly: Anomaly dictionary
        include_evidence: Whether to include sample transactions
    
    Returns:
        dict: Structured payload for LLM
    """
    # Get contributors
    contributors = get_contributors_for_anomaly(conn, anomaly["id"])
    
    # Get company info
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT name, business_model FROM companies WHERE id = %s",
            (str(anomaly["company_id"]),)
        )
        company = cur.fetchone() or {}
    
    # Parse month date
    month_date = anomaly["month"]
    if isinstance(month_date, str):
        month_date = date.fromisoformat(month_date)
    
    payload = {
        "company": {
            "name": company.get("name", "Unknown"),
            "business_model": company.get("business_model"),
        },
        "anomaly": {
            "metric_name": anomaly["metric_name"],
            "metric_name_tr": metric_name_tr(anomaly["metric_name"]),
            "month": str(anomaly["month"]),
            "month_label_tr": month_label_tr(month_date),
            "prev_value": float(anomaly["prev_value"]) if anomaly["prev_value"] else None,
            "curr_value": float(anomaly["curr_value"]),
            "pct_change": float(anomaly["pct_change"]) if anomaly["pct_change"] else None,
        },
        "contributors": [
            {
                "label": c["label"],
                "amount": float(c["amount"]),
                "amount_formatted": format_amount_tr(c["amount"]),
                "share_pct": round(float(c["share_of_total"]) * 100, 1),
            }
            for c in contributors
        ],
    }
    
    # Optionally add evidence sample
    if include_evidence:
        evidence = get_evidence_transactions(
            conn,
            anomaly["company_id"],
            str(anomaly["month"]),
            anomaly["metric_name"],
            limit=5
        )
        payload["evidence_sample"] = [
            {
                "date": str(e["tx_date"]),
                "description": e["description"],
                "customer": e["customer_name"],
                "amount": float(e["amount"]),
            }
            for e in evidence
        ]
    
    return payload


def build_prompt(payload: dict) -> str:
    """
    Build LLM prompt for anomaly explanation.
    
    Args:
        payload: Structured anomaly payload
    
    Returns:
        str: Prompt string
    """
    prompt = f"""Sen deneyimli bir finansal analist ve CFO danışmanısın.
Aşağıdaki finansal anomali hakkında kısa ve net bir açıklama yaz.

KURALLAR:
1. Sayıları ASLA değiştirme, verilen değerleri kullan.
2. Türkçe açıklama için doğal ve akıcı bir dil kullan.
3. İngilizce açıklama için profesyonel ve özlü bir dil kullan.
4. Her açıklama 2-3 cümle olsun.
5. Değişimin yönünü (artış/azalış) ve ana nedenlerini belirt.

VERİ:
{json.dumps(payload, indent=2, ensure_ascii=False)}

ÇIKTI FORMATI (JSON):
{{
  "tr_explanation": "Türkçe açıklama buraya...",
  "en_explanation": "English explanation here..."
}}

Sadece JSON döndür, başka bir şey yazma."""

    return prompt


def call_reasoning_llm(prompt: str) -> dict:
    """
    Call OpenAI API to generate explanations using gpt-5-mini with reasoning.
    
    Args:
        prompt: Prompt string
    
    Returns:
        dict: {"tr_explanation": "...", "en_explanation": "..."}
    """
    config = get_config()
    client = OpenAI(api_key=config.openai_api_key)
    
    try:
        # Use gpt-5-mini with responses API and reasoning
        result = client.responses.create(
            model="gpt-5-mini",
            input=prompt,
            reasoning={"effort": "low"},
            text={"verbosity": "low"},
        )
        
        raw_text = result.output_text.strip()
        
        # Try to parse JSON
        # Handle potential markdown code blocks
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        
        result = json.loads(raw_text)
        return {
            "tr_explanation": result.get("tr_explanation", ""),
            "en_explanation": result.get("en_explanation", ""),
        }
        
    except json.JSONDecodeError:
        # Fallback: use raw text as Turkish explanation
        return {
            "tr_explanation": raw_text,
            "en_explanation": "",
        }
    except Exception as e:
        return {
            "tr_explanation": f"Açıklama oluşturulamadı: {e}",
            "en_explanation": f"Could not generate explanation: {e}",
        }


def generate_highlight_for_anomaly(
    conn: psycopg.Connection,
    anomaly_id: int,
    llm_func=None
) -> bool:
    """
    Generate and store highlights for a single anomaly.
    
    Args:
        conn: Database connection
        anomaly_id: ID of the anomaly
        llm_func: Optional LLM function (for testing)
    
    Returns:
        bool: True if successful
    """
    if llm_func is None:
        llm_func = call_reasoning_llm
    
    # Get anomaly details
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id, company_id, month, metric_name,
                   prev_value, curr_value, pct_change
            FROM anomalies
            WHERE id = %s
            """,
            (anomaly_id,)
        )
        anomaly = cur.fetchone()
        if not anomaly:
            return False
    
    # Build payload and prompt
    payload = build_anomaly_payload(conn, anomaly)
    prompt = build_prompt(payload)
    
    # Call LLM
    result = llm_func(prompt)
    
    # Store highlights
    with conn.cursor() as cur:
        # Turkish
        if result.get("tr_explanation"):
            cur.execute(
                """
                INSERT INTO anomaly_highlights (anomaly_id, language, text)
                VALUES (%s, 'tr', %s)
                ON CONFLICT (anomaly_id, language) DO UPDATE SET text = EXCLUDED.text
                """,
                (anomaly_id, result["tr_explanation"])
            )
        
        # English
        if result.get("en_explanation"):
            cur.execute(
                """
                INSERT INTO anomaly_highlights (anomaly_id, language, text)
                VALUES (%s, 'en', %s)
                ON CONFLICT (anomaly_id, language) DO UPDATE SET text = EXCLUDED.text
                """,
                (anomaly_id, result["en_explanation"])
            )
        
        conn.commit()
    
    return True


def generate_highlights_for_new_anomalies(
    conn: psycopg.Connection,
    company_id: Optional[UUID] = None,
    batch_size: int = 20,
    llm_func=None
) -> int:
    """
    Generate highlights for anomalies that don't have them yet.
    
    Args:
        conn: Database connection
        company_id: Optional company filter
        batch_size: Maximum anomalies to process
        llm_func: Optional LLM function (for testing)
    
    Returns:
        int: Number of anomalies processed
    """
    # Find anomalies without highlights
    query = """
        SELECT a.id
        FROM anomalies a
        LEFT JOIN anomaly_highlights ah ON ah.anomaly_id = a.id
        WHERE ah.id IS NULL
    """
    params = []
    
    if company_id:
        query += " AND a.company_id = %s"
        params.append(str(company_id))
    
    query += " ORDER BY a.severity_score DESC LIMIT %s"
    params.append(batch_size)
    
    with conn.cursor() as cur:
        cur.execute(query, params)
        anomaly_ids = [row[0] for row in cur.fetchall()]
    
    count = 0
    for anomaly_id in anomaly_ids:
        try:
            if generate_highlight_for_anomaly(conn, anomaly_id, llm_func):
                count += 1
                print(f"Generated highlights for anomaly {anomaly_id}")
        except Exception as e:
            print(f"Error generating highlights for anomaly {anomaly_id}: {e}")
    
    return count


def get_highlights_for_anomaly(
    conn: psycopg.Connection,
    anomaly_id: int
) -> dict:
    """
    Get highlights for an anomaly.
    
    Args:
        conn: Database connection
        anomaly_id: ID of the anomaly
    
    Returns:
        dict: {"tr": "...", "en": "..."} or empty strings if not found
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT language, text
            FROM anomaly_highlights
            WHERE anomaly_id = %s
            """,
            (anomaly_id,)
        )
        rows = cur.fetchall()
    
    result = {"tr": "", "en": ""}
    for lang, text in rows:
        if lang in result:
            result[lang] = text
    
    return result
