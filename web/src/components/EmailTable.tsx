import { create } from "zustand";

import { useEmails } from "@/hooks/useEmails";
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowsOutSimpleIcon, PlusIcon, TrashIcon } from "@phosphor-icons/react";
import { useState, useCallback } from "react";
import { ModalEscreverEmail } from "@/components/ui/modal";
import { Input } from "./ui/input";
import { ExpandModal } from "./ui/expandModal";
import type { Email } from "@/types/email";

export type FilterType = "todos" | "produtivo" | "improdutivo";

// Removido: interface Email (usar apenas o import de types/email)

export interface SendEmailData {
  to: string;
  subject: string;
  content: string;
  file: File | null;
}

interface FilterStore {
  filter: FilterType;
  setFilter: (filter: FilterType) => void;
}

const FILTERS = [
  { label: "Todos", value: "todos" as const },
  { label: "Produtivo", value: "produtivo" as const },
  { label: "Improdutivo", value: "improdutivo" as const },
];

const TABLE_COLUMNS = {
  SENDER_WIDTH: '18%',
  SUBJECT_WIDTH: '25%',
  CATEGORY_WIDTH: '15%',
  ACTIONS_WIDTH: '10%',
} as const;

const ANIMATION_CONFIG = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 10 },
  transition: { duration: 0.2 },
} as const;

const GLASS_STYLE = {
  backdropFilter: 'blur(12px)',
} as const;

const useFilterStore = create<FilterStore>((set) => ({
  filter: "todos",
  setFilter: (filter) => set({ filter }),
}));

const normalizeEmails = (emails: Email[]): Email[] => {
  return emails.map((email) => ({
    ...email,
    _id: email._id ?? (email as any).id ?? '', // garantir string
  }));
};

const filterEmails = (emails: Email[], searchTerm: string): Email[] => {
  const search = searchTerm.toLowerCase();
  return emails.filter(
    (email) =>
      email.email.toLowerCase().includes(search) ||
      email.content?.toLowerCase().includes(search) ||
      email.category?.toLowerCase().includes(search)
  );
};

interface TableHeaderSectionProps {
  search: string;
  onSearchChange: (value: string) => void;
  filter: FilterType;
  onFilterChange: (filter: FilterType) => void;
  emailCount: number;
}

const TableHeaderSection = ({ 
  search, 
  onSearchChange, 
  filter, 
  onFilterChange, 
  emailCount 
}: TableHeaderSectionProps) => (
  <TableCell colSpan={4} className="p-4 rounded-t-2xl">
    <div className="flex flex-wrap items-center gap-4">
      <div className="flex gap-2">
        <Input
          type="text"
          placeholder="Buscar email ou assunto..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="border-2 bg-white/80 rounded-md px-4 py-2 text-base focus:ring-2 ring-slate-900 min-w-[400px] mr-12"
        />
        {FILTERS.map((filterOption) => (
          <Button
            key={filterOption.value}
            variant={filter === filterOption.value ? "default" : "outline"}
            className={`rounded-md transition-all font-semibold px-4 py-1.5 text-base ${
              filter === filterOption.value 
                ? 'ring-2 scale-105 bg-neutral-900 text-white' 
                : 'bg-white text-neutral-700 border border-neutral-200'
            } shadow-none`}
            onClick={() => onFilterChange(filterOption.value)}
          >
            {filterOption.label}
          </Button>
        ))}
      </div>
      <div className="ml-auto text-base text-slate-500 font-medium">
        {emailCount} email{emailCount !== 1 && 's'} encontrado{emailCount !== 1 && 's'}
      </div>
    </div>
  </TableCell>
);

interface CategoryBadgeProps {
  category: string;
}

const CategoryBadge = ({ category }: CategoryBadgeProps) => {
  const isProductive = category === "Produtivo";
  const badgeClasses = isProductive
    ? "border-green-400 text-green-700 bg-green-50"
    : "border-red-300 text-red-600 bg-red-50";

  return (
    <span 
      className={`px-2 py-1 rounded-md text-xs font-semibold border ${badgeClasses}`}
      style={{ letterSpacing: 0.2 }}
    >
      {category}
    </span>
  );
};

interface EmailActionsProps {
  email: Email;
  onDelete: (email: Email) => void;
  onExpand: (email: Email) => void;
}

const EmailActions = ({ email, onDelete, onExpand }: EmailActionsProps) => (
  <div className="flex gap-2">
    <Button
      variant="outline"
      size="default"
      className="rounded-md border border-neutral-200 bg-white text-neutral-700 hover:bg-neutral-900 hover:text-white transition-colors shadow-none"
      onClick={() => onExpand(email)}
    >
      <ArrowsOutSimpleIcon size={20} />
      Expandir
    </Button>
    <Button
      variant="outline"
      size="icon"
      className="rounded-md border border-red-200 bg-red-50 text-red-600 hover:bg-red-600 hover:text-white hover:border-red-600 group shadow-none"
      onClick={() => onDelete(email)}
    >
      <TrashIcon size={20} className="transition-colors group-hover:text-white" />
    </Button>
  </div>
);

interface EmailRowProps {
  email: Email;
  onDelete: (email: Email) => void;
  onExpand: (email: Email) => void;
}

const EmailRow = ({ email, onDelete, onExpand }: EmailRowProps) => (
  <motion.tr
    key={email._id}
    {...ANIMATION_CONFIG}
    className="border-b last:border-0 hover:bg-muted/50 transition-colors rounded-md"
  >
    <TableCell className="font-medium whitespace-nowrap p-4">
      {email.email}
    </TableCell>
    <TableCell className="whitespace-nowrap">
      <span className="font-semibold text-neutral-900">{email.snippet}</span>
      <span className="text-neutral-500"> - {email.content}</span>
    </TableCell>
    <TableCell>
      <CategoryBadge category={email.category} />
    </TableCell>
    <TableCell>
      <EmailActions email={email} onDelete={onDelete} onExpand={onExpand} />
    </TableCell>
  </motion.tr>
);

interface EmailTableHeaderProps {
  onWriteEmail: () => void;
}

const EmailTableHeader = ({ onWriteEmail }: EmailTableHeaderProps) => (
  <div className="flex items-center justify-between mb-2">
    <h2 className="text-2xl font-semibold tracking-tight text-slate-900 drop-shadow-sm">
      Caixa de Entrada
    </h2>
    <Button 
      className="flex items-center gap-2 px-5 py-2 rounded-lg bg-neutral-900 text-white hover:bg-neutral-800 transition-colors shadow-none" 
      variant="default" 
      size="lg" 
      onClick={onWriteEmail}
    >
      <PlusIcon size={20} weight="bold" />
      Escrever
    </Button>
  </div>
);

const deleteEmailAPI = async (emailId: string): Promise<void> => {
  const response = await fetch(`/api/delete/${emailId}`, { method: "POST" });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || response.statusText);
  }
};

const sendEmailAPI = async (data: SendEmailData): Promise<any> => {
  const formData = new FormData();
  formData.append("email", data.to);
  formData.append("subject", data.subject);
  formData.append("content", data.content);
  
  if (data.file) {
    formData.append("file", data.file);
  }

  const response = await fetch("/api/analyzis", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || response.statusText);
  }

  return response.json();
};

export function EmailTable() {
  const [modalOpen, setModalOpen] = useState(false);
  const [expandModalOpen, setExpandModalOpen] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  const [search, setSearch] = useState("");

  const filter = useFilterStore((state) => state.filter);
  const setFilter = useFilterStore((state) => state.setFilter);

  const { emails, loading, error } = useEmails(filter);

  const normalizedEmails = normalizeEmails(emails);
  const filteredEmails = filterEmails(normalizedEmails, search);

  const handleDeleteEmail = useCallback(async (email: Email) => {
    const emailId = email._id;

    if (!emailId) {
      alert("ID do email não encontrado.");
      return;
    }

    if (!window.confirm("Tem certeza que deseja deletar este email?")) {
      return;
    }

    try {
      await deleteEmailAPI(emailId);
      console.log("Email deletado com sucesso:", emailId);
    } catch (error) {
      console.error("Erro ao deletar email:", error);
      alert(`Erro ao deletar email: ${error instanceof Error ? error.message : 'Erro desconhecido'}`);
    }
  }, []);

  const handleSendEmail = useCallback(async (data: SendEmailData) => {
    try {
      const result = await sendEmailAPI(data);
      alert(
        `Categoria: ${result.category}\nConfiança: ${result.confidence}\nSugestão de resposta: ${result.suggested_reply}`
      );
    } catch (error) {
      console.error("Erro ao enviar email:", error);
      alert(`Erro ao analisar email: ${error instanceof Error ? error.message : 'Erro de conexão'}`);
    }
  }, []);

  const handleOpenModal = useCallback(() => setModalOpen(true), []);
  const handleCloseModal = useCallback(() => setModalOpen(false), []);

  const handleExpandEmail = useCallback((email: Email) => {
    setSelectedEmail(email);
    setExpandModalOpen(true);
  }, []);

  const handleCloseExpandModal = useCallback(() => {
    setExpandModalOpen(false);
    setSelectedEmail(null);
  }, []);

  return (
    <>
      <ModalEscreverEmail 
        open={modalOpen} 
        onClose={handleCloseModal} 
        onSend={handleSendEmail} 
      />

  <ExpandModal open={expandModalOpen} onClose={handleCloseExpandModal} email={selectedEmail} />

      <div 
        className="p-8 w-full h-full flex flex-col gap-4 modern-glass shadow-xl border border-slate-200" 
        style={GLASS_STYLE}
      >
        <EmailTableHeader onWriteEmail={handleOpenModal} />

        {loading && (
          <div className="text-slate-400 animate-pulse mb-2">
            Carregando emails...
          </div>
        )}

        {error && (
          <div className="text-red-500 mb-2">{error}</div>
        )}

        <div className="overflow-x-auto rounded-2xl shadow bg-white/80 animate-fade-in p-2">
          <Table className="overflow-hidden max-w-full">
            <colgroup>
              <col style={{ width: TABLE_COLUMNS.SENDER_WIDTH }} />
              <col style={{ width: TABLE_COLUMNS.SUBJECT_WIDTH }} />
              <col style={{ width: TABLE_COLUMNS.CATEGORY_WIDTH }} />
              <col style={{ width: TABLE_COLUMNS.ACTIONS_WIDTH }} />
            </colgroup>

            <TableHeader>
              <TableHeaderSection
                search={search}
                onSearchChange={setSearch}
                filter={filter}
                onFilterChange={setFilter}
                emailCount={filteredEmails.length}
              />
              <TableRow>
                <TableHead className="text-lg p-3 font-semibold text-slate-800 modern-table-head">
                  Remetente
                </TableHead>
                <TableHead className="text-lg p-3 font-semibold text-slate-800 modern-table-head">
                  Assunto
                </TableHead>
                <TableHead className="text-lg p-3 font-semibold text-slate-800 modern-table-head">
                  Categoria
                </TableHead>
                <TableHead className="text-lg p-3 font-semibold text-slate-800 modern-table-head">
                  Ações
                </TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              <AnimatePresence>
                {filteredEmails.map((email) => (
                  <EmailRow 
                    key={email._id} 
                    email={email} 
                    onDelete={handleDeleteEmail}
                    onExpand={handleExpandEmail}
                  />
                ))}
              </AnimatePresence>
            </TableBody>
          </Table>

          {filteredEmails.length === 0 && !loading && (
            <div className="p-8 text-center text-gray-400">
              Nenhum email encontrado.
            </div>
          )}
        </div>
      </div>
    </>
  );
// Removido: } extra
}