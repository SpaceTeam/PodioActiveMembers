# SpaceTeam Podio Members Stats

This project is designed to interact with the Podio API to fetch and analyze member data from a specific Podio app. It retrieves member information, tracks status changes, calculates monthly statistics, and generates visualizations of active members over time.

## Features

- **Authentication**: Uses OAuth2 for secure API access.
- **Data Caching**: Caches member and revision data to improve performance and reduce API calls.
- **Status Tracking**: Identifies and tracks members' status changes, specifically when they leave ("ausgetreten").
- **Monthly Statistics**: Calculates and plots monthly statistics of active members.
- **Visualization**: Generates plots and CSV files for data analysis.

## Requirements

- Python 3.7+
- Podio API credentials
- `.env` file with the following variables:
  - `PODIO_CLIENT_ID`
  - `PODIO_CLIENT_SECRET`
  - `PODIO_USERNAME`
  - `PODIO_PASSWORD`
  - `PODIO_APP_ID`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/SpaceTeam/PodioActiveMembers.git
   cd PodioActiveMembers
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with your Podio API credentials.

## Usage

1. Run the main script:
   ```bash
   python main.py
   ```

2. The script will authenticate with Podio, fetch member data, calculate statistics, and generate a plot and CSV file.

## Caching

- Member data is cached in `members_cache.json`.
- Revisions are cached in `revisions_cache_{item_id}.json` for each member.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or support, please contact it@spaceteam.at.
