import { unified } from "unified";
import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import rehypeStringify from "rehype-stringify";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

export const markdownParser = unified()
  .use(remarkParse)
  .use(remarkMath)
  .use(remarkRehype)
  .use(rehypeSanitize, {
    ...defaultSchema,
    attributes: {
      ...defaultSchema.attributes,
      // The `language-*` regex is allowed by default.
      code: [["className", /^language-./, "math-inline", "math-display"]],
    },
  })
  .use(rehypeKatex)
  .use(rehypeStringify);
