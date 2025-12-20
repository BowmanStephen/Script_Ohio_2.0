import { NextResponse } from "next/server";
import { loadBowlPredictions } from "@/src/data/loaders";

export async function GET() {
  try {
    const bowlData = await loadBowlPredictions(2025);
    return NextResponse.json(bowlData);
  } catch (error) {
    console.error("Failed to load bowl predictions:", error);
    return NextResponse.json(
      { error: "Failed to load bowl predictions" },
      { status: 500 }
    );
  }
}
