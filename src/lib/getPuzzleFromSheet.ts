import { google } from "googleapis";

function parseGroups(raw: string) {
  const trimmed = raw?.trim() ?? "";
  try {
    return JSON.parse(trimmed);
  } catch (err) {
    try {
      if (
        (trimmed.startsWith('"') && trimmed.endsWith('"')) ||
        (trimmed.startsWith("'") && trimmed.endsWith("'"))
      ) {
        return JSON.parse(trimmed.slice(1, -1));
      }
    } catch {
      // ignore
    }
    console.error("Failed to parse groups", trimmed.slice(0, 30), err);
    return null;
  }
}

function getSheets() {
  const sheetId = process.env.GOOGLE_SHEETS_ID;
  if (!sheetId) {
    console.error("GOOGLE_SHEETS_ID env var missing");
    throw new Error("missing GOOGLE_SHEETS_ID");
  }
  const auth = getAuth();
  console.log(`Connecting to sheet ${sheetId}`);
  return { sheets: google.sheets({ version: "v4", auth }), sheetId };
}

function getAuth() {
  const raw = process.env.GOOGLE_SERVICE_ACCOUNT_KEY;
  if (!raw) {
    console.error("GOOGLE_SERVICE_ACCOUNT_KEY env var missing");
    throw new Error("missing google credentials");
  }
  try {
    const json = Buffer.from(raw, "base64").toString();
    return new google.auth.GoogleAuth({
      credentials: JSON.parse(json),
      scopes: ["https://www.googleapis.com/auth/spreadsheets.readonly"],
    });
  } catch (err) {
    console.error("Failed to decode GOOGLE_SERVICE_ACCOUNT_KEY, trying raw JSON", err);
    try {
      return new google.auth.GoogleAuth({
        credentials: JSON.parse(raw),
        scopes: ["https://www.googleapis.com/auth/spreadsheets.readonly"],
      });
    } catch (err2) {
      console.error("Invalid GOOGLE_SERVICE_ACCOUNT_KEY", err2);
      throw err2;
    }
  }
}

async function fetchRows() {
  const { sheets, sheetId } = getSheets();
  const range = "puzzles!A2:F";
  console.log(`Fetching range ${range}`);
  try {
    const res = await sheets.spreadsheets.values.get({
      spreadsheetId: sheetId,
      range,
    });
    const rows = res.data.values ?? [];
    console.log(`Fetched ${rows.length} rows from sheet`);
    if (rows.length > 0) {
      console.debug(`First row: ${JSON.stringify(rows[0])}`);
    }
    return rows;
  } catch (err) {
    console.error("Failed to fetch rows from Google Sheets", err);
    throw err;
  }
}

export async function getPuzzleByDate(dateIso: string) {
  console.log(`getPuzzleByDate: ${dateIso}`);
  const rows = await fetchRows();
  const row = rows.find((r) => r[2] === dateIso);
  if (!row) {
    console.warn(`Puzzle not found for ${dateIso}`);
    return null;
  }

  const [, puzzle_id, , groups, author, todays_theme] = row;
  const parsed = parseGroups(groups);
  if (!parsed) {
    console.error(`Error parsing groups for ${dateIso}`);
    return null;
  }
  return {
    date: dateIso,
    puzzle_id: Number(puzzle_id),
    groups: parsed,
    author,
    todays_theme,
  };
}

export async function getLatestPuzzle() {
  console.log("getLatestPuzzle");
  const rows = await fetchRows();
  if (rows.length === 0) return null;

  const row = rows[rows.length - 1];
  console.log(`Latest row: ${JSON.stringify(row)}`);
  const [, puzzle_id, date, groups, author, todays_theme] = row;
  const parsed = parseGroups(groups);
  if (!parsed) {
    console.error("Error parsing latest puzzle");
    return null;
  }
  return {
    date,
    puzzle_id: Number(puzzle_id),
    groups: parsed,
    author,
    todays_theme,
  };
}
