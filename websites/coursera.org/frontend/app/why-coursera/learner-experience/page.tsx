import Link from "next/link";

export default function LearnerExperiencePage() {
  const features = [
    {
      title: "World-Class Content",
      description:
        "Access courses from top universities and leading companies including Google, IBM, Meta, and more.",
      icon: "🎓",
    },
    {
      title: "Flexible Learning",
      description:
        "Learn at your own pace with on-demand videos, quizzes, and hands-on projects that fit any schedule.",
      icon: "⏰",
    },
    {
      title: "Interactive Projects",
      description:
        "Apply what you learn with real-world projects and assignments that build practical skills.",
      icon: "💻",
    },
    {
      title: "Peer Community",
      description:
        "Connect with a global community of learners through discussion forums and collaborative activities.",
      icon: "🌐",
    },
    {
      title: "Mobile Learning",
      description:
        "Download courses to learn offline with our mobile apps for iOS and Android devices.",
      icon: "📱",
    },
    {
      title: "Recognized Credentials",
      description:
        "Earn certificates and degrees that are valued by employers and can be shared on LinkedIn.",
      icon: "🏆",
    },
  ];

  const testimonials = [
    {
      quote:
        "Coursera gave me the flexibility to learn new skills while working full-time. The quality of instruction is outstanding.",
      name: "Sarah M.",
      role: "Data Analyst",
    },
    {
      quote:
        "The hands-on projects helped me build a portfolio that landed me my first job in tech.",
      name: "James K.",
      role: "Software Developer",
    },
    {
      quote:
        "I completed my degree entirely online through Coursera while raising my family. It changed my career trajectory.",
      name: "Maria L.",
      role: "Product Manager",
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
            <span className="text-zinc-900">Learner Experience</span>
          </nav>
          <h1 className="text-4xl font-semibold tracking-tight text-zinc-900">
            Exceptional Learner Experience
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-zinc-600">
            Discover why millions of learners choose Coursera for their educational journey.
          </p>
        </div>
      </div>

      {/* Features Grid */}
      <div className="mx-auto max-w-6xl px-4 py-16">
        <h2 className="text-2xl font-semibold text-zinc-900">What Makes Coursera Different</h2>
        <p className="mt-2 max-w-2xl text-sm text-zinc-600">
          Our platform is designed to provide the best possible learning experience for students of all backgrounds.
        </p>
        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm transition hover:shadow-md"
            >
              <div className="text-3xl">{feature.icon}</div>
              <h3 className="mt-4 text-lg font-semibold text-zinc-900">{feature.title}</h3>
              <p className="mt-2 text-sm leading-6 text-zinc-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Testimonials */}
      <div className="border-y border-zinc-200 bg-zinc-50">
        <div className="mx-auto max-w-6xl px-4 py-16">
          <h2 className="text-center text-2xl font-semibold text-zinc-900">What Learners Say</h2>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            {testimonials.map((testimonial) => (
              <div
                key={testimonial.name}
                className="rounded-lg border border-zinc-200 bg-white p-6 shadow-sm"
              >
                <p className="text-sm italic leading-6 text-zinc-600">&ldquo;{testimonial.quote}&rdquo;</p>
                <div className="mt-4">
                  <div className="font-semibold text-zinc-900">{testimonial.name}</div>
                  <div className="text-xs text-zinc-500">{testimonial.role}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Platform Preview */}
      <div className="mx-auto max-w-6xl px-4 py-16">
        <div className="grid items-center gap-10 lg:grid-cols-2">
          <div>
            <h2 className="text-2xl font-semibold text-zinc-900">Learn Anytime, Anywhere</h2>
            <p className="mt-4 text-sm leading-6 text-zinc-600">
              Whether you&apos;re on your laptop at home or using our mobile app on the go, Coursera provides a
              seamless learning experience. Download courses for offline access, track your progress, and pick up
              right where you left off.
            </p>
            <ul className="mt-6 space-y-3 text-sm text-zinc-600">
              <li className="flex items-center gap-2">
                <span className="text-[#0056D2]">✓</span> Cross-device synchronization
              </li>
              <li className="flex items-center gap-2">
                <span className="text-[#0056D2]">✓</span> Offline learning mode
              </li>
              <li className="flex items-center gap-2">
                <span className="text-[#0056D2]">✓</span> Progress tracking dashboard
              </li>
              <li className="flex items-center gap-2">
                <span className="text-[#0056D2]">✓</span> Personalized recommendations
              </li>
            </ul>
            <div className="mt-8">
              <Link
                href="/courses"
                className="inline-flex h-10 items-center justify-center rounded-md bg-[#0056D2] px-6 text-sm font-semibold text-white hover:bg-[#004bb8]"
              >
                Explore Courses
              </Link>
            </div>
          </div>
          <div className="flex items-center justify-center">
            <div className="h-64 w-full max-w-md rounded-lg border border-zinc-200 bg-gradient-to-br from-zinc-100 to-zinc-50 p-8 shadow-sm">
              <div className="flex h-full flex-col items-center justify-center text-center">
                <div className="text-5xl">📚</div>
                <p className="mt-4 text-sm font-medium text-zinc-500">Interactive Learning Platform</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="border-t border-zinc-200 bg-zinc-50">
        <div className="mx-auto max-w-6xl px-4 py-12">
          <div className="flex flex-col items-center text-center">
            <h2 className="text-2xl font-semibold text-zinc-900">
              Ready to transform learning at your institution?
            </h2>
            <p className="mt-2 max-w-xl text-sm text-zinc-600">
              Join thousands of institutions using Coursera for Campus to deliver exceptional learning experiences.
            </p>
            <div className="mt-6 flex gap-4">
              <Link
                href="/contact"
                className="inline-flex h-10 items-center justify-center rounded-md bg-[#0056D2] px-6 text-sm font-semibold text-white hover:bg-[#004bb8]"
              >
                Contact Us
              </Link>
              <Link
                href="/compare-plans"
                className="inline-flex h-10 items-center justify-center rounded-md border border-zinc-300 bg-white px-6 text-sm font-semibold text-zinc-700 hover:bg-zinc-50"
              >
                Compare Plans
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

