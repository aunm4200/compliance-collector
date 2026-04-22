"use client";

import { devBypassAuth, initializeMsal, tokenRequest } from "./msalConfig";

async function getToken(): Promise<string | null> {
  if (devBypassAuth) return null;
  const instance = await initializeMsal();
  if (!instance) return null;
  const account = instance.getActiveAccount() || instance.getAllAccounts()[0];
  if (!account) return null;
  try {
    const resp = await instance.acquireTokenSilent({ ...tokenRequest, account });
    instance.setActiveAccount(resp.account);
    return resp.accessToken;
  } catch {
    const resp = await instance.acquireTokenPopup({ ...tokenRequest, account });
    instance.setActiveAccount(resp.account);
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
