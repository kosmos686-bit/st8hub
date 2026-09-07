export default function BlogPostLayout({ children }: { children: React.ReactNode }) {
  return (
    <article className="mx-auto max-w-2xl px-6 py-24 [&_h1]:text-3xl [&_h1]:font-semibold [&_h1]:tracking-tight [&_p]:mt-4 [&_p]:text-foreground/80">
      {children}
    </article>
  );
}
