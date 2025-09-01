export type Email = {
  _id: string;
  email: string;
  snippet: string;
  content: string;
  category: "Produtivo" | "Improdutivo";
  confidence?: number;
  suggested_reply?: string;
};

export const FILTERS = ["todos", "produtivo", "improdutivo"] as const;
export type EmailFilter = typeof FILTERS[number];
