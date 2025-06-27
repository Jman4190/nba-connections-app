import { NextResponse } from "next/server";
import { getPuzzleByDate, getLatestPuzzle } from "@/lib/getPuzzleFromSheet";

export const runtime = "nodejs";

export async function GET(req: Request) {
  const date = new URL(req.url).searchParams.get("date");
  if (date) {
    const puzzle = await getPuzzleByDate(date);
    if (puzzle) return NextResponse.json(puzzle);
  }

  const latest = await getLatestPuzzle();
  return latest
    ? NextResponse.json(latest)
    : NextResponse.json({ error: "not found" }, { status: 404 });
}
