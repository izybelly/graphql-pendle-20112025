import requests
from collections import defaultdict
from datetime import datetime, timezone
import csv


SUBGRAPH_URL = "https://gateway.thegraph.com/api/subgraphs/id/97MFRfM1qyic6JYQuoS9pDD4NhaH8HTioFj32Ynpsf1j"
API_KEY = "b214b0f962d755b24bae5d542e4c7361"
BATCH_SIZE = 1000
TOTAL_YIELD_POT = 877992.7680  


QUERY_TEMPLATE = """
{
  deposits(
    first: %d,
    skip: %d,
    orderBy: timestamp,
    orderDirection: asc,
    block: { number: 23836544 }
  ) {
    id
    account {
      id
    }
    amount
    timestamp
    transactionHash
  }
  
  withdrawals(
    first: %d,
    skip: %d,
    orderBy: timestamp,
    orderDirection: asc
  ) {
    id
    account {
      id
    }
    amount
    timestamp
    transactionHash
  }
}
"""


def fetch_batch(skip):
    query = QUERY_TEMPLATE % (BATCH_SIZE, skip, BATCH_SIZE, skip)
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post(SUBGRAPH_URL, json={'query': query}, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def fetch_all_events():
    deposits = []
    withdrawals = []
    skip = 0


    while True:
        data = fetch_batch(skip)
        batch_deposits = data['deposits']
        batch_withdrawals = data['withdrawals']


        deposits.extend(batch_deposits)
        withdrawals.extend(batch_withdrawals)


        if len(batch_deposits) < BATCH_SIZE and len(batch_withdrawals) < BATCH_SIZE:
            break
        skip += BATCH_SIZE


    return deposits, withdrawals


def save_to_csv(filename, data, fields):
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for item in data:
            row = {field: item.get(field) for field in fields}
            row['account_id'] = item['account']['id']
            writer.writerow(row)


def save_yields_to_csv(filename, user_yields, total_yield):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['account_id', 'yield', 'yield_decimal'])
        for user, y in user_yields.items():
            decimal = (y / total_yield) if total_yield else 0
            writer.writerow([user, f"{y:.6f}", f"{decimal:.8f}"])


def calculate_yield(deposits, withdrawals, total_yield):
    user_events = defaultdict(list)


    for d in deposits:
        user_events[d['account']['id']].append({
            'type': 'deposit',
            'amount': float(d['amount']),
            'timestamp': int(d['timestamp'])
        })
    for w in withdrawals:
        user_events[w['account']['id']].append({
            'type': 'withdrawal',
            'amount': float(w['amount']),
            'timestamp': int(w['timestamp'])
        })


    user_weighted_exposure = {}
    total_weighted_exposure = 0.0


    for user, events in user_events.items():
        events.sort(key=lambda e: e['timestamp'])
        position = 0.0
        last_timestamp = None
        weighted_exposure = 0.0


        for event in events:
            ts = event['timestamp']
            if last_timestamp is not None and position > 0:
                delta_days = (ts - last_timestamp) / 86400  # seconds to days
                weighted_exposure += position * delta_days
            if event['type'] == 'deposit':
                position += event['amount']
            else:
                position -= event['amount']
            last_timestamp = ts


        # Account for any open position held until now
        if position > 0 and last_timestamp is not None:
            current_ts = int(datetime.now(timezone.utc).timestamp())
            delta_days = (current_ts - last_timestamp) / 86400
            weighted_exposure += position * delta_days


        user_weighted_exposure[user] = weighted_exposure
        total_weighted_exposure += weighted_exposure


    # Calculate user yield proportional to weighted exposure
    user_yield = {}
    for user, exposure in user_weighted_exposure.items():
        if total_weighted_exposure > 0:
            user_yield[user] = (exposure / total_weighted_exposure) * total_yield
        else:
            user_yield[user] = 0.0


    return user_yield


def main():
    deposits, withdrawals = fetch_all_events()


    deposit_fields = ['id', 'account_id', 'amount', 'timestamp', 'transactionHash']
    withdrawal_fields = ['id', 'account_id', 'amount', 'timestamp', 'transactionHash']


    save_to_csv('deposits.csv', deposits, deposit_fields)
    save_to_csv('withdrawals.csv', withdrawals, withdrawal_fields)
    print("Data saved to deposits.csv and withdrawals.csv")


    user_yields = calculate_yield(deposits, withdrawals, TOTAL_YIELD_POT)

    save_yields_to_csv('user_yields.csv', user_yields, TOTAL_YIELD_POT)
    print("User yields saved to user_yields.csv")

if __name__ == "__main__":
    main()
