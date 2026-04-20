"use client";

import { PublicClientApplication } from "@azure/msal-browser";
import { devBypassAuth, msalConfig, tokenRequest } from "./msalConfig";

let _pca: PublicClientApplication | null = null;
function pca(): PublicClientApplication | null {
  if (devBypassAuth) return null;
  if (typeof window === "undefined") return null;
  if (_pca) return _pca;
  _pca = new PublicClientApplication(msalConfig);
  return _pca;
}

async function getToken(): Promise<string | null> {
  if (devBypassAuth) return null;
  const instance = pca();
  if (!instance) return null;
  const account = instance.getActiveAccount() || instance.getAllAccounts()[0];
  if (!account) return null;
  try {
    const resp = await instance.acquireTokenSilent({ ...tokenRequest, account });
    return resp.accessToken;
  } catch {
    const resp = await instance.acquireTokenPopup(tokenRequest);
    return resp.accessToken;
  }
}

export async function api<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getToken();
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`/api/backend${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}
