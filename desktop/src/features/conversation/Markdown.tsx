import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ExternalLink } from "../help/ExternalLink";

type MdNode = { type: string; value?: string; children?: MdNode[] };

/**
 * Keep the agent's single line breaks as line breaks.
 *
 * The agent writes lines such as "Result: …" followed by "Each stated input
 * on its own:" and means two lines. Markdown folds a single newline into a
 * space, so the bubbles used `white-space: pre-wrap` to keep them — which also
 * printed the newlines *between* rendered blocks, adding stray blank lines to
 * every list and table. Turning soft breaks into real ones lets the blocks
 * render normally while each written line stays a line.
 */
function remarkSoftBreaks() {
  const walk = (node: MdNode) => {
    if (!node.children) return;
    const children: MdNode[] = [];
    for (const child of node.children) {
      if (child.type === "text" && child.value?.includes("\n")) {
        child.value.split("\n").forEach((part, index) => {
          if (index > 0) children.push({ type: "break" });
          if (part) children.push({ type: "text", value: part });
        });
      } else {
        walk(child);
        children.push(child);
      }
    }
    node.children = children;
  };
  return (tree: MdNode) => walk(tree);
}

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
        remarkPlugins={[remarkGfm, remarkSoftBreaks]}
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
