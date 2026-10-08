from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.database import create_tables
from backend.excel_service import create_inbound_fingerprint, read_purchase_statement_bytes
from backend.inbound_service import (
    inbound_import_exists,
    preview_inbound_rows,
    save_inbound_rows_auto,
)
from backend.inventory_service import get_all_reorder_analysis, get_inventory
from backend.order_service import create_order_request_excel

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="Consumables Order Automation API",
    version="1.0.0",
    description="Excel 구매자료를 DB에 반영하고 재고/수요 이력으로 발주요청서를 생성하는 API",
    lifespan=lifespan,
)


@app.get("/")
def root():
    return {
        "message": "Consumables Order Automation API",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/imports/inbound/preview")
async def preview_inbound_excel(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="xlsx 파일만 업로드할 수 있습니다.")

    try:
        file_bytes = await file.read()
        rows = read_purchase_statement_bytes(file_bytes, file.filename)
        fingerprint = create_inbound_fingerprint(rows)
        preview = preview_inbound_rows(rows)
        return {
            "filename": file.filename,
            "duplicate": inbound_import_exists(fingerprint),
            **preview,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/imports/inbound/commit")
async def commit_inbound_excel(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="xlsx 파일만 업로드할 수 있습니다.")

    try:
        file_bytes = await file.read()
        rows = read_purchase_statement_bytes(file_bytes, file.filename)
        fingerprint = create_inbound_fingerprint(rows)

        if inbound_import_exists(fingerprint):
            raise HTTPException(status_code=409, detail="이미 DB에 반영된 Excel입니다.")

        result = save_inbound_rows_auto(fingerprint, file.filename, rows)
        return {
            "message": "입고 Excel DB 반영 완료",
            "filename": file.filename,
            **result,
        }
    except HTTPException:
        raise
    except ValueError as exc:
        if str(exc) == "DUPLICATE_IMPORT":
            raise HTTPException(status_code=409, detail="이미 DB에 반영된 Excel입니다.") from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/inventory")
def inventory():
    return get_inventory()


@app.get("/analytics/reorder")
def reorder_analysis():
    return get_all_reorder_analysis()


@app.post("/orders/generate")
def generate_order_excel(within_days: int = 30):
    if within_days < 0 or within_days > 3650:
        raise HTTPException(status_code=400, detail="within_days는 0~3650 사이여야 합니다.")

    file_path = create_order_request_excel(within_days)
    if file_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"향후 {within_days}일 이내 발주 대상 품목이 없습니다.",
        )

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
