import { Configuration, LogLevel, PublicClientApplication } from "@azure/msal-browser";

export const msalConfig: Configuration = {
  auth: {
    clientId: process.env.NEXT_PUBLIC_ENTRA_CLIENT_ID || "",
    authority:
      process.env.NEXT_PUBLIC_ENTRA_AUTHORITY ||
      "https://login.microsoftonline.com/common",
    redirectUri:
      process.env.NEXT_PUBLIC_ENTRA_REDIRECT_URI ||
      (typeof window !== "undefined" ? `${window.location.origin}/auth/callback` : ""),
    postLogoutRedirectUri:
      typeof window !== "undefined" ? window.location.origin : undefined,
    navigateToLoginRequestUrl: true,
  },
  cache: {
    cacheLocation: "sessionStorage",
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) return;
        if (level === LogLevel.Error) console.error(message);
      },
      logLevel: LogLevel.Warning,
    },
  },
};

export const apiScope =
  process.env.NEXT_PUBLIC_ENTRA_API_SCOPE || "api://placeholder/access_as_user";

export const loginRequest = { scopes: ["openid", "profile", "email", apiScope] };
export const tokenRequest = { scopes: [apiScope] };

export const devBypassAuth =
  process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === "true";

let _msalInstance: PublicClientApplication | null = null;
let _msalInitPromise: Promise<void> | null = null;

export function getMsalInstance(): PublicClientApplication | null {
  if (devBypassAuth) return null;
  if (typeof window === "undefined") return null;
  if (_msalInstance) return _msalInstance;

  _msalInstance = new PublicClientApplication(msalConfig);

  const existingAccount = _msalInstance.getActiveAccount() || _msalInstance.getAllAccounts()[0];
  if (existingAccount) {
    _msalInstance.setActiveAccount(existingAccount);
  }

  return _msalInstance;
}

export async function initializeMsal(): Promise<PublicClientApplication | null> {
  const instance = getMsalInstance();
  if (!instance) return null;

  if (!_msalInitPromise) {
    _msalInitPromise = instance.initialize().then(() => {
      const existingAccount = instance.getActiveAccount() || instance.getAllAccounts()[0];
      if (existingAccount) {
        instance.setActiveAccount(existingAccount);
      }
    });
  }

  await _msalInitPromise;
  return instance;
}
