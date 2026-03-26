import Link from "next/link";
import { Button, Card } from "@/components/ui";

export function WelcomeCard() {
  return (
    <Card className="text-center py-12">
      <h2 className="text-2xl font-bold text-slate-900">
        AudienceRoom へようこそ
      </h2>
      <p className="mt-3 text-slate-600">
        面接やプレゼンの練習を、AI聴衆と一緒に始めましょう。
        <br />
        本番に近い緊張感の中で練習することで、自信がつきます。
      </p>
      <div className="mt-8">
        <Link href="/sessions/new">
          <Button size="lg">最初の練習を始める</Button>
        </Link>
      </div>
      <p className="mt-4 text-sm text-slate-500">
        練習は何度でもやり直せます。気軽に始めてみましょう。
      </p>
    </Card>
  );
}
