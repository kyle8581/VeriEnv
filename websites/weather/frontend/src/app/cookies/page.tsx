import { InfoPage } from "@/components/InfoPage";

export default function CookiesPage() {
  return (
    <InfoPage title="Cookie Policy">
      <p>
        The frontend uses browser storage for local authentication tokens during
        development. A production deployment can be configured to use secure
        HTTP-only cookies.
      </p>
    </InfoPage>
  );
}

