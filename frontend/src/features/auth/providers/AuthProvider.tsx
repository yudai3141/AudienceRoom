"use client";

import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  onAuthStateChanged,
  signOut as firebaseSignOut,
  type User,
  type Auth,
} from "firebase/auth";
import { getFirebaseAuth } from "@/lib/firebase";
import { setTokenGetter } from "@/lib/api/client";

export type AuthState = {
  user: User | null;
  loading: boolean;
  signOut: () => Promise<void>;
  getIdToken: () => Promise<string | null>;
};

export const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const authRef = useRef<Auth | null>(null);
  const userRef = useRef<User | null>(null);
  const initializedRef = useRef(false);

  useEffect(() => {
    if (initializedRef.current) return;
    initializedRef.current = true;

    const auth = getFirebaseAuth();
    if (!auth) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- Initial mount only, Firebase unavailable
      setLoading(false);
      return;
    }

    authRef.current = auth;

    setTokenGetter(async () => {
      const currentUser = userRef.current;
      if (!currentUser) return null;
      return currentUser.getIdToken();
    });

    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      userRef.current = firebaseUser;
      setUser(firebaseUser);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const signOut = useCallback(async () => {
    const auth = authRef.current;
    if (!auth) return;
    await firebaseSignOut(auth);
  }, []);

  const getIdToken = useCallback(async () => {
    const currentUser = userRef.current;
    if (!currentUser) return null;
    return currentUser.getIdToken();
  }, []);

  const value = useMemo<AuthState>(
    () => ({ user, loading, signOut, getIdToken }),
    [user, loading, signOut, getIdToken],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
