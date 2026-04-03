# 🗺️ Data Flow Diagram

> **Concept:** This diagram shows how data moves through the pipeline — from Kaggle download all the way to the final Excel report.

```mermaid
flowchart TD
    classDef ingestion fill:#fce4ec,stroke:#e91e63,color:#000
    classDef storage   fill:#e3f2fd,stroke:#1976d2,color:#000
    classDef compute   fill:#e8f5e9,stroke:#388e3c,color:#000
    classDef output    fill:#fff8e1,stroke:#f57f17,color:#000
    classDef infra     fill:#ede7f6,stroke:#7b1fa2,color:#000

    subgraph Ingest["📥 Ingest"]
        KI["kaggle_ingest.py\nDownload + map columns"]
        LD["load.py\nTruncate + write to DB"]
        KI --> LD
    end

    subgraph DB["🗄️ PostgreSQL (insurance schema)"]
        direction LR
        M["👤 member"]
        P["🏥 provider"]
        C["💊 claim"]
    end

    subgraph Transform["🔧 Transform"]
        TR["transform.py\nJoin tables · compute KPIs\ntrends · loss ratios"]
    end

    subgraph Model["🤖 ML Model"]
        MO["model.py\nLabel high-cost members\ntrain logistic regression"]
    end

    subgraph Outputs["📁 outputs/"]
        CSV1["kpis.csv"]
        CSV2["monthly.csv"]
        CSV3["loss_ratio.csv"]
        CSV4["network_summary.csv"]
        CSV5["diagnosis_summary.csv"]
        TXT["model_metrics.txt"]
    end

    subgraph Report["📊 Report"]
        RP["report.py\nCombine all outputs"]
        XL["insurance_summary.xlsx\n6-sheet workbook"]
        RP --> XL
    end

    subgraph Infra["⚙️ Infrastructure"]
        UT["utils.py\nDB connection · config loader"]
    end

    LD --> M & P & C
    UT -->|"shared by"| LD & TR & MO
    M & P & C --> TR & MO
    TR --> CSV1 & CSV2 & CSV3 & CSV4 & CSV5
    MO --> TXT
    CSV1 & CSV2 & CSV3 & CSV4 & CSV5 & TXT --> RP

    class KI,LD ingestion
    class M,P,C storage
    class TR,MO compute
    class CSV1,CSV2,CSV3,CSV4,CSV5,TXT,XL output
    class UT infra
```

---

## 📋 Key Data Handoffs

| From | To | What passes |
|------|-----|------------|
| `kaggle_ingest.py` | `load.py` | Pandas DataFrames (member, provider, claim) |
| `load.py` | PostgreSQL | 3 relational tables |
| PostgreSQL | `transform.py` | SQL JOINed query results |
| `transform.py` | `outputs/` | 5 CSV files |
| `model.py` | `outputs/` | `model_metrics.txt` |
| `outputs/` | `report.py` | 6 files → 6 Excel sheets |
