# Renault Charge History

Rough & ready Python jobby, probably horrendously written, which:

- Downloads the charge history of my car
- For each charge, calculate its cost using the Octopus Agile prices at the time
- Calculate an efficiency rating depending on how much the car charged, versus how much energy was drawn from my home

## Installation

🤔

## Usage

```sh
# Set renault username and password for your shell session
# (stick a space in front of them so they're saved against your bash history)
 export RENAULT_USERNAME=
 export RENAULT_PASSWORD=

# Run the jobby
python charge-history-to-csv.py

# See what you've done
xsv table "export/$(ls -t export | head -n 1)"
```

### Example output

```txt
chargeStartDate      chargeEndDate        chargeDuration  chargeStartBatteryLevel  chargeEndBatteryLevel  chargeEnergyRecovered  chargeEndStatus  homeEnergyConsumed   efficiency          cost
2024-03-02 15:26:43  2024-03-02 15:59:46  34              93                       99                     3.05                   ok               1.2466666666666668   244.65240641711227  16.326259909228444
2024-03-08 00:14:38  2024-03-08 15:11:41  898             48                       100                    26.55                  ok               32.92666666666667    80.63373152460012   406.61362918454944
2024-03-11 22:32:00  2024-03-12 10:34:17  723             39                       87                     22.8                   ok               26.510000000000005   86.0052810260279    364.98964574382177
```

### Public charging

- `homeEnergyConsumed` is a calculation of how much my granny charger would have consumed over `chargeDuration`
- `efficiency` is calculated as how much `homeEnergyConsumed` went into `chargeEnergyRecovered`, as there will be losses with using a granny charger
- If `efficiency` is greater than 100, the car consumed more electricity than my home charger could've supplied. That charge session was likely made using a public charger
- `cost` is calculated as `homeEnergyConsumed` versus Octopus Agile prices at the time. It cannot and will not be an accurate cost for public charging sessions