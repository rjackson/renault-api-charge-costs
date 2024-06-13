import csv
from datetime import datetime, timedelta
from renault_api.renault_client import RenaultClient
from typing import Any, List, Optional, Dict
import aiohttp
import asyncio
import os
import requests

username = os.environ.get("RENAULT_USERNAME")
password = os.environ.get("RENAULT_PASSWORD")
if not username or not password:
    raise ValueError("Username or password is missing")

HOME_CHARGER_WATTAGE = 2.2  # kW


class Charge:
    chargeStartDate: datetime
    chargeEndDate: datetime
    chargeDuration: int
    chargeStartBatteryLevel: int
    chargeEndBatteryLevel: int
    chargeEnergyRecovered: float
    chargeEndStatus: Optional[str]

    def __init__(
        self,
        chargeStartDate: str,
        chargeEndDate: str,
        chargeDuration: int,
        chargeStartBatteryLevel: int,
        chargeEndBatteryLevel: int,
        chargeEnergyRecovered: float,
        chargeEndStatus: Optional[str] = None,
    ):
        self.chargeStartDate = datetime.strptime(chargeStartDate, "%Y-%m-%dT%H:%M:%S%z")
        self.chargeEndDate = datetime.strptime(chargeEndDate, "%Y-%m-%dT%H:%M:%S%z")
        self.chargeDuration = chargeDuration
        self.chargeStartBatteryLevel = chargeStartBatteryLevel
        self.chargeEndBatteryLevel = chargeEndBatteryLevel
        self.chargeEnergyRecovered = chargeEnergyRecovered
        self.chargeEndStatus = chargeEndStatus


class EnrichedCharge(Charge):
    cost: float


def calculate_charge_cost(
    charge: Charge, agile_pricing: Dict[datetime, float]
) -> float:
    start = charge.chargeStartDate
    end = charge.chargeEndDate
    # total_energy = charge.chargeEnergyRecovered
    total_energy = charge.chargeDuration / 60 * HOME_CHARGER_WATTAGE  # kWh
    total_duration = (end - start).total_seconds() / 60  # total duration in minutes

    cost = 0.0
    current_time = start
    while current_time < end:
        next_time = min(current_time + timedelta(minutes=30), end)
        chunk_duration = (
            next_time - current_time
        ).total_seconds() / 60  # chunk duration in minutes
        chunk_energy = total_energy / total_duration * chunk_duration
        chunk_price = agile_pricing[
            current_time.replace(
                minute=current_time.minute // 30 * 30, second=0, tzinfo=None
            ).isoformat()
        ]  # assumes pricing data is available for each half-hour
        chunk_cost = chunk_energy * chunk_price
        cost += chunk_cost
        current_time = next_time

    return cost


def get_agile_pricing(start: datetime, end: datetime) -> Dict[datetime, float]:
    # Construct the URL
    PRODUCT_CODE = "AGILE-18-02-21"
    TARIFF_CODE = f"E-1R-{PRODUCT_CODE}-C"
    url = f"https://api.octopus.energy/v1/products/{PRODUCT_CODE}/electricity-tariffs/{TARIFF_CODE}/standard-unit-rates/"

    # charges recorded when the car was start/stopping at a bad charger could have the same time, which Octopus API doesn't like
    if (end - start).total_seconds() <= 60:
        end += timedelta(minutes=1)

    # Send the GET request
    response = requests.get(
        url, params={"period_from": start.isoformat(), "period_to": end.isoformat()}
    )

    # Check the response status
    response.raise_for_status()

    # Parse the pricing data
    pricing_data = response.json()["results"]
    pricing = {
        datetime.fromisoformat(item["valid_from"])
        .replace(tzinfo=None)
        .isoformat(timespec="seconds"): item["value_inc_vat"]
        for item in pricing_data
    }

    return pricing


def enrich_charge(charge: Charge) -> EnrichedCharge:
    homeEnergyConsumed = charge.chargeDuration / 60 * HOME_CHARGER_WATTAGE
    efficiency = (
        (charge.chargeEnergyRecovered / homeEnergyConsumed * 100)
        if charge.chargeEnergyRecovered > 0
        else 0
    )
    return {
        "chargeStartDate": charge.chargeStartDate.replace(tzinfo=None),
        "chargeEndDate": charge.chargeEndDate.replace(tzinfo=None),
        "chargeDuration": charge.chargeDuration,
        "chargeStartBatteryLevel": charge.chargeStartBatteryLevel,
        "chargeEndBatteryLevel": charge.chargeEndBatteryLevel,
        "chargeEnergyRecovered": charge.chargeEnergyRecovered,
        "chargeEndStatus": charge.chargeEndStatus,
        "homeEnergyConsumed": homeEnergyConsumed,
        "efficiency": efficiency,
        "cost": calculate_charge_cost(
            charge,
            get_agile_pricing(
                charge.chargeStartDate,
                charge.chargeEndDate,
            ),
        ),
    }


async def main():
    async with aiohttp.ClientSession() as websession:
        client = RenaultClient(websession=websession, locale="en_GB")
        await client.session.login(username, password)
        person = await client.get_person()

        account_id = next(
            account.accountId
            for account in person.accounts
            if account.accountType == "MYRENAULT"
        )

        account = await client.get_api_account(account_id)
        vehicles = await account.get_vehicles()

        vin = vehicles.vehicleLinks[0].vin
        vehicle = await account.get_api_vehicle(vin)

        start = datetime(2023, 1, 1)
        end = datetime(2025, 1, 31)

        charge_history = map(
            lambda x: Charge(**x),
            ((await vehicle.get_charges(start, end)).raw_data["charges"]),
        )
        charge_history = sorted(charge_history, key=lambda x: x.chargeStartDate)        

        enriched_charges = map(enrich_charge, charge_history)

        # Export enriched charges as CSV
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        csv_filename = f"export/enriched_charges_{timestamp}.csv"

        with open(csv_filename, "w", newline="") as csvfile:
            fieldnames = [
                "chargeStartDate",
                "chargeEndDate",
                "chargeDuration",
                "chargeStartBatteryLevel",
                "chargeEndBatteryLevel",
                "chargeEnergyRecovered",
                "chargeEndStatus",
                "homeEnergyConsumed",
                "efficiency",
                "cost",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(enriched_charges)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
