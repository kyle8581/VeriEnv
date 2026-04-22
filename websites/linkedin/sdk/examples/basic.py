from linkedin_clone_sdk import LinkedInCloneClient, LocalSqliteDb


def main() -> None:
    client = LinkedInCloneClient(base_url="http://127.0.0.1:12079")
    client.login("jane.doe@example.com", "password123")

    me = client.me()
    print("me:", me["email"], me["first_name"], me["last_name"])

    feed = client.feed(limit=3)
    print("feed items:", len(feed["items"]))

    # Local DB inspection (works only when running locally with SQLite)
    db = LocalSqliteDb("../backend/var/app.db")
    print("users:", db.scalar("select count(*) from users"))


if __name__ == "__main__":
    main()

