import { NextResponse } from "next/server";
import { getPuzzleByDate } from "@/lib/getPuzzleFromSheet";

export const runtime = "nodejs";

export async function GET(req: Request) {
  const date = new URL(req.url).searchParams.get("date");
  if (!date) return NextResponse.json({ error: "date required" }, { status: 400 });

  const puzzle = await getPuzzleByDate(date);
  return puzzle
    ? NextResponse.json(puzzle)
    : NextResponse.json({ error: "not found" }, { status: 404 });
}
