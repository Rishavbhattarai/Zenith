import { cookies } from "next/headers";
import { AUTH_COOKIE } from "@/lib/backend";
import LoginForm from "./login-form";
import Dashboard from "./dashboard";

export default async function Home() {
  const cookieStore = await cookies();
  const authed = Boolean(cookieStore.get(AUTH_COOKIE)?.value);

  return authed ? <Dashboard /> : <LoginForm />;
}
