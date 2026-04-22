import Link from "next/link";

export default function OutcomesPage() {
  const stats = [
    { value: "87%", label: "of learners report career benefits" },
    { value: "76%", label: "feel more prepared for their careers" },
    { value: "88%", label: "rate content as high quality" },
    { value: "1M+", label: "certificates earned annually" },
  ];

  const outcomes = [
    {
      title: "Career Advancement",
      description:
        "Learners gain skills that lead to promotions, new roles, and higher salaries. Our credentials are recognized by employers worldwide.",
    },
    {
      title: "Job-Ready Skills",
      description:
        "Courses are designed with industry input to ensure learners develop the competencies employers are looking for.",
    },
    {
      title: "Increased Confidence",
      description:
        "Learners report feeling more confident in their abilities and better equipped to tackle workplace challenges.",
    },
    {
      title: "Lifelong Learning",
      description:
        "Our platform encourages continuous skill development, helping learners stay competitive in a rapidly changing job market.",
    },
  ];

  return (
    <div className="bg-white">
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-[#0056D2]/5 to-white">
        <div className="mx-auto max-w-6xl px-4 py-16">
          <nav className="mb-6 text-sm text-zinc-500">
            <Link href="/why-coursera" className="hover:text-[#0056D2]">
              Why Coursera
            </Link>
            <span className="mx-2">/</span>
            <span className="text-zinc-900">Outcomes</span>
          </nav>
          <h1 className="text-4xl font-semibold tracking-tight text-zinc-900">
            Proven Learner Outcomes
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-zinc-600">
            See how Coursera for Campus drives measurable results for students and institutions alike.
          </p>
        </div>
      </div>

      {/* Stats Section */}
      <div className="border-y border-zinc-200 bg-zinc-50">
        <div className="mx-auto max-w-6xl px-4 py-12">
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-4xl font-bold text-[#0056D2]">{stat.value}</div>
                <div className="mt-2 text-sm text-zinc-600">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Outcomes Grid */}
      <div className="mx-auto max-w-6xl px-4 py-16">
        <h2 className="text-2xl font-semibold text-zinc-900">What Learners Achieve</h2>
        <p className="mt-2 text-sm text-zinc-600">
          Research shows that Coursera learners experience significant improvements across key outcome areas.
        </p>
        <div className="mt-10 grid gap-6 sm:grid-cols-2">
          {outcomes.map((outcome) => (
            <div
              key={outcome.title}
              className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm"
            >
              <h3 className="text-lg font-semibold text-zinc-900">{outcome.title}</h3>
              <p className="mt-2 text-sm leading-6 text-zinc-600">{outcome.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA Section */}
      <div className="border-t border-zinc-200 bg-zinc-50">
        <div className="mx-auto max-w-6xl px-4 py-12">
          <div className="flex flex-col items-center text-center">
            <h2 className="text-2xl font-semibold text-zinc-900">
              Ready to drive outcomes at your institution?
            </h2>
            <p className="mt-2 max-w-xl text-sm text-zinc-600">
              Contact us to learn how Coursera for Campus can help your students succeed.
            </p>
            <div className="mt-6 flex gap-4">
              <Link
                href="/contact"
                className="inline-flex h-10 items-center justify-center rounded-md bg-[#0056D2] px-6 text-sm font-semibold text-white hover:bg-[#004bb8]"
              >
                Contact Us
              </Link>
              <Link
                href="/resources"
                className="inline-flex h-10 items-center justify-center rounded-md border border-zinc-300 bg-white px-6 text-sm font-semibold text-zinc-700 hover:bg-zinc-50"
              >
                View Resources
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

