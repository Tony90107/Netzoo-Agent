import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ExternalLink } from "../help/ExternalLink";

/** Render agent-authored Markdown without allowing raw HTML into the WebView. */
export function Markdown({
  children,
  className,
}: {
  children: string;
  className?: string;
}) {
  return (
    <div className={className ? `md ${className}` : "md"}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        skipHtml
        components={{
          a({ href, children: linkText }) {
            if (!href || !/^https?:\/\//i.test(href)) return <span>{linkText}</span>;
            return <ExternalLink href={href}>{linkText}</ExternalLink>;
          },
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
