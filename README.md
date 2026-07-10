# AP Invoice Doc Classification & Vendor Name Matching — Analysis Dashboard

The complete end-to-end project lives in one folder:

## 👉 [`ap-invoice-doc-classfn-vendorname-analysis/`](ap-invoice-doc-classfn-vendorname-analysis/)

It contains everything:

| Folder | What it is |
|---|---|
| [`dashboard/`](ap-invoice-doc-classfn-vendorname-analysis/dashboard/) | **Frontend + backends** — the React/Vite review app, the Flask/Gmail email backend, and the serverless entry |
| [`data-fetching/`](ap-invoice-doc-classfn-vendorname-analysis/data-fetching/) | **Data fetching** — Metabase-API pull scripts + `query.md` (the SQL); a prod-DB connection can replace this later |
| [`docs/`](ap-invoice-doc-classfn-vendorname-analysis/docs/) | `workflow-architecture.html` — the end-to-end workflow & architecture, viewable in a browser |

**Start here:** [`ap-invoice-doc-classfn-vendorname-analysis/README.md`](ap-invoice-doc-classfn-vendorname-analysis/README.md) — full setup, run, data flow, and everything else.

```bash
cd ap-invoice-doc-classfn-vendorname-analysis/dashboard
npm install && npm run dev
```

> No customer data is committed. Generate data with the pipeline in `data-fetching/` (or upload an
> Excel file via the dashboard's Get Data screen) before reviewing.
