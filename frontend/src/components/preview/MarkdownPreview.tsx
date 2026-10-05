import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/** Rendered Markdown. Raw HTML in the file is shown as text, not rendered, and
 * images are left out: they'd be fetched from wherever the file points, and
 * relative ones (the common case) can't be resolved against Box anyway. */
export default function MarkdownPreview({ text }: { text: string }) {
  return (
    <div className="prose prose-sm max-w-none p-6 prose-headings:font-heading prose-a:text-primary">
      <Markdown
        remarkPlugins={[remarkGfm]}
        disallowedElements={['img']}
        components={{
          a: ({ node: _node, ...props }) => <a {...props} target="_blank" rel="noreferrer" />,
        }}
      >
        {text}
      </Markdown>
    </div>
  )
}
