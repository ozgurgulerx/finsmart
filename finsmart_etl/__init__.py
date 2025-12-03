"""
Finsmart ETL - AI CFO Backend

A YC-grade financial data pipeline that:
- Ingests data from Finsmart API (Bronze)
- Normalizes transactions (Silver)
- Computes monthly KPIs (Gold)
- Detects anomalies (±20% MoM)
- Generates LLM explanations
- Provides CFO Month View
"""

__version__ = "0.1.0"
