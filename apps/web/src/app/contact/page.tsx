export default function ContactPage() {
  return (
    <section className="space-y-6">
      <h1 className="font-display text-4xl text-text-natural">Contact</h1>
      <p className="text-text-beige">Send feedback, bug reports, or collaboration requests.</p>
      <form className="card max-w-2xl space-y-4">
        <input placeholder="Your name" className="w-full rounded-md border border-accent-orange/30 px-3 py-2" />
        <input placeholder="Your email" type="email" className="w-full rounded-md border border-accent-orange/30 px-3 py-2" />
        <textarea placeholder="Message" rows={5} className="w-full rounded-md border border-accent-orange/30 px-3 py-2" />
        <button className="btn-primary" type="submit">Send</button>
      </form>
    </section>
  );
}
