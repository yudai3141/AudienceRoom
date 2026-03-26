import { initializeApp, getApps, type FirebaseApp } from "firebase/app";
import { getAuth, connectAuthEmulator, type Auth } from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

let app: FirebaseApp | null = null;
let auth: Auth | null = null;
let emulatorConnected = false;

function getFirebaseApp(): FirebaseApp | null {
  if (app) return app;

  if (!firebaseConfig.apiKey) {
    return null;
  }

  app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
  return app;
}

function getFirebaseAuth(): Auth | null {
  if (auth) return auth;

  const firebaseApp = getFirebaseApp();
  if (!firebaseApp) return null;

  auth = getAuth(firebaseApp);

  if (
    typeof window !== "undefined" &&
    process.env.NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST &&
    !emulatorConnected
  ) {
    emulatorConnected = true;
    connectAuthEmulator(
      auth,
      `http://${process.env.NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST}`,
      { disableWarnings: true },
    );
  }

  return auth;
}

export { getFirebaseApp, getFirebaseAuth };
