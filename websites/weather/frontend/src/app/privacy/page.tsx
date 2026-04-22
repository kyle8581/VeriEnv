import { InfoPage } from "@/components/InfoPage";

export default function PrivacyPage() {
  return (
    <InfoPage title="Privacy Policy">
      <p>
        This project stores account data (email, name) and personalization data
        (saved locations, subscription state) in a local database.
      </p>
      <p>
        For development, demo accounts are seeded and the database can be reset
        via <code>./reset_servers.sh</code>.
      </p>
    </InfoPage>
  );
}

