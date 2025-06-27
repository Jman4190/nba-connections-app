import { google } from "googleapis";

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

export async function getPuzzleByDate(dateIso: string) {
  console.log(`getPuzzleByDate: ${dateIso}`);
  const sheets = google.sheets({ version: "v4", auth: getAuth() });
  const range = "puzzles!A2:E"; // skip header
  const res = await sheets.spreadsheets.values.get({
    spreadsheetId: process.env.GOOGLE_SHEETS_ID,
    range,
  });

  const rows = res.data.values ?? [];
  const row = rows.find((r) => r[0] === dateIso);
  if (!row) {
    console.warn(`Puzzle not found for ${dateIso}`);
    return null;
  }

  const [, puzzle_id, groups, author, todays_theme] = row;
  try {
    return {
      date: dateIso,
      puzzle_id: Number(puzzle_id),
      groups: JSON.parse(groups),
      author,
      todays_theme,
    };
  } catch (err) {
    console.error(`Error parsing groups for ${dateIso}`, err);
    return null;
  }
}

export async function getLatestPuzzle() {
  console.log("getLatestPuzzle");
  const sheets = google.sheets({ version: "v4", auth: getAuth() });
  const range = "puzzles!A2:E";
  const res = await sheets.spreadsheets.values.get({
    spreadsheetId: process.env.GOOGLE_SHEETS_ID,
    range,
  });

  const rows = res.data.values ?? [];
  if (rows.length === 0) return null;

  const [date, puzzle_id, groups, author, todays_theme] = rows[rows.length - 1];
  console.log(`Latest puzzle date: ${date}`);
  try {
    return {
      date,
      puzzle_id: Number(puzzle_id),
      groups: JSON.parse(groups),
      author,
      todays_theme,
    };
  } catch (err) {
    console.error("Error parsing latest puzzle", err);
    return null;
  }
}
