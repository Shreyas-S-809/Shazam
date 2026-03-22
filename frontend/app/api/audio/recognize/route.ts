import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

// Disable Next.js body parsing — we forward the raw stream to the backend
export const dynamic = "force-dynamic";

const BACKEND =
  process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(req: NextRequest) {
  try {
    const contentType = req.headers.get("content-type") || "";

    // Forward the source query param ("mic" | "upload") to the backend
    const source = req.nextUrl.searchParams.get("source") || "upload";

    // Forward the entire multipart body as-is to the FastAPI backend
    const backendRes = await fetch(
      `${BACKEND}/api/audio/recognize?source=${encodeURIComponent(source)}`,
      {
        method: "POST",
        headers: { "content-type": contentType },
        body: req.body,
        // @ts-expect-error -- Node 18+ fetch supports duplex for streaming
        duplex: "half",
      }
    );

    const data = await backendRes.json();
    return NextResponse.json(data, { status: backendRes.status });
  } catch (err) {
    console.error("Proxy to backend failed:", err);
    return NextResponse.json(
      { success: false, error: "Backend unavailable. Please try again." },
      { status: 502 }
    );
  }
}
