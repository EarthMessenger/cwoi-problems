import { ActionError, defineAction } from "astro:actions";
import { z } from "astro:schema";
import { getSession } from "auth-astro/server";
import { pgPool } from "../db";

export const server = {
  postComment: defineAction({
    accept: "form",
    input: z.object({
      problemId: z.string(),
      comment: z.string().max(10000)
    }),
    handler: async (input, ctx) => {
      const session = await getSession(ctx.request);
      if (!session) {
        throw new ActionError({
          code: "UNAUTHORIZED",
        });
      }
      await pgPool.sql`INSERT INTO comments (author, content, problem_id) VALUES (${session.user.name}, ${input.comment}, ${input.problemId});`;
    }
  }),
  deleteComment: defineAction({
    accept: "json",
    input: z.object({
      id: z.number()
    }),
    handler: async (input, ctx) => {
      const session = await getSession(ctx.request);
      if (!session) {
        throw new ActionError({
          code: "UNAUTHORIZED",
        });
      }
      const commentAuthor = await pgPool.sql`SELECT author FROM comments WHERE id = ${input.id};`;
      if (commentAuthor.rowCount == 0) {
        throw new ActionError({
          code: "NOT_FOUND",
        });
      }
      if (commentAuthor.rows[0].author != session.user.name) {
        throw new ActionError({
          code: "UNAUTHORIZED",
        });
      }
      await pgPool.sql`DELETE FROM comments WHERE id = ${input.id};`;
    }
  }),
}