from __future__ import annotations

import logging
import time

import anyio
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse
from functools import partial

from api.engine import IndexManager, resolve_asset_urls
from api.models import DocsetOut, OpenRequest, OpenResponse, ReindexRequest, SearchRequest, SearchResponse
from api.settings import Settings

settings = Settings.from_env()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("docs_api")
manager = IndexManager(settings)
app = FastAPI(title="Docs Retrieval API", version="0.1.0")


def _auth(authorization: str | None = Header(default=None)) -> None:
    if not settings.token:
        return
    expected = f"Bearer {settings.token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.on_event("startup")
async def _startup() -> None:
    if not settings.auto_index:
        return
    await anyio.to_thread.run_sync(manager.ensure_ready)


@app.get("/docsets", response_model=list[DocsetOut], dependencies=[Depends(_auth)])
async def list_docsets():
    try:
        docsets = await anyio.to_thread.run_sync(manager.registry_docsets)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return [
        DocsetOut(
            docset_id=d.docset_id,
            root_path=str(d.root_path),
            tags=list(d.tags),
            keywords=list(d.keywords),
            version=d.version,
            enabled=d.enabled,
        )
        for d in docsets
    ]


@app.post("/reindex", dependencies=[Depends(_auth)])
async def reindex(req: ReindexRequest):
    started = time.perf_counter()
    try:
        await anyio.to_thread.run_sync(partial(manager.reindex, docset_ids=req.docset_ids))
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"ok": True, "elapsed_ms": int((time.perf_counter() - started) * 1000)}


@app.post("/search", response_model=SearchResponse, dependencies=[Depends(_auth)])
async def search(req: SearchRequest):
    try:
        payload = await anyio.to_thread.run_sync(
            partial(
                manager.search,
                source_hint=req.source_hint,
                context=req.context,
                top_k=req.top_k,
            ),
            req.query,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    routing = payload["routing"]
    results = payload["results"]
    return SearchResponse(
        results=results,
        routing={"selected_docsets": routing.selected_docsets, "reasons": routing.reasons},
    )


@app.post("/open", response_model=OpenResponse, dependencies=[Depends(_auth)])
async def open_doc(req: OpenRequest):
    try:
        section = await anyio.to_thread.run_sync(manager.open, req.doc_ref)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    docset = await anyio.to_thread.run_sync(manager.get_docset, section.docset_id)
    logger.info("open_done doc_ref=%s docset_id=%s", req.doc_ref, section.docset_id)
    assets = resolve_asset_urls(docset, list(section.assets))
    return OpenResponse(
        doc_ref=req.doc_ref,
        docset_id=section.docset_id,
        title=section.heading_path[-1] if section.heading_path else "Untitled",
        heading_path=list(section.heading_path),
        file_path=section.file_path,
        anchor=section.anchor,
        url=f"file://{docset.root_path / section.file_path}{section.anchor}",
        text=section.text,
        code_blocks=list(section.code_blocks),
        assets=assets,
        version=docset.version,
    )


@app.get("/asset", dependencies=[Depends(_auth)])
async def asset(docset_id: str = Query(min_length=1), path: str = Query(min_length=1)):
    try:
        target = await anyio.to_thread.run_sync(partial(manager.asset_path, docset_id=docset_id, relative_path=path))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return FileResponse(target)
