import { ReactNode } from 'react';
import { redirect } from 'next/navigation';

export function ProtectedRoute({ children }: { children: ReactNode }) {
  // Note: This is a server component wrapper. Client-side auth checks are handled via useAuth hook
  return <>{children}</>;
}
