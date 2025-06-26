import json
import os
import datetime as dt
import base64
import gspread


def get_sheet():
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
    cell = ws.find(date)
    if cell:
        ws.update(f"A{cell.row}:E{cell.row}", [row])
    else:
        ws.append_row(row, value_input_option="USER_ENTERED")

