import csv

TOTAL_YIELD_POT = 877992.7680  # Set to your actual value

def check_csv(filename, total_yield_pot):
    yield_sum = 0.0
    yield_decimal_sum = 0.0

    with open(filename, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Remove potential percent sign and convert to float
            y = float(row['yield'])
            yd = float(row['yield_decimal'])
            yield_sum += y
            yield_decimal_sum += yd

    print(f"Sum of yields:      {yield_sum:.6f}")
    print(f"Expected (pot):     {total_yield_pot:.6f}")
    print(f"Sum of decimals:    {yield_decimal_sum:.8f}")
    print(f"Expected (≈1.0):    {1.0:.8f}")

    if abs(yield_sum - total_yield_pot) < 1e-6 and abs(yield_decimal_sum - 1.0) < 1e-8:
        print("Validation: SUCCESS")
    else:
        print("Validation: FAILED")

if __name__ == "__main__":
    check_csv("user_yields.csv", TOTAL_YIELD_POT)
