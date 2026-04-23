import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

/** Serves MSAL and backend config from server-side env vars at runtime.
 * This lets Container App env vars take effect without rebuilding the image.
 */
export async function GET() {
  return NextResponse.json({
    clientId: process.env.ENTRA_CLIENT_ID ?? "",
    authority:
      process.env.ENTRA_AUTHORITY ?? "https://login.microsoftonline.com/common",
    redirectUri: process.env.ENTRA_REDIRECT_URI ?? "",
    apiScope: process.env.ENTRA_API_SCOPE ?? "",
    devBypassAuth: process.env.DEV_BYPASS_AUTH === "true",
  });
}
