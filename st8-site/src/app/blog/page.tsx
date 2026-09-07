import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Блог",
  description: "Заметки ST8-AI про AI-автоматизацию бизнеса.",
};

const posts = [
  {
    slug: "dobro-pozhalovat",
    title: "Добро пожаловать в блог ST8-AI",
    description: "Первая заметка — о том, зачем мы завели блог и что здесь будет.",
  },
];

export default function BlogPage() {
  return (
    <section className="px-6 py-24">
      <div className="mx-auto max-w-3xl">
        <h1 className="text-3xl font-semibold tracking-tight">Блог</h1>
        <ul className="mt-10 space-y-6">
          {posts.map((post) => (
            <li key={post.slug} className="border-b border-border pb-6">
              <Link
                href={`/blog/${post.slug}`}
                className="text-lg font-medium hover:text-gold"
              >
                {post.title}
              </Link>
              <p className="mt-2 text-sm text-foreground/60">{post.description}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
