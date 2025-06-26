import { google } from "googleapis";

export async function getPuzzleByDate(dateIso: string) {
  const auth = new google.auth.GoogleAuth({
    credentials: JSON.parse(Buffer.from(process.env.GOOGLE_SERVICE_ACCOUNT_KEY!, "base64").toString()),
    scopes: ["https://www.googleapis.com/auth/spreadsheets.readonly"],
  });
  const sheets = google.sheets({ version: "v4", auth });
  const range = "puzzles!A2:E"; // skip header
  const res = await sheets.spreadsheets.values.get({
    spreadsheetId: process.env.GOOGLE_SHEETS_ID,
    range,
  });

  const rows = res.data.values ?? [];
  const row = rows.find((r) => r[0] === dateIso);
  if (!row) return null;

  const [, puzzle_id, groups, author, todays_theme] = row;
  return {
    date: dateIso,
    puzzle_id: Number(puzzle_id),
    groups: JSON.parse(groups),
    author,
    todays_theme,
  };
}
