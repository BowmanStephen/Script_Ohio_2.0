import { NextResponse } from "next/server";
import { loadWeeklyPredictions } from "@/src/data/loaders";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ week: string }> }
) {
  try {
    const { week } = await params;
    const weekNum = parseInt(week, 10);

    if (isNaN(weekNum) || weekNum < 1 || weekNum > 16) {
      return NextResponse.json(
        { error: "Invalid week number" },
        { status: 400 }
      );
    }

    const games = await loadWeeklyPredictions(weekNum, 2025);
    return NextResponse.json({ games });
  } catch (error) {
    console.error("Failed to load weekly predictions:", error);
    return NextResponse.json(
      { error: "Failed to load predictions" },
      { status: 500 }
    );
  }
}
