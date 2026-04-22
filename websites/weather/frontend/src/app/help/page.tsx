import { InfoPage } from "@/components/InfoPage";

export default function HelpPage() {
  return (
    <InfoPage title="Help">
      <p>
        Use the search bar to find a city or zip code. You can save locations
        after signing in, and subscribe to unlock premium personalization.
      </p>
      <ul>
        <li>
          Reset data: run <code>./reset_servers.sh</code>
        </li>
        <li>
          Start services: run <code>./start_servers.sh</code>
        </li>
      </ul>
    </InfoPage>
  );
}

