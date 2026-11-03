import type { ReactNode } from "react";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
}

function renderInline(text: string): ReactNode[] {
  const pattern = /(\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)|\*\*([^*]+)\*\*|`([^`]+)`)/g;
  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) parts.push(text.slice(lastIndex, match.index));
    if (match[2] && match[3]) {
      parts.push(<a key={key++} href={match[3]} target="_blank" rel="noreferrer" className="font-medium text-blue-700 underline decoration-blue-300 underline-offset-2 hover:text-blue-900">{match[2]}</a>);
    } else if (match[4]) {
      parts.push(<strong key={key++} className="font-semibold text-slate-900">{match[4]}</strong>);
    } else if (match[5]) {
      parts.push(<code key={key++} className="rounded bg-slate-100 px-1.5 py-0.5 text-[0.9em] text-slate-700">{match[5]}</code>);
    }
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return parts;
}

function MarkdownContent({ content }: { content: string }) {
  const lines = content.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index].trim();
    if (!line) {
      index += 1;
      continue;
    }

    const heading = line.match(/^#{1,3}\s+(.+)$/);
    if (heading) {
      blocks.push(<h3 key={index} className="mb-2 mt-5 text-base font-bold text-slate-900 first:mt-0">{renderInline(heading[1])}</h3>);
      index += 1;
      continue;
    }

    const bullet = line.match(/^[-*]\s+(.+)$/);
    const numbered = line.match(/^\d+[.)]\s+(.+)$/);
    if (bullet || numbered) {
      const ordered = Boolean(numbered);
      const items: string[] = [];
      while (index < lines.length) {
        const current = lines[index].trim();
        const item = ordered ? current.match(/^\d+[.)]\s+(.+)$/) : current.match(/^[-*]\s+(.+)$/);
        if (!item) break;
        items.push(item[1]);
        index += 1;
      }
      const List = ordered ? "ol" : "ul";
      blocks.push(
        <List key={`list-${index}`} className={`mb-3 space-y-2 pl-5 text-sm leading-6 text-slate-700 ${ordered ? "list-decimal" : "list-disc"}`}>
          {items.map((item, itemIndex) => <li key={`${itemIndex}-${item}`}>{renderInline(item)}</li>)}
        </List>,
      );
      continue;
    }

    const paragraph: string[] = [line];
    index += 1;
    while (index < lines.length && lines[index].trim()) {
      const next = lines[index].trim();
      if (/^(#{1,3}\s+|[-*]\s+|\d+[.)]\s+)/.test(next)) break;
      paragraph.push(next);
      index += 1;
    }
    blocks.push(<p key={`paragraph-${index}`} className="mb-3 text-sm leading-6 text-slate-700 last:mb-0">{renderInline(paragraph.join(" "))}</p>);
  }
  return <div>{blocks}</div>;
}

export default function ChatMessage({ role, content }: ChatMessageProps) {
  const isUser = role === "user";
  return (
    <article className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[min(90%,48rem)] rounded-2xl px-5 py-4 shadow-sm ${isUser ? "rounded-br-md bg-blue-600 text-white" : "rounded-bl-md border border-slate-200 bg-white"}`}>
        {isUser ? <p className="whitespace-pre-wrap text-sm leading-6">{content}</p> : <MarkdownContent content={content} />}
      </div>
    </article>
  );
}
