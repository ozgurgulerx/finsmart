"""
CFO Month View: Comprehensive financial view for a company and month.

Provides:
- Metrics overview with MoM changes
- Anomaly details with contributors and explanations
- Evidence samples for human verification
- Consolidated executive report
"""

import json
from datetime import date
from typing import Optional
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from openai import OpenAI

from .config import get_config
from .metrics import compute_monthly_kpis
from .anomalies import detect_anomalies, get_anomalies_for_month, explain_anomaly_detection
from .contributors import (
    compute_contributors_for_company,
    get_contributors_for_anomaly,
    get_evidence_transactions,
)
from .explanations import (
    generate_highlights_for_new_anomalies,
    get_highlights_for_anomaly,
    generate_highlight_for_anomaly,
    month_label_tr,
    metric_name_tr,
    format_amount_tr,
)


def generate_executive_report(
    company_name: str,
    month_label: str,
    anomalies: list[dict]
) -> dict:
    """
    Generate a consolidated executive report summarizing all anomalies.
    
    Uses gpt-5-mini with minimal reasoning to create a coherent narrative.
    Structure: Complete Turkish report first, then complete English report.
    
    Args:
        company_name: Company name
        month_label: Turkish month label (e.g., "Eylül 2023")
        anomalies: List of anomaly details
    
    Returns:
        dict: Executive report with separate Turkish and English sections
    """
    config = get_config()
    client = OpenAI(api_key=config.openai_api_key)
    
    # Build detailed anomaly info for prompt
    anomaly_details = []
    for a in anomalies:
        pct = a.get("pct_change")
        pct_str = f"%{round(pct, 1)}" if pct is not None else "N/A"
        direction = "artış" if (pct or 0) > 0 else "azalış"
        
        # Get detection reasoning (from gpt-5-nano)
        detection = a.get("detection", {})
        detection_reasoning = detection.get("reasoning", "")
        
        # Get root cause analysis (from gpt-5-mini highlights)
        highlights = a.get("highlights", {})
        root_cause_tr = highlights.get("tr", "")
        root_cause_en = highlights.get("en", "")
        
        # Get top contributors
        top_contributors = a.get("contributors", [])[:3]
        contributor_list = [f"{c['label']}: {c['amount_formatted']}" for c in top_contributors]
        
        anomaly_details.append({
            "metric": a.get("metric_name"),
            "metric_tr": a.get("metric_name_tr"),
            "prev": a.get("prev_formatted"),
            "curr": a.get("curr_formatted"),
            "pct_change": pct_str,
            "direction": direction,
            "detection_reason": detection.get("reason"),
            "detection_reasoning": detection_reasoning,  # Why it's an anomaly (gpt-5-nano)
            "root_cause_tr": root_cause_tr,  # Root cause analysis TR (gpt-5-mini)
            "root_cause_en": root_cause_en,  # Root cause analysis EN (gpt-5-mini)
            "top_contributors": contributor_list,
        })
    
    prompt = f"""Sen deneyimli bir CFO danışmanısın. Aşağıdaki aylık finansal anomalileri analiz et ve yönetim kuruluna sunulacak kapsamlı bir özet rapor hazırla.

ŞİRKET: {company_name}
DÖNEM: {month_label}

ANOMALİ DETAYLARI:
{json.dumps(anomaly_details, indent=2, ensure_ascii=False)}

ÖNEMLİ KURALLAR:
1. Önce TAMAMEN TÜRKÇE bir rapor oluştur (hiç İngilizce kelime kullanma)
2. Sonra TAMAMEN İNGİLİZCE ayrı bir rapor oluştur (hiç Türkçe kelime kullanma)
3. Türkçe raporda metrik isimlerini Türkçe karşılıklarıyla yaz (metric_tr alanını kullan)
4. İngilizce raporda metrik isimlerini İngilizce yaz (metric alanını kullan)

Her rapor şu bölümleri içermeli:
1. Başlık
2. Genel Değerlendirme (1-2 paragraf - dönemin genel finansal durumu)
3. Tespit Edilen Anomaliler (her anomali için):
   - Metrik adı ve değişim yüzdesi
   - Neden anomali olarak işaretlendi (detection_reasoning'den Türkçe/İngilizce çevir)
   - Kök neden analizi (root_cause_tr veya root_cause_en kullan)
4. Aksiyon Önerileri (somut ve uygulanabilir öneriler)

ÇIKTI FORMATI (JSON):
{{
  "report_tr": {{
    "title": "{month_label} Finansal Anomali Özet Raporu",
    "overview": "Genel değerlendirme paragrafı (tamamen Türkçe)...",
    "anomalies": [
      {{
        "metric": "Türkçe metrik adı",
        "change": "%X.X artış/azalış", 
        "why_anomaly": "Neden anomali olarak işaretlendi (Türkçe)...",
        "root_cause": "Kök neden analizi (Türkçe)..."
      }}
    ],
    "action_recommendations": [
      "Türkçe aksiyon önerisi 1",
      "Türkçe aksiyon önerisi 2"
    ]
  }},
  "report_en": {{
    "title": "{month_label} Financial Anomaly Summary Report",
    "overview": "General assessment paragraph (fully in English)...",
    "anomalies": [
      {{
        "metric": "English metric name",
        "change": "X.X% increase/decrease",
        "why_anomaly": "Why flagged as anomaly (English)...",
        "root_cause": "Root cause analysis (English)..."
      }}
    ],
    "action_recommendations": [
      "English action recommendation 1",
      "English action recommendation 2"
    ]
  }}
}}

Sadece JSON döndür, başka açıklama ekleme."""

    try:
        result = client.responses.create(
            model="gpt-5-mini",
            input=prompt,
            reasoning={"effort": "low"},
            text={"verbosity": "low"},
        )
        
        raw_text = result.output_text.strip()
        
        # Handle potential markdown code blocks
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            # Remove first and last lines (```json and ```)
            raw_text = "\n".join(lines[1:-1]) if len(lines) > 2 else raw_text
            if raw_text.startswith("json"):
                raw_text = raw_text[4:].strip()
        
        report = json.loads(raw_text)
        return report
        
    except json.JSONDecodeError as e:
        # Fallback: build report from existing data
        anomaly_items_tr = []
        anomaly_items_en = []
        for a in anomaly_details:
            anomaly_items_tr.append({
                "metric": a["metric_tr"],
                "change": f"{a['pct_change']} {a['direction']}",
                "why_anomaly": a["detection_reasoning"] or "Eşik değerleri aşıldı",
                "root_cause": a["root_cause_tr"] or "Detaylı analiz bekleniyor"
            })
            anomaly_items_en.append({
                "metric": a["metric"],
                "change": a["pct_change"],
                "why_anomaly": a["detection_reasoning"] or "Thresholds exceeded",
                "root_cause": a["root_cause_en"] or "Detailed analysis pending"
            })
        
        return {
            "report_tr": {
                "title": f"{month_label} Finansal Anomali Özet Raporu",
                "overview": f"Bu dönemde {len(anomalies)} finansal anomali tespit edilmiştir.",
                "anomalies": anomaly_items_tr,
                "action_recommendations": ["Detaylı inceleme yapılması önerilir"]
            },
            "report_en": {
                "title": f"{month_label} Financial Anomaly Summary Report",
                "overview": f"{len(anomalies)} financial anomalies were detected this period.",
                "anomalies": anomaly_items_en,
                "action_recommendations": ["Detailed review recommended"]
            },
            "error": f"Could not parse LLM response: {e}"
        }
    except Exception as e:
        return {
            "report_tr": {
                "title": f"{month_label} Finansal Anomali Özet Raporu",
                "overview": f"Bu dönemde {len(anomalies)} anomali tespit edildi.",
                "anomalies": [],
                "action_recommendations": []
            },
            "report_en": {
                "title": f"{month_label} Financial Anomaly Summary Report",
                "overview": f"{len(anomalies)} anomalies were detected this period.",
                "anomalies": [],
                "action_recommendations": []
            },
            "error": str(e)
        }


def get_company_info(conn: psycopg.Connection, company_id: UUID) -> dict:
    """
    Get company information.
    
    Args:
        conn: Database connection
        company_id: Internal company UUID
    
    Returns:
        dict: Company info
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id, finsmart_guid, name, business_model, created_at
            FROM companies
            WHERE id = %s
            """,
            (str(company_id),)
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Company {company_id} not found")
        return dict(row)


def get_metrics_overview(
    conn: psycopg.Connection,
    company_id: UUID,
    month: date
) -> list[dict]:
    """
    Get all metrics for a month with MoM comparison.
    
    Args:
        conn: Database connection
        company_id: Internal company UUID
        month: Target month (first of month)
    
    Returns:
        List of metric dictionaries with prev/curr/change
    """
    # Calculate previous month
    if month.month == 1:
        prev_month = month.replace(year=month.year - 1, month=12)
    else:
        prev_month = month.replace(month=month.month - 1)
    
    # Get current month KPIs
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT metric_name, value
            FROM monthly_kpis
            WHERE company_id = %s AND month = %s
            """,
            (str(company_id), month)
        )
        current_kpis = {row["metric_name"]: row["value"] for row in cur.fetchall()}
    
    # Get previous month KPIs
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT metric_name, value
            FROM monthly_kpis
            WHERE company_id = %s AND month = %s
            """,
            (str(company_id), prev_month)
        )
        prev_kpis = {row["metric_name"]: row["value"] for row in cur.fetchall()}
    
    # Get anomalies for this month
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT metric_name
            FROM anomalies
            WHERE company_id = %s AND month = %s
            """,
            (str(company_id), month)
        )
        anomaly_metrics = {row[0] for row in cur.fetchall()}
    
    # Build overview
    metrics = []
    all_metric_names = set(current_kpis.keys()) | set(prev_kpis.keys())
    
    for metric_name in sorted(all_metric_names):
        curr_val = current_kpis.get(metric_name)
        prev_val = prev_kpis.get(metric_name)
        
        # Calculate percentage change
        pct_change = None
        if prev_val and prev_val != 0 and curr_val is not None:
            pct_change = float((curr_val - prev_val) / abs(prev_val) * 100)
        
        metrics.append({
            "metric_name": metric_name,
            "metric_name_tr": metric_name_tr(metric_name),
            "prev_value": float(prev_val) if prev_val else None,
            "curr_value": float(curr_val) if curr_val else None,
            "prev_formatted": format_amount_tr(prev_val) if prev_val else "-",
            "curr_formatted": format_amount_tr(curr_val) if curr_val else "-",
            "pct_change": round(pct_change, 1) if pct_change else None,
            "is_anomalous": metric_name in anomaly_metrics,
        })
    
    return metrics


def get_anomaly_details(
    conn: psycopg.Connection,
    company_id: UUID,
    month: date,
    generate_missing_highlights: bool = True
) -> list[dict]:
    """
    Get detailed anomaly information for a month.
    
    Args:
        conn: Database connection
        company_id: Internal company UUID
        month: Target month
        generate_missing_highlights: If True, generate highlights on-the-fly
    
    Returns:
        List of detailed anomaly dictionaries
    """
    import sys
    
    anomalies = get_anomalies_for_month(conn, company_id, str(month))
    
    details = []
    total = len(anomalies)
    for i, anomaly in enumerate(anomalies, 1):
        anomaly_id = anomaly["id"]
        metric = anomaly["metric_name"]
        
        print(f"  [{i}/{total}] Processing anomaly: {metric}...", file=sys.stderr)
        
        # Get contributors
        contributors = get_contributors_for_anomaly(conn, anomaly_id)
        print(f"    - Found {len(contributors)} contributors", file=sys.stderr)
        
        # Get highlights
        highlights = get_highlights_for_anomaly(conn, anomaly_id)
        
        # Generate missing highlights on-the-fly
        if generate_missing_highlights and not highlights.get("tr"):
            print(f"    - Generating LLM explanation (gpt-5-mini)...", file=sys.stderr)
            try:
                generate_highlight_for_anomaly(conn, anomaly_id)
                highlights = get_highlights_for_anomaly(conn, anomaly_id)
                print(f"    - ✓ Explanation generated", file=sys.stderr)
            except Exception as e:
                print(f"    - ✗ Could not generate highlights: {e}", file=sys.stderr)
        else:
            print(f"    - Explanation already exists", file=sys.stderr)
        
        # Get evidence sample
        evidence = get_evidence_transactions(
            conn, company_id, str(month), anomaly["metric_name"], limit=10
        )
        print(f"    - Found {len(evidence)} evidence transactions", file=sys.stderr)
        
        # Get detection metadata
        meta = anomaly.get("meta") or {}
        if isinstance(meta, str):
            import json
            meta = json.loads(meta)
        
        # Get LLM explanation of why this is an anomaly
        detection_reasoning = None
        if generate_missing_highlights and meta:
            print(f"    - Generating detection reasoning (gpt-5-nano)...", file=sys.stderr)
            try:
                detection_reasoning = explain_anomaly_detection(anomaly)
                print(f"    - ✓ Detection reasoning generated", file=sys.stderr)
            except Exception as e:
                print(f"    - ✗ Could not generate detection reasoning: {e}", file=sys.stderr)
        
        details.append({
            "metric_name": anomaly["metric_name"],
            "metric_name_tr": metric_name_tr(anomaly["metric_name"]),
            "prev_value": float(anomaly["prev_value"]) if anomaly["prev_value"] else None,
            "curr_value": float(anomaly["curr_value"]) if anomaly["curr_value"] else None,
            "prev_formatted": format_amount_tr(anomaly["prev_value"]) if anomaly["prev_value"] else "-",
            "curr_formatted": format_amount_tr(anomaly["curr_value"]) if anomaly["curr_value"] else "-",
            "pct_change": round(float(anomaly["pct_change"]), 1) if anomaly["pct_change"] else None,
            "severity_score": round(float(anomaly["severity_score"]), 1) if anomaly["severity_score"] else None,
            "status": anomaly["status"],
            # Detection context
            "detection": {
                "reason": meta.get("detection_reason"),
                "yoy_value": meta.get("yoy_value"),
                "yoy_pct": round(float(meta.get("yoy_pct", 0)), 1) if meta.get("yoy_pct") else None,
                "rolling_3m_avg": meta.get("rolling_3m_avg"),
                "rolling_pct": round(float(meta.get("rolling_pct", 0)), 1) if meta.get("rolling_pct") else None,
                "zscore": round(float(meta.get("zscore", 0)), 2) if meta.get("zscore") else None,
                "reasoning": detection_reasoning,
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
            "highlights": highlights,
            "evidence_sample": [
                {
                    "date": str(e["tx_date"]),
                    "account_code": e["account_code"],
                    "account_name": e["account_name"],
                    "coa_code": e["coa_code"],
                    "coa_name": e["coa_name"],
                    "description": e["description"],
                    "customer_name": e["customer_name"],
                    "amount": float(e["amount"]),
                    "amount_formatted": format_amount_tr(e["amount"]),
                }
                for e in evidence
            ],
        })
    
    return details


def has_data_for_month(conn: psycopg.Connection, company_id: UUID, month: date) -> dict:
    """Check if data already exists for this month."""
    with conn.cursor() as cur:
        # Check KPIs
        cur.execute(
            "SELECT COUNT(*) FROM monthly_kpis WHERE company_id = %s AND month = %s",
            (str(company_id), month)
        )
        kpi_count = cur.fetchone()[0]
        
        # Check anomalies
        cur.execute(
            "SELECT COUNT(*) FROM anomalies WHERE company_id = %s AND month = %s",
            (str(company_id), month)
        )
        anomaly_count = cur.fetchone()[0]
        
        # Check contributors for this month's anomalies
        cur.execute(
            """
            SELECT COUNT(*) FROM anomaly_contributors ac
            JOIN anomalies a ON ac.anomaly_id = a.id
            WHERE a.company_id = %s AND a.month = %s
            """,
            (str(company_id), month)
        )
        contributor_count = cur.fetchone()[0]
    
    return {
        "kpis": kpi_count,
        "anomalies": anomaly_count,
        "contributors": contributor_count,
        "complete": kpi_count > 0 and anomaly_count >= 0 and contributor_count >= 0
    }


def build_cfo_month_view(
    conn: psycopg.Connection,
    company_id: UUID,
    month: date,
    ensure_computed: bool = True,
    generate_highlights: bool = True
) -> dict:
    """
    Build comprehensive CFO view for a company and month.
    
    This is the main entrypoint for UI and agents.
    
    Args:
        conn: Database connection
        company_id: Internal company UUID
        month: Target month (will be normalized to first of month)
        ensure_computed: If True, run compute pipeline first (if needed)
        generate_highlights: If True, generate missing highlights
    
    Returns:
        dict: Complete CFO view with metrics, anomalies, and evidence
    """
    import sys
    
    # Normalize month to first of month
    month = month.replace(day=1)
    month_str = month.strftime("%Y-%m")
    
    print(f"[CFO View] Building view for {month_str}...", file=sys.stderr)
    
    # Check if data already exists
    existing = has_data_for_month(conn, company_id, month)
    print(f"[CFO View] Existing data: {existing['kpis']} KPIs, {existing['anomalies']} anomalies, {existing['contributors']} contributors", file=sys.stderr)
    
    # Only recompute if ensure_computed=True AND data is missing
    if ensure_computed and not existing["complete"]:
        print("[CFO View] Data incomplete, running compute pipeline...", file=sys.stderr)
        compute_monthly_kpis(conn, company_id)
        detect_anomalies(conn, company_id)
        compute_contributors_for_company(conn, company_id)
        
        if generate_highlights:
            generate_highlights_for_new_anomalies(conn, company_id, batch_size=10)
    elif ensure_computed:
        print("[CFO View] Data already exists, skipping recompute.", file=sys.stderr)
    else:
        print("[CFO View] Skip-compute mode, using existing data.", file=sys.stderr)
    
    # Get company info
    print(f"[CFO View] Fetching company info...", file=sys.stderr)
    company = get_company_info(conn, company_id)
    
    # Get metrics overview
    print(f"[CFO View] Fetching metrics overview for {month_str}...", file=sys.stderr)
    metrics_overview = get_metrics_overview(conn, company_id, month)
    print(f"[CFO View] Found {len(metrics_overview)} metrics.", file=sys.stderr)
    
    # Get anomaly details
    print(f"[CFO View] Fetching anomaly details for {month_str}...", file=sys.stderr)
    anomalies = get_anomaly_details(
        conn, company_id, month,
        generate_missing_highlights=generate_highlights
    )
    print(f"[CFO View] Found {len(anomalies)} anomalies for this month.", file=sys.stderr)
    
    # Build summary
    total_anomalies = len(anomalies)
    positive_anomalies = sum(1 for a in anomalies if a["pct_change"] and a["pct_change"] > 0)
    negative_anomalies = total_anomalies - positive_anomalies
    
    print(f"[CFO View] Summary: {total_anomalies} anomalies ({positive_anomalies} positive, {negative_anomalies} negative)", file=sys.stderr)
    
    # Generate consolidated executive report
    executive_report = None
    if generate_highlights and anomalies:
        print(f"[CFO View] Generating consolidated executive report (gpt-5-mini)...", file=sys.stderr)
        try:
            executive_report = generate_executive_report(
                company_name=company["name"],
                month_label=month_label_tr(month),
                anomalies=anomalies
            )
            print(f"[CFO View] ✓ Executive report generated", file=sys.stderr)
        except Exception as e:
            print(f"[CFO View] ✗ Could not generate executive report: {e}", file=sys.stderr)
    
    print(f"[CFO View] Done! Outputting JSON...", file=sys.stderr)
    
    return {
        "company": {
            "id": str(company["id"]),
            "finsmart_guid": str(company["finsmart_guid"]),
            "name": company["name"],
            "business_model": company["business_model"],
        },
        "month": str(month),
        "month_label_tr": month_label_tr(month),
        "summary": {
            "total_metrics": len(metrics_overview),
            "total_anomalies": total_anomalies,
            "positive_anomalies": positive_anomalies,
            "negative_anomalies": negative_anomalies,
        },
        "metrics_overview": metrics_overview,
        "anomalies": anomalies,
        # Consolidated executive report at the end
        "executive_report": executive_report,
    }


def format_report_markdown(report: dict, language: str = "tr") -> str:
    """
    Format executive report as professional Markdown.
    
    Args:
        report: Executive report dict with report_tr and report_en
        language: 'tr' for Turkish, 'en' for English
    
    Returns:
        Formatted Markdown string
    """
    lang_report = report.get(f"report_{language}", {})
    
    if not lang_report:
        return f"# Report not available for language: {language}"
    
    lines = []
    
    # Title
    title = lang_report.get("title", "Financial Report")
    lines.append(f"# {title}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Overview section
    if language == "tr":
        lines.append("## Genel Değerlendirme")
    else:
        lines.append("## Executive Overview")
    lines.append("")
    lines.append(lang_report.get("overview", ""))
    lines.append("")
    
    # Anomalies section
    anomalies = lang_report.get("anomalies", [])
    if anomalies:
        if language == "tr":
            lines.append("## Tespit Edilen Anomaliler")
        else:
            lines.append("## Detected Anomalies")
        lines.append("")
        
        for i, a in enumerate(anomalies, 1):
            metric = a.get("metric", "Unknown")
            change = a.get("change", "N/A")
            
            lines.append(f"### {i}. {metric}")
            lines.append("")
            
            if language == "tr":
                lines.append(f"**Değişim:** {change}")
                lines.append("")
                lines.append(f"**Neden Anomali?**")
                lines.append(f"> {a.get('why_anomaly', 'Bilgi mevcut değil')}")
                lines.append("")
                lines.append(f"**Kök Neden Analizi:**")
                lines.append(f"> {a.get('root_cause', 'Analiz bekleniyor')}")
            else:
                lines.append(f"**Change:** {change}")
                lines.append("")
                lines.append(f"**Why Anomaly?**")
                lines.append(f"> {a.get('why_anomaly', 'Information not available')}")
                lines.append("")
                lines.append(f"**Root Cause Analysis:**")
                lines.append(f"> {a.get('root_cause', 'Analysis pending')}")
            
            lines.append("")
    
    # Action recommendations
    actions = lang_report.get("action_recommendations", [])
    if actions:
        lines.append("---")
        lines.append("")
        if language == "tr":
            lines.append("## Aksiyon Önerileri")
        else:
            lines.append("## Recommended Actions")
        lines.append("")
        
        for action in actions:
            lines.append(f"- {action}")
        lines.append("")
    
    # Footer
    lines.append("---")
    lines.append("")
    if language == "tr":
        lines.append("*Bu rapor otomatik olarak oluşturulmuştur.*")
    else:
        lines.append("*This report was generated automatically.*")
    
    return "\n".join(lines)


def save_reports_to_files(
    report: dict,
    company_name: str,
    month_str: str,
    output_dir: str = "."
) -> dict:
    """
    Save executive reports as Markdown files.
    
    Args:
        report: Executive report dict
        company_name: Company name for filename
        month_str: Month string (YYYY-MM)
        output_dir: Directory to save files
    
    Returns:
        dict with file paths
    """
    import os
    import re
    
    # Sanitize company name for filename
    safe_name = re.sub(r'[^\w\-]', '_', company_name.lower())
    
    files = {}
    
    for lang in ["tr", "en"]:
        md_content = format_report_markdown(report, lang)
        filename = f"report_{safe_name}_{month_str}_{lang}.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        files[lang] = filepath
    
    return files


def get_available_months(
    conn: psycopg.Connection,
    company_id: UUID
) -> list[str]:
    """
    Get list of months with data for a company.
    
    Args:
        conn: Database connection
        company_id: Internal company UUID
    
    Returns:
        List of month strings (YYYY-MM-DD format)
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT month
            FROM monthly_kpis
            WHERE company_id = %s
            ORDER BY month DESC
            """,
            (str(company_id),)
        )
        return [str(row[0]) for row in cur.fetchall()]


def get_company_by_guid(
    conn: psycopg.Connection,
    finsmart_guid: str
) -> Optional[dict]:
    """
    Get company by Finsmart GUID.
    
    Args:
        conn: Database connection
        finsmart_guid: Finsmart company GUID
    
    Returns:
        Company dict or None if not found
    """
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT * FROM companies WHERE finsmart_guid = %s",
            (finsmart_guid,)
        )
        return cur.fetchone()
