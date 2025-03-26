import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from dateutil.relativedelta import relativedelta
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class PodioClient:
    def __init__(self):
        # Load credentials from .env file
        self.client_id = os.getenv("PODIO_CLIENT_ID")
        self.client_secret = os.getenv("PODIO_CLIENT_SECRET")
        self.username = os.getenv("PODIO_USERNAME")
        self.password = os.getenv("PODIO_PASSWORD")
        self.app_id = os.getenv("PODIO_APP_ID")
        self.access_token = None
        self.authenticate()
        print("Podio client initialized")

    def authenticate(self):
        """Authenticate with Podio API using password authentication"""
        url = "https://podio.com/oauth/token"
        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password,
        }

        response = requests.post(url, data=payload)
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            print("Authentication successful")
        else:
            print(f"Authentication failed: {response.text}")
            raise Exception("Authentication failed")

    def get_headers(self):
        """Get headers for API requests"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def get_all_members(self):
        """Get all members from the Podio app using direct API calls or cache"""
        cache_file = "members_cache.json"

        # Check if cache file exists
        if os.path.exists(cache_file):
            print("Loading members from cache...")
            with open(cache_file, "r") as file:
                all_members = json.load(file)
            print(f"Loaded {len(all_members)} members from cache")
            return all_members

        print("Fetching members from Podio API...")
        all_members = []
        offset = 0
        limit = 30

        while True:
            print(f"Fetching batch with offset {offset}...")
            url = f"https://api.podio.com/item/app/{self.app_id}/filter"
            payload = {"limit": limit, "offset": offset}

            response = requests.post(url, headers=self.get_headers(), json=payload)

            if response.status_code != 200:
                print(f"Error fetching members: {response.text}")
                break

            data = response.json()
            items = data.get("items", [])

            if not items:
                break

            all_members.extend(items)
            offset += limit

            if len(items) < limit:
                break

        # Save members to cache file
        with open(cache_file, "w") as file:
            json.dump(all_members, file)
        print(f"Retrieved and cached {len(all_members)} members")

        return all_members

    def get_item_revisions(self, item_id):
        """Get revision history for an item, using cache if available"""
        cache_file = f"revisions_cache_{item_id}.json"

        # Check if cache file exists
        if os.path.exists(cache_file):
            print(f"Loading revisions for item {item_id} from cache...")
            with open(cache_file, "r") as file:
                revisions = json.load(file)
            return revisions

        try:
            url = f"https://api.podio.com/item/{item_id}/revision"
            response = requests.get(url, headers=self.get_headers())

            if response.status_code != 200:
                print(f"Error fetching revisions for item {item_id}: {response.text}")
                return []

            revisions = response.json()

            # Save revisions to cache file
            with open(cache_file, "w") as file:
                json.dump(revisions, file)
            print(f"Retrieved and cached revisions for item {item_id}")

            return revisions
        except Exception as e:
            print(f"Error fetching revisions for item {item_id}: {str(e)}")
            return []


def extract_member_data(members):
    """Extract relevant data from member items"""
    member_data = []

    # Debug: Print field IDs from the first member to identify correct fields
    if members:
        print("\nField IDs in first member:")
        for field in members[0].get("fields", []):
            field_id = field.get("field_id")
            field_type = field.get("type")
            field_label = field.get("label", "No label")
            print(f"Field ID: {field_id}, Type: {field_type}, Label: {field_label}")

    # Look for join date field (Beginn Mitgliedschaft)
    join_date_field_id = None
    status_field_id = None
    name_field_id = None

    # Try to identify field IDs from the first few members
    for i in range(min(5, len(members))):
        for field in members[i].get("fields", []):
            label = field.get("label", "").lower()
            if "beginn" in label and "mitgliedschaft" in label:
                join_date_field_id = field.get("field_id")
                print(f"Found join date field ID: {join_date_field_id}")
            elif "status" in label:
                status_field_id = field.get("field_id")
                print(f"Found status field ID: {status_field_id}")
            elif "vorname" in label or "name" in label:
                name_field_id = field.get("field_id")
                print(f"Found name field ID: {name_field_id}")

    # If we couldn't find the fields by label, use the IDs
    if not join_date_field_id:
        join_date_field_id = 229611689  # "beginn-mitgliedschaft"
    if not status_field_id:
        status_field_id = 216758721  # "status"
    if not name_field_id:
        name_field_id = 206882163  # "name"

    print(
        f"Using field IDs - Join date: {join_date_field_id}, Status: {status_field_id}, Name: {name_field_id}"
    )

    for member in members:
        item_id = member.get("item_id")
        created_on = member.get("created_on")

        # Initialize member info
        member_info = {
            "item_id": item_id,
            "created_on": created_on,
            "join_date": None,
            "leave_date": None,
            "status": None,
            "name": None,
        }

        # Extract fields
        fields = member.get("fields", [])
        for field in fields:
            field_id = field.get("field_id")
            field_type = field.get("type")

            # Extract join date (Beginn Mitgliedschaft)
            if field_id == join_date_field_id:  # Beginn Mitgliedschaft
                if field_type == "date" and "start" in field.get("values", [{}])[0]:
                    member_info["join_date"] = field["values"][0]["start"]

            # Extract status
            elif field_id == status_field_id:  # Status field
                if field_type == "category" and field.get("values"):
                    member_info["status"] = field["values"][0]["value"]["text"]

            # Extract name
            elif field_id == name_field_id:  # Vorname field
                if field_type == "text" and field.get("values"):
                    member_info["name"] = field["values"][0]["value"]

        member_data.append(member_info)

    # Debug: Check how many members have join dates
    members_with_join_dates = [m for m in member_data if m["join_date"]]
    print(
        f"\nFound {len(members_with_join_dates)} members with join dates out of {len(member_data)} total"
    )

    if members_with_join_dates:
        print("Sample join dates:")
        for i in range(min(5, len(members_with_join_dates))):
            print(
                f"  Member {members_with_join_dates[i]['name']}: {members_with_join_dates[i]['join_date']}"
            )

    return member_data


def find_status_change_dates(podio_client, member_data):
    """Find dates when members' status changed to 'ausgetreten'"""
    # Use the status field ID from the screenshot
    status_field_id = 216758721
    ausgetreten_value = 4

    for i, member in enumerate(member_data):
        print(
            f"Processing revisions for member {i + 1}/{len(member_data)} (ID: {member['item_id']})"
        )
        revisions = podio_client.get_item_revisions(member["item_id"])

        for revision in revisions:
            # Check if this revision changed the status field
            if "data" in revision and "fields" in revision["data"]:
                for field in revision["data"]["fields"]:
                    if field.get("field_id") == status_field_id:  # Status field ID
                        values = field.get("values", [])
                        if values and values[0].get("value") == ausgetreten_value:
                            member["leave_date"] = revision.get("created_on")
                            break

            if member.get("leave_date"):
                break

    return member_data


def calculate_monthly_stats(member_data):
    """Calculate monthly statistics of active members"""
    # Filter out members without join dates
    valid_members = [m for m in member_data if m["join_date"]]

    if not valid_members:
        print("No members with valid join dates found!")
        return []

    # Find the earliest join date and latest leave date
    earliest_date = min(
        [
            datetime.fromisoformat(m["join_date"].replace("Z", "+00:00"))
            for m in valid_members
        ]
    )

    latest_date = datetime.now()
    for m in member_data:
        if m["leave_date"]:
            leave_date = datetime.fromisoformat(m["leave_date"].replace("Z", "+00:00"))
            if leave_date > latest_date:
                latest_date = leave_date

    # Create a range of months from earliest to latest
    current_date = earliest_date.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    end_date = latest_date.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    ) + relativedelta(months=1)

    months = []
    while current_date <= end_date:
        months.append(current_date)
        current_date += relativedelta(months=1)

    # Count active members for each month
    monthly_counts = []
    for month_start in months:
        month_end = month_start + relativedelta(months=1) - timedelta(seconds=1)

        active_count = 0
        for member in member_data:
            if not member["join_date"]:
                continue

            join_date = datetime.fromisoformat(
                member["join_date"].replace("Z", "+00:00")
            )

            # Check if member was active during this month
            if join_date <= month_end:
                if (
                    not member["leave_date"]
                    or datetime.fromisoformat(
                        member["leave_date"].replace("Z", "+00:00")
                    )
                    > month_end
                ):
                    active_count += 1

        monthly_counts.append(
            {"month": month_start.strftime("%Y-%m"), "active_members": active_count}
        )

    return monthly_counts


def plot_monthly_stats(monthly_stats):
    """Create a plot of monthly member statistics"""
    if not monthly_stats:
        print("No monthly statistics to plot!")
        return

    df = pd.DataFrame(monthly_stats)
    df["month"] = pd.to_datetime(df["month"])

    plt.figure(figsize=(12, 6))
    plt.plot(df["month"], df["active_members"], marker="o")
    plt.title("Space Team Active Members Over Time")
    plt.xlabel("Month")
    plt.ylabel("Number of Active Members")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the plot
    plt.savefig("space_team_members_stats.png")
    print("Plot saved as space_team_members_stats.png")

    # Also save the data as CSV
    df.to_csv("space_team_members_stats.csv", index=False)
    print("Data saved as space_team_members_stats.csv")

    # Print summary statistics
    print("\nMembership Summary:")
    print(f"Current active members: {df.iloc[-1]['active_members']}")
    print(
        f"Peak membership: {df['active_members'].max()} (in {df.iloc[df['active_members'].argmax()]['month']})"
    )
    print(f"Average membership: {df['active_members'].mean():.1f}")


def main():
    print("Initializing Podio client...")
    podio_client = PodioClient()

    print("Fetching members from Podio...")
    members = podio_client.get_all_members()
    print(f"Found {len(members)} members")

    print("Extracting member data...")
    member_data = extract_member_data(members)

    print("Finding status change dates...")
    member_data = find_status_change_dates(podio_client, member_data)

    print("Calculating monthly statistics...")
    monthly_stats = calculate_monthly_stats(member_data)

    print("Plotting results...")
    plot_monthly_stats(monthly_stats)

    print("Done!")


if __name__ == "__main__":
    main()
