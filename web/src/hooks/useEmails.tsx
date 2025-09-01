import type { Email, EmailFilter } from "@/types/email";
import { useEffect, useState } from "react";

export const useEmails = (filter: EmailFilter) => {
  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch("/api/list?page=1&per_page=100")
      .then(async (res) => {
        if (!res.ok) throw new Error("Erro ao buscar emails");
        const data = await res.json();
        let emails = data.emails || [];
        emails = emails.map((e: any, idx: number) => ({
          ...e,
          id: e.id || e._id || String(idx),
        }));
        setEmails(emails);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  let filtered = emails;
  if (filter === "produtivo") filtered = emails.filter((e) => e.category === "Produtivo");
  if (filter === "improdutivo") filtered = emails.filter((e) => e.category === "Improdutivo");

  return { emails: filtered, loading, error };
}
