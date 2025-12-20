import { NextResponse } from "next/server";
import { loadExternalModelAnalysis } from "@/src/data/loaders";

export async function GET() {
  try {
    const analysis = await loadExternalModelAnalysis();
    return NextResponse.json(analysis);
  } catch (error) {
    console.error("Failed to load analytics:", error);
    return NextResponse.json(
      { error: "Failed to load analytics" },
      { status: 500 }
    );
  }
}
