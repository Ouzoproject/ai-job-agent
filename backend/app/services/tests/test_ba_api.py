import asyncio
import base64

import httpx


BA_BASE_URL = (
    "https://rest.arbeitsagentur.de/"
    "jobboerse/jobsuche-service"
)

HEADERS = {
    "X-API-Key": "jobboerse-jobsuche",
}


async def main():

    reference = "19321-0065990133-S"

    encoded_reference = base64.b64encode(
        reference.encode("utf-8")
    ).decode("utf-8")

    url = (
        f"{BA_BASE_URL}/pc/v4/jobdetails/"
        f"{encoded_reference}"
    )

    async with httpx.AsyncClient(timeout=30.0) as client:

        response = await client.get(
            url,
            headers=HEADERS,
        )

        print("Status:", response.status_code)
        print()
        print(response.text)


if __name__ == "__main__":
    asyncio.run(main())