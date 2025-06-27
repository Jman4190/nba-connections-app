import json
import os
import datetime as dt
import base64
import logging
import gspread

logger = logging.getLogger(__name__)


def get_sheet():
    logger.debug("Opening Google sheet")
    sa_info = json.loads(
        base64.b64decode(os.environ["GOOGLE_SERVICE_ACCOUNT_KEY"]).decode()
    )
    gc = gspread.service_account_from_dict(sa_info)
    return gc.open_by_key(os.environ["GOOGLE_SHEETS_ID"]).worksheet("puzzles")


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

