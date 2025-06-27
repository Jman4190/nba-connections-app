import json
import os
import datetime as dt
import base64
import logging
import gspread

logger = logging.getLogger(__name__)


def _load_sa_info():
    key = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY")
    if not key:
        logger.error("GOOGLE_SERVICE_ACCOUNT_KEY env var missing")
        raise RuntimeError("missing GOOGLE_SERVICE_ACCOUNT_KEY")
    try:
        decoded = base64.b64decode(key).decode()
        logger.debug("Decoded service account key from base64")
        return json.loads(decoded)
    except Exception:
        logger.debug("Service account key not base64, using raw JSON")
        return json.loads(key)


def get_sheet():
    sheet_id = os.environ.get("GOOGLE_SHEETS_ID")
    if not sheet_id:
        logger.error("GOOGLE_SHEETS_ID env var missing")
        raise RuntimeError("missing GOOGLE_SHEETS_ID")

    logger.debug("Opening Google sheet %s", sheet_id)
    try:
        sa_info = _load_sa_info()
        gc = gspread.service_account_from_dict(sa_info)
        return gc.open_by_key(sheet_id).worksheet("puzzles")
    except Exception as exc:
        logger.exception("Failed to open Google sheet: %s", exc)
        raise


def upsert_puzzle(puzzle):
    ws = get_sheet()
    date = dt.date.fromisoformat(puzzle["date"]).isoformat()
    row = [
        date,
        puzzle["puzzle_id"],
        json.dumps(puzzle["groups"]),
        puzzle["author"],
        puzzle.get("todays_theme"),
    ]
    logger.debug("Upserting puzzle for %s", date)
    cell = ws.find(date)
    if cell:
        ws.update(f"A{cell.row}:E{cell.row}", [row])
        logger.info("Updated puzzle for %s", date)
    else:
        ws.append_row(row, value_input_option="USER_ENTERED")
        logger.info("Inserted puzzle for %s", date)

