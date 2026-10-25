import api from "./api";

function urlBase64ToUint8Array(base64String: string) {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = window.atob(base64);
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
}

export async function isPushSupported() {
  return typeof window !== "undefined" && "serviceWorker" in navigator && "PushManager" in window;
}

export async function getPushSubscriptionStatus(): Promise<"unsupported" | "granted" | "denied" | "default"> {
  if (!(await isPushSupported())) return "unsupported";
  return Notification.permission;
}

/** Registers the service worker, requests permission, subscribes to push, and saves it on the backend. */
export async function subscribeToPush(): Promise<{ success: boolean; message: string }> {
  if (!(await isPushSupported())) {
    return { success: false, message: "Push notifications aren't supported in this browser." };
  }

  const permission = await Notification.requestPermission();
  if (permission !== "granted") {
    return { success: false, message: "Notification permission was not granted." };
  }

  const registration = await navigator.serviceWorker.register("/sw.js");
  await navigator.serviceWorker.ready;

  const { data } = await api.get("/notifications/push/vapid-public-key/");
  const applicationServerKey = urlBase64ToUint8Array(data.public_key);

  const subscription = await registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey,
  });

  const subJson = subscription.toJSON();
  await api.post("/notifications/push/subscribe/", {
    endpoint: subJson.endpoint,
    keys: subJson.keys,
  });

  return { success: true, message: "Push notifications enabled." };
}

export async function unsubscribeFromPush(): Promise<{ success: boolean; message: string }> {
  if (!(await isPushSupported())) return { success: false, message: "Not supported." };

  const registration = await navigator.serviceWorker.getRegistration();
  const subscription = await registration?.pushManager.getSubscription();
  if (!subscription) return { success: true, message: "Already unsubscribed." };

  const endpoint = subscription.endpoint;
  await subscription.unsubscribe();
  await api.delete("/notifications/push/subscribe/", { data: { endpoint } });

  return { success: true, message: "Push notifications disabled." };
}
